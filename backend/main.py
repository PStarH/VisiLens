from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core import (
    DatasetHandle,
    get_current_dataset,
    load_dataset,
    set_current_dataset,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-load test.csv if it exists (for demo purposes)."""
    test_csv = Path(__file__).parent / "test.csv"
    if test_csv.exists():
        try:
            dataset = load_dataset(str(test_csv))
            set_current_dataset(dataset)
            logger.info(
                "Auto-loaded test.csv: %d rows, %d columns",
                dataset.row_count,
                dataset.column_count,
            )
        except Exception as e:
            logger.warning("Could not auto-load test.csv: %s", e)
    yield


app = FastAPI(
    title="VisiLens API",
    description="A fast, local-first API for exploring large datasets via VisiData",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
            # Apply sort
            dataset.sort_by_column(column, ascending)

            # Return updated state and rows
            state = dataset.get_state()
            await self.send_response("sorted", {
                "success": True,
                "state": state,
                "total": dataset.row_count,
            })

            # Also send the first chunk of sorted rows
            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "rows": rows,
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True  # Signal frontend to clear cache
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
            # Apply filter
            if term.strip():  # Only filter if term is non-empty
                dataset.filter_by_column(column, term)
            else:
                dataset.clear_filter()

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
                "rows": rows,
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True  # Signal frontend to clear cache
            })

        except ValueError as e:
            await self.send_error(str(e), action="filtered")
        except Exception as e:
            await self.send_error(f"Filter failed: {e}", action="filtered")

    async def handle_apply_filter(self, filter_payload: dict | None):
        """Handle apply_filter command."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="filtered")
            return

        try:
            # Apply filter
            dataset.apply_structured_filter(filter_payload)

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

            # Return updated state
            state = dataset.get_state()
            await self.send_response("reset", {
                "success": True,
                "state": state,
                "total": dataset.row_count,
            })

            # Send rows from original state
            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "rows": rows,
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True  # Signal frontend to clear cache
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
            data = await asyncio.to_thread(dataset.get_column_frequency, column)
            await self.send_response("analysis_result", {
                "column": column,
                "data": data
            })
        except ValueError as e:
            await self.send_error(str(e), action="analysis_result")
        except Exception as e:
            await self.send_error(f"Analysis failed: {e}", action="analysis_result")

    async def handle_get_stats(self, column: str):
        """Handle get_stats command (quick column summary)."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="stats_result")
            return

        try:
            # Run stats in a separate thread
            data = await asyncio.to_thread(dataset.get_column_stats_sample, column)
            await self.send_response("stats_result", {
                "column": column,
                "data": data
            })
        except ValueError as e:
            await self.send_error(str(e), action="stats_result")
        except Exception as e:
            await self.send_error(f"Stats failed: {e}", action="stats_result")

    async def handle_set_col_type(self, col_id: str, type_str: str):
        """Handle set_col_type command to change a column's type."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="columns")
            return

        try:
            # Change the column type
            dataset.set_column_type(col_id, type_str)

            # Send updated columns list
            columns = [
                {"name": c.name, "type": c.type, "width": c.width}
                for c in dataset.get_columns()
            ]
            await self.send_response("columns", {
                "columns": columns,
                "count": len(columns)
            })

            # Send refreshed rows to show new typed values
            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "rows": rows,
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True  # Signal frontend to clear cache
            })

        except ValueError as e:
            await self.send_error(str(e), action="columns")
        except Exception as e:
            await self.send_error(f"Type change failed: {e}", action="columns")

    async def handle_rename_col(self, col_id: str, new_name: str):
        """Handle rename_col command to rename a column."""
        dataset = _get_dataset_or_none()
        if dataset is None:
            await self.send_error("No dataset loaded", action="columns")
            return

        try:
            # Rename the column
            dataset.rename_column(col_id, new_name)

            # Send updated columns list
            columns = [
                {"name": c.name, "type": c.type, "width": c.width}
                for c in dataset.get_columns()
            ]
            await self.send_response("columns", {
                "columns": columns,
                "count": len(columns)
            })

            # Send refreshed rows with new column names
            rows = dataset.get_rows(start=0, limit=100)
            await self.send_response("rows", {
                "rows": rows,
                "start": 0,
                "limit": 100,
                "total": dataset.row_count,
                "reset": True  # Signal frontend to clear cache
            })

        except ValueError as e:
            await self.send_error(str(e), action="columns")
        except Exception as e:
            await self.send_error(f"Rename failed: {e}", action="columns")

    async def handle_command(self, message: dict):
        """Route a command to the appropriate handler."""
        action = message.get("action")

        # Use a simple dispatch table to keep branching manageable for
        # linters and maintainability. Handlers return coroutines.
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
                lambda msg: self.handle_apply_filter(msg.get("filter"))
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
                lambda msg: self.handle_get_stats(msg.get("column"))
                if msg.get("column")
                else self.send_error("Missing 'column' parameter", action="stats_result")
            ),
            "ping": (
                lambda msg: self.send_response("pong")
            ),
            "set_col_type": (
                lambda msg: self.handle_set_col_type(
                    msg.get("col_id"),
                    msg.get("type")
                )
                if msg.get("col_id") and msg.get("type")
                else self.send_error("Missing 'col_id' or 'type' parameter", action="columns")
            ),
            "rename_col": (
                lambda msg: self.handle_rename_col(
                    msg.get("col_id"),
                    msg.get("new_name")
                )
                if msg.get("col_id") and msg.get("new_name")
                else self.send_error("Missing 'col_id' or 'new_name' parameter", action="columns")
            ),
        }

        handler = handlers.get(action)
        if handler:
            await handler(message)
        else:
            await self.send_error(f"Unknown action: {action}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time data exploration.

    Commands:
    - {"action": "get_columns"} - Get column metadata
    - {"action": "get_rows", "start": 0, "limit": 50} - Get row slice
    - {"action": "get_info"} - Get dataset info
    - {"action": "load", "path": "/path/to/file"} - Load dataset
    - {"action": "ping"} - Connection health check
    """
    await websocket.accept()
    handler = WebSocketHandler(websocket)
    logger.info("WebSocket client connected")

    try:
        while True:
            # Receive JSON message
            try:
                message = await websocket.receive_json()
            except json.JSONDecodeError:
                await handler.send_error("Invalid JSON")
                continue

            # Handle the command
            await handler.handle_command(message)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# --- REST Endpoints (kept for compatibility) ---

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "VisiLens API",
        "version": "0.1.0",
        "websocket": "/ws"
    }


@app.post("/load", response_model=LoadResponse, tags=["Data"])
async def load_data(request: LoadRequest):
    """
    Load a dataset from a local file path.

    Supports 50+ formats via VisiData: CSV, TSV, JSON, Parquet,
    SQLite, Excel, and more.
    """
    try:
        dataset = load_dataset(request.path)
        set_current_dataset(dataset)

        columns = [
            ColumnResponse(name=c.name, type=c.type, width=c.width)
            for c in dataset.get_columns()
        ]

        return LoadResponse(
            success=True,
            message=f"Loaded {dataset.row_count} rows from {request.path}",
            info=DatasetInfoResponse(
                path=dataset.path,
                row_count=dataset.row_count,
                column_count=dataset.column_count,
                columns=columns
            )
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load: {e}")


@app.get("/info", response_model=DatasetInfoResponse, tags=["Data"])
async def get_info():
    """Get metadata about the currently loaded dataset."""
    dataset = _require_dataset()
    columns = [
        ColumnResponse(name=c.name, type=c.type, width=c.width)
        for c in dataset.get_columns()
    ]
    return DatasetInfoResponse(
        path=dataset.path,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        columns=columns
    )


@app.get("/columns", response_model=ColumnsResponse, tags=["Data"])
async def get_columns():
    """
    Get column headers and types from the loaded dataset.

    Returns column metadata including name, inferred type,
    and display width.
    """
    dataset = _require_dataset()
    columns = [
        ColumnResponse(name=c.name, type=c.type, width=c.width)
        for c in dataset.get_columns()
    ]
    return ColumnsResponse(columns=columns, count=len(columns))


@app.get("/rows", response_model=RowsResponse, tags=["Data"])
async def get_rows(
    start: int = Query(default=0, ge=0, description="Starting row index"),
    limit: int = Query(default=50, ge=1, le=10000, description="Number of rows to return")
):
    """
    Get a slice of rows from the loaded dataset.

    Supports pagination via start/limit parameters.
    All values are serialized to JSON-safe types.
    """
    dataset = _require_dataset()

    rows = dataset.get_rows(start=start, limit=limit)

    return RowsResponse(
        rows=rows,
        start=start,
        limit=limit,
        total=dataset.row_count
    )


# Serve static frontend files (for dev/production consistency)
static_dir = Path(__file__).parent.parent / "vdweb" / "static"
if static_dir.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


# For development: python -m uvicorn backend.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
