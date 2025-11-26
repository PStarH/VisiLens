"""
VdWeb Server Module

FastAPI application serving both the WebSocket API and the static frontend.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .core import (
    DatasetHandle,
    get_current_dataset,
    load_dataset,
    set_current_dataset,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for initial dataset (set by CLI)
_initial_dataset_path: str | None = None
# Unique session ID for this server instance to detect restarts
SERVER_SESSION_ID = str(uuid.uuid4())

# Constants
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
OPERATION_TIMEOUT_SEC = 5.0


def set_initial_dataset_path(path: str) -> None:
    """Set the initial dataset path to load on startup."""
    global _initial_dataset_path
    _initial_dataset_path = path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the initial dataset if provided."""
    if _initial_dataset_path:
        try:
            dataset = load_dataset(_initial_dataset_path)
            set_current_dataset(dataset)
            logger.info(
                "Loaded dataset: %d rows, %d columns from %s",
                dataset.row_count,
                dataset.column_count,
                _initial_dataset_path,
            )
        except Exception as e:
            logger.error("Could not load dataset from %s: %s", _initial_dataset_path, e)
    yield


# --- Response Models ---

class ColumnResponse(BaseModel):
    """Column metadata response."""
    name: str
    type: str
    width: int | None = None


class ColumnsResponse(BaseModel):
    """Response for /columns endpoint."""
    columns: list[ColumnResponse]
    count: int


class RowsResponse(BaseModel):
    """Response for /rows endpoint."""
    header: list[str]
    rows: list[list[Any]]
    start: int
    limit: int
    total: int


class DatasetInfoResponse(BaseModel):
    """Response for /info endpoint."""
    path: str
    row_count: int
    column_count: int
    columns: list[ColumnResponse]


class LoadRequest(BaseModel):
    """Request body for loading a dataset."""
    path: str


class LoadResponse(BaseModel):
    """Response for /load endpoint."""
    success: bool
    message: str
    info: DatasetInfoResponse | None = None


class ErrorResponse(BaseModel):
    """Standard error response contract."""
    action: str
    success: bool = False
    error: str


# --- Helper Functions ---

def _require_dataset() -> DatasetHandle:
    """Get current dataset or raise 404."""
    dataset = get_current_dataset()
    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="No dataset loaded. POST to /load first."
        )
    return dataset


def _get_dataset_or_none() -> DatasetHandle | None:
    """Get current dataset or return None."""
    return get_current_dataset()


# --- WebSocket Handler ---

