"""
VisiLens FastAPI Backend

A minimal REST API exposing VisiData's data loading and querying
capabilities. The browser is just a renderer - all logic lives here.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core import (
    ColumnInfo,
    DatasetHandle,
    get_current_dataset,
    load_dataset,
    set_current_dataset,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-load test.csv if it exists (for demo purposes)."""
    test_csv = Path(__file__).parent / "test.csv"
    if test_csv.exists():
        try:
            dataset = load_dataset(str(test_csv))
            set_current_dataset(dataset)
            print(f"Auto-loaded test.csv: {dataset.row_count} rows, {dataset.column_count} columns")
        except Exception as e:
            print(f"Warning: Could not auto-load test.csv: {e}")
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


# --- Endpoints ---

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "VisiLens API",
        "version": "0.1.0"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
