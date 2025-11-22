"""
VdWeb Server Module

FastAPI application serving both the WebSocket API and the static frontend.
"""

from __future__ import annotations

import json
import logging
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
    rows: list[dict[str, Any]]
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

        rows = dataset.get_rows(start=start, limit=limit)
        await self.send_response("rows", {
            "rows": rows,
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
        try:
            dataset = load_dataset(path)
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
            dataset.sort_by_column(column, ascending)
            state = dataset.get_state()
            await self.send_response("sorted", {
                "success": True,
                "state": state,
                "total": dataset.row_count,
            })

            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "rows": rows,
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True
            })

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
                dataset.filter_by_column(column, term)
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
                "rows": rows,
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True
            })

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
                "rows": rows,
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True
            })

        except Exception as e:
            await self.send_error(f"Reset failed: {e}", action="reset")

    async def handle_command(self, message: dict):
        """Route a command to the appropriate handler."""
        action = message.get("action")

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
                "reset": (
                    lambda msg: self.handle_reset()
                ),
                "ping": (
                    lambda msg: self.send_response("pong")
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
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

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