class WebSocketHandler:
    """
    Handles WebSocket commands for real-time data exploration.

    Protocol:
    - Client sends: {"action": "get_rows", "start": 0, "limit": 50}
    - Server sends: {"action": "rows", "success": true, "data": {...}}
    """

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.active_stats_tasks: dict[str, asyncio.Task] = {}

    async def send_response(self, action: str, data: Any = None, success: bool = True, error: str | None = None):
        """Send a JSON response to the client."""
        response = {
            "action": action,
            "success": success,
        }
        if data is not None:
            response["data"] = data
        if error is not None:
            response["error"] = error
        await self.websocket.send_json(response)

    async def send_error(self, message: str, action: str = "error"):
        """Send an error response."""
        await self.send_response(action, success=False, error=message)

    async def handle_get_columns(self):
        """Handle get_columns command."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="columns")
            return

        columns = [
            {"name": c.name, "type": c.type, "width": c.width}
            for c in dataset.get_columns()
        ]
        await self.send_response("columns", {
            "columns": columns,
            "count": len(columns)
        })

    async def handle_get_rows(self, start: int = 0, limit: int = 50):
        """Handle get_rows command."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="rows")
            return

        # Clamp values
        start = max(0, start)
        limit = min(max(1, limit), 10000)

        result = dataset.get_rows(start=start, limit=limit)
        await self.send_response("rows", {
            "header": result["header"],
            "rows": result["rows"],
            "start": start,
            "limit": limit,
            "total": dataset.row_count
        })

    async def handle_get_info(self):
        """Handle get_info command."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="info")
            return

        columns = [
            {"name": c.name, "type": c.type, "width": c.width}
            for c in dataset.get_columns()
        ]
        await self.send_response("info", {
            "path": dataset.path,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "columns": columns
        })

    async def handle_load(self, path: str):
        """Handle load command to load a new dataset."""
        # Check file size
        try:
            size = os.path.getsize(path)
            if size > MAX_FILE_SIZE_BYTES:
                await self.send_error(
                    f"File too large ({size / 1024 / 1024:.1f}MB). Limit is {MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f}MB.",
                    action="loaded"
                )
                return
        except OSError as e:
             await self.send_error(f"Could not access file: {e}", action="loaded")
             return

        try:
            # Wrap load in timeout
            dataset = await asyncio.wait_for(
                asyncio.to_thread(load_dataset, path),
                timeout=OPERATION_TIMEOUT_SEC
            )
            set_current_dataset(dataset)

            columns = [
                {"name": c.name, "type": c.type, "width": c.width}
                for c in dataset.get_columns()
            ]
            await self.send_response("loaded", {
                "path": dataset.path,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count,
                "columns": columns
            })
        except asyncio.TimeoutError:
            await self.send_error("Loading timed out.", action="loaded")
        except FileNotFoundError:
            await self.send_error(f"File not found: {path}", action="loaded")
        except Exception as e:
            await self.send_error(f"Failed to load: {e}", action="loaded")

    async def handle_sort(self, column: str, ascending: bool = True):
        """Handle sort command."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="sorted")
            return

        try:
            # Wrap sort in timeout
            await asyncio.wait_for(
                asyncio.to_thread(dataset.sort_by_column, column, ascending),
                timeout=OPERATION_TIMEOUT_SEC
            )
            
            state = dataset.get_state()
            await self.send_response("sorted", {
                "success": True,
                "state": state,
                "total": dataset.row_count,
            })

            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "header": rows["header"],
                "rows": rows["rows"],
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True
            })

        except asyncio.TimeoutError:
            await self.send_error("Sort operation timed out.", action="sorted")
        except ValueError as e:
            await self.send_error(str(e), action="sorted")
        except Exception as e:
            await self.send_error(f"Sort failed: {e}", action="sorted")

    async def handle_filter(self, column: str, term: str):
        """Handle filter command."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="filtered")
            return

        try:
            if term.strip():
                # Wrap filter in timeout
                await asyncio.wait_for(
                    asyncio.to_thread(dataset.filter_by_column, column, term),
                    timeout=OPERATION_TIMEOUT_SEC
                )
            else:
                dataset.clear_filter()

            state = dataset.get_state()
            await self.send_response("filtered", {
                "success": True,
                "state": state,
                "total": dataset.row_count,
            })

            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "header": rows["header"],
                "rows": rows["rows"],
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True
            })

        except asyncio.TimeoutError:
            await self.send_error("Filter operation timed out.", action="filtered")
        except ValueError as e:
            await self.send_error(str(e), action="filtered")
        except Exception as e:
            await self.send_error(f"Filter failed: {e}", action="filtered")

    async def handle_apply_filter(self, filter_payload: dict | None):
        """Handle apply_filter command."""
        logger.info(f"Handling apply_filter with payload: {filter_payload}")
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="filtered")
            return

        try:
            # Apply filter with timeout
            await asyncio.wait_for(
                asyncio.to_thread(dataset.apply_structured_filter, filter_payload),
                timeout=OPERATION_TIMEOUT_SEC
            )

            # Return updated state and rows
            state = dataset.get_state()
            await self.send_response("filtered", {
                "success": True,
                "state": state,
                "total": dataset.row_count,
            })

            # Send the filtered rows
            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "header": rows["header"],
                "rows": rows["rows"],
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True
            })

        except asyncio.TimeoutError:
            await self.send_error("Filter operation timed out.", action="filtered")
        except ValueError as e:
            await self.send_error(str(e), action="filtered")
        except Exception as e:
            await self.send_error(f"Filter failed: {e}", action="filtered")

    async def handle_reset(self):
        """Handle reset command (clear all sorts/filters)."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="reset")
            return

        try:
            dataset.reset()
            state = dataset.get_state()
            await self.send_response("reset", {
                "success": True,
                "state": state,
                "total": dataset.row_count,
            })

            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "header": rows["header"],
                "rows": rows["rows"],
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True
            })

        except Exception as e:
            await self.send_error(f"Reset failed: {e}", action="reset")

    async def handle_analyze(self, column: str):
        """Handle analyze command (frequency distribution)."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="analysis_result")
            return

        try:
            # Run analysis in a separate thread to avoid blocking the event loop
            data = await asyncio.wait_for(
                asyncio.to_thread(dataset.get_column_frequency, column),
                timeout=OPERATION_TIMEOUT_SEC
            )
            await self.send_response("analysis_result", {
                "column": column,
                "data": data
            })
        except asyncio.TimeoutError:
            await self.send_error(f"Analysis timed out for {column}", action="analysis_result")
        except ValueError as e:
            await self.send_error(str(e), action="analysis_result")
        except Exception as e:
            await self.send_error(f"Analysis failed: {e}", action="analysis_result")

    async def handle_get_stats(self, column: str, req_id: int | None = None, force: bool = False):
        """Handle get_stats command (quick column summary)."""
        # Request Coalescing: If a task for this column is already running, skip
        if column in self.active_stats_tasks and not force:
            logger.info(f"Coalescing stats request for column: {column}")
            return

        async def fetch_and_send():
            logger.info(f"Task started: stats for {column}")
            try:
                dataset = _get_dataset_or_none()
                if dataset is None:
                    await self.send_error("No dataset loaded", action="stats_result")
                    return

                # Run stats in a separate thread with timeout
                try:
                    data = await asyncio.wait_for(
                        asyncio.to_thread(dataset.get_column_stats_sample, column),
                        timeout=OPERATION_TIMEOUT_SEC
                    )
                    logger.info(f"Task finished: stats for {column}")
                    
                    # Minimal response payload
                    response_data = {
                        "column": column,
                        "data": data
                    }
                    if req_id is not None:
                        response_data["req_id"] = req_id

                    await self.send_response("stats_result", response_data)

                except asyncio.TimeoutError:
                    logger.warning(f"Task timeout: stats for {column}")
                    # Return placeholder stats on timeout
                    response_data = {
                        "column": column,
                        "data": None,
                        "timed_out": True
                    }
                    if req_id is not None:
                        response_data["req_id"] = req_id
                    
                    await self.send_response("stats_result", response_data)
                    
            except ValueError as e:
                logger.error(f"Task error: stats for {column} - {e}")
                await self.send_error(str(e), action="stats_result")
            except Exception as e:
                logger.error(f"Task failed: stats for {column} - {e}")
                await self.send_error(f"Stats failed: {e}", action="stats_result")
            finally:
                # Remove self from active tasks
                self.active_stats_tasks.pop(column, None)

        # Create and track the task
        task = asyncio.create_task(fetch_and_send())
        self.active_stats_tasks[column] = task
        # Note: We do NOT await the task here, allowing the loop to process other messages

    async def handle_rename_col(self, col_id: str, new_name: str):
        """Handle rename_col command."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="rename_col")
            return

        try:
            await asyncio.to_thread(dataset.rename_column, col_id, new_name)
            
            # Return updated columns
            columns = [
                {"name": c.name, "type": c.type, "width": c.width}
                for c in dataset.get_columns()
            ]
            await self.send_response("columns", {
                "columns": columns,
                "count": len(columns)
            })
            
            # Also refresh rows header
            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "header": rows["header"],
                "rows": rows["rows"],
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True
            })

        except ValueError as e:
            await self.send_error(str(e), action="rename_col")
        except Exception as e:
            await self.send_error(f"Rename failed: {e}", action="rename_col")

    async def handle_set_col_type(self, col_id: str, new_type: str):
        """Handle set_col_type command."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="set_col_type")
            return

        try:
            # This might take a moment if it reloads the sheet
            await asyncio.wait_for(
                asyncio.to_thread(dataset.set_column_type, col_id, new_type),
                timeout=OPERATION_TIMEOUT_SEC * 2 # Give it more time for reload
            )
            
            # Return updated columns
            columns = [
                {"name": c.name, "type": c.type, "width": c.width}
                for c in dataset.get_columns()
            ]
            await self.send_response("columns", {
                "columns": columns,
                "count": len(columns)
            })
            
            # Refresh rows with new types
            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "header": rows["header"],
                "rows": rows["rows"],
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True
            })

        except asyncio.TimeoutError:
            await self.send_error("Type change timed out.", action="set_col_type")
        except ValueError as e:
            await self.send_error(str(e), action="set_col_type")
        except Exception as e:
            await self.send_error(f"Type change failed: {e}", action="set_col_type")

    async def handle_command(self, message: dict):
        """Route a command to the appropriate handler."""
        action = message.get("action")
        logger.info(f"Received command action: {action}")

        handlers = {
                "get_columns": (
                    lambda msg: self.handle_get_columns()
                ),
                "get_rows": (
                    lambda msg: self.handle_get_rows(
                        msg.get("start", 0),
                        msg.get("limit", 50),
                    )
                ),
                "get_info": (
                    lambda msg: self.handle_get_info()
                ),
                "load": (
                    lambda msg: self.handle_load(msg.get("path"))
                    if msg.get("path")
                    else self.send_error("Missing 'path' parameter", action="loaded")
                ),
                "sort": (
                    lambda msg: self.handle_sort(
                        msg.get("column"),
                        msg.get("ascending", True),
                    )
                    if msg.get("column")
                    else self.send_error("Missing 'column' parameter", action="sorted")
                ),
                "filter": (
                    lambda msg: self.handle_filter(
                        msg.get("column"),
                        msg.get("term", ""),
                    )
                    if msg.get("column")
                    else self.send_error("Missing 'column' parameter", action="filtered")
                ),
                "apply_filter": (
                    lambda msg: self.handle_apply_filter(msg.get("filter_payload"))
                ),
                "reset": (
                    lambda msg: self.handle_reset()
                ),
                "analyze": (
                    lambda msg: self.handle_analyze(msg.get("column"))
                    if msg.get("column")
                    else self.send_error("Missing 'column' parameter", action="analysis_result")
                ),
                "get_stats": (
                    lambda msg: self.handle_get_stats(
                        msg.get("column"),
                        msg.get("req_id"),
                        msg.get("force", False)
                    )
                    if msg.get("column")
                    else self.send_error("Missing 'column' parameter", action="stats_result")
                ),
                "ping": (
                    lambda msg: self.send_response("pong")
                ),
                "rename_col": (
                    lambda msg: self.handle_rename_col(
                        msg.get("col_id"),
                        msg.get("new_name")
                    )
                    if msg.get("col_id") and msg.get("new_name")
                    else self.send_error("Missing parameters", action="rename_col")
                ),
                "set_col_type": (
                    lambda msg: self.handle_set_col_type(
                        msg.get("col_id"),
                        msg.get("type")
                    )
                    if msg.get("col_id") and msg.get("type")
                    else self.send_error("Missing parameters", action="set_col_type")
                ),
        }

        handler = handlers.get(action)
        if handler:
            await handler(message)
        else:
            await self.send_error(f"Unknown action: {action}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="VdWeb API",
        description="A fast, local-first API for exploring large datasets via VisiData",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time data exploration."""
        await websocket.accept()
        handler = WebSocketHandler(websocket)
        logger.info("WebSocket client connected")

        # Send server restart/hello event
        await handler.send_response("server_restart", {
            "session_id": SERVER_SESSION_ID,
            "message": "Server ready"
        })

        try:
            while True:
                try:
                    message = await websocket.receive_json()
                except json.JSONDecodeError:
                    await handler.send_error("Invalid JSON")
                    continue

                await handler.handle_command(message)

        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
            # Cancel active tasks
            for task in handler.active_stats_tasks.values():
                task.cancel()
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            # Cancel active tasks
            for task in handler.active_stats_tasks.values():
                task.cancel()

    # Serve static frontend files
    # The static directory should contain the built React app
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    else:
        @app.get("/")
        async def root():
            return {
                "error": "Frontend not built",
                "message": "Run 'npm run build' in the frontend directory and copy dist/* to vdweb/static/"
            }

    return app


# For development: python -m uvicorn vdweb.server:app --reload
app = create_app()
