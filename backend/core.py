"""
VisiData Core Wrapper Module

This module wraps VisiData's internal API for programmatic use,
without launching the TUI. All data operations (loading, filtering,
sorting) happen here - the browser is just a renderer.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import visidata


@dataclass
class ColumnInfo:
    """Metadata about a column in the dataset."""
    name: str
    type: str
    width: int | None = None


@dataclass
class DatasetHandle:
    """
    A handle to a loaded VisiData sheet.

    Provides thread-safe access to the underlying data without
    exposing VisiData internals to the API layer.
    """
    sheet: Any  # visidata.Sheet
    path: str
    _lock: threading.RLock = field(default_factory=threading.RLock)

    @property
    def row_count(self) -> int:
        """Total number of rows in the dataset."""
        with self._lock:
            return len(self.sheet.rows)

    @property
    def column_count(self) -> int:
        """Total number of columns in the dataset."""
        with self._lock:
            return len(self.sheet.columns)

    def get_columns(self) -> list[ColumnInfo]:
        """
        Return column metadata (name, type, width).

        VisiData column types are mapped to string representations
        for JSON serialization.
        """
        with self._lock:
            columns = []
            for col in self.sheet.columns:
                # Map VisiData type to string representation
                type_name = _get_type_name(col.type)
                columns.append(ColumnInfo(
                    name=col.name,
                    type=type_name,
                    width=getattr(col, 'width', None)
                ))
            return columns

    def get_rows(self, start: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        """
        Return a slice of rows as list of dicts.

        All values are converted to JSON-serializable types.
        Non-serializable values become strings.

        Args:
            start: Starting row index (0-based)
            limit: Maximum number of rows to return

        Returns:
            List of row dictionaries with column names as keys
        """
        with self._lock:
            rows = self.sheet.rows[start:start + limit]
            columns = self.sheet.columns

            result = []
            for row in rows:
                row_dict = {}
                for col in columns:
                    try:
                        # Get the typed value from VisiData
                        value = col.getTypedValue(row)
                        # Ensure JSON serializable
                        row_dict[col.name] = _serialize_value(value)
                    except Exception:
                        # Fallback to display value on any error
                        row_dict[col.name] = col.getDisplayValue(row)
                result.append(row_dict)
            return result


def _get_type_name(vd_type: Any) -> str:
    """Map VisiData type objects to string names."""
    if vd_type is None:
        return "string"  # Default to string for untyped columns

    type_map = {
        int: "integer",
        float: "float",
        str: "string",
        bool: "boolean",
    }

    # Handle VisiData's special types
    type_name = getattr(vd_type, '__name__', str(vd_type))

    if vd_type in type_map:
        return type_map[vd_type]
    elif type_name == 'anytype' or type_name == '':
        return "string"
    elif 'date' in type_name.lower():
        return "date"
    elif 'currency' in type_name.lower():
        return "currency"
    else:
        return type_name if type_name else "string"


def _serialize_value(value: Any) -> Any:
    """
    Convert a value to a JSON-serializable type.

    Handles common non-serializable types from VisiData.
    """
    if value is None:
        return None

    # Already serializable primitives
    if isinstance(value, (str, int, float, bool)):
        return value

    # Handle bytes
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return value.hex()

    # Handle datetime objects
    if hasattr(value, 'isoformat'):
        return value.isoformat()

    # Handle VisiData's TypedWrapper or similar
    if hasattr(value, 'val'):
        return _serialize_value(value.val)

    # Fallback: convert to string
    return str(value)


def load_dataset(path: str) -> DatasetHandle:
    """
    Load a dataset from the given path using VisiData's loaders.

    This function uses VisiData's internal API to load data without
    launching the TUI. VisiData automatically detects the file format
    based on extension.

    Supported formats include: CSV, TSV, JSON, SQLite, Parquet,
    Excel, and 50+ others.

    Args:
        path: Path to the data file (local filesystem)

    Returns:
        DatasetHandle for accessing the loaded data

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is not supported
    """
    filepath = Path(path)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Initialize VisiData in non-interactive mode
    vd = visidata.vd

    # Use VisiData's openSource to get the appropriate sheet type
    vd_path = visidata.Path(str(filepath))
    sheet = vd.openSource(vd_path)

    # VisiData's reload() is async by default. For synchronous loading,
    # we directly call iterload() and materialize the rows.
    if hasattr(sheet, 'iterload'):
        sheet.rows = list(sheet.iterload())

    # Handle CSV/TSV: first row is header, create columns from it
    # VisiData's CsvSheet yields raw lists where row[0] is the header
    if not sheet.columns and sheet.rows:
        first_row = sheet.rows[0]
        if isinstance(first_row, (list, tuple)):
            # First row is the header - use it for column names
            for i, col_name in enumerate(first_row):
                sheet.addColumn(visidata.ColumnItem(str(col_name), i))
            # Remove header row from data
            sheet.rows = sheet.rows[1:]

    return DatasetHandle(
        sheet=sheet,
        path=str(filepath.absolute())
    )


# Module-level dataset cache for the simple demo
# In production, this would be replaced with proper session management
_current_dataset: DatasetHandle | None = None


def get_current_dataset() -> DatasetHandle | None:
    """Get the currently loaded dataset (for demo purposes)."""
    return _current_dataset


def set_current_dataset(dataset: DatasetHandle) -> None:
    """Set the current dataset (for demo purposes)."""
    global _current_dataset
    _current_dataset = dataset
