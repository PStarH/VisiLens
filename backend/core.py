"""
VisiData Core Wrapper Module

This module wraps VisiData's internal API for programmatic use,
without launching the TUI. All data operations (loading, filtering,
sorting) happen here - the browser is just a renderer.
"""

from __future__ import annotations

import math
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
    _original_rows: list[Any] | None = field(default=None, init=False)
    _current_sort: tuple[str, bool] | None = field(default=None, init=False)  # (column_name, ascending)
    _current_filter: tuple[str, str] | None = field(default=None, init=False)  # (column_name, search_term)

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

    def sort_by_column(self, column_name: str, ascending: bool = True) -> None:
        """
        Sort rows by the specified column.

        Uses VisiData's column value getter to sort rows in place.
        Stores the original row order on first sort for potential reset.

        Args:
            column_name: Name of the column to sort by
            ascending: True for ascending order, False for descending

        Raises:
            ValueError: If column not found
        """
        with self._lock:
            # Store original rows if this is the first sort/filter operation
            if self._original_rows is None:
                self._original_rows = self.sheet.rows[:]

            # Find the column
            col = next((c for c in self.sheet.columns if c.name == column_name), None)
            if col is None:
                raise ValueError(f"Column '{column_name}' not found")

            # Sort rows using VisiData's column value getter
            # Handle potential errors in getTypedValue by falling back to string comparison
            def sort_key(row: Any) -> Any:
                try:
                    val = col.getTypedValue(row)
                    # Handle None values (sort them to the end)
                    if val is None:
                        return (1, None) if ascending else (0, None)
                    return (0, val)
                except Exception:
                    # Fallback to display value for comparison
                    return (0, col.getDisplayValue(row))

            self.sheet.rows = sorted(
                self.sheet.rows,
                key=sort_key,
                reverse=not ascending
            )

            # Track current sort state
            self._current_sort = (column_name, ascending)

    def filter_by_column(self, column_name: str, search_term: str) -> None:
        """
        Filter rows by searching for a term in the specified column.

        Case-insensitive substring match.
        Preserves current sort order.

        Args:
            column_name: Name of the column to filter by
            search_term: Search string to filter rows

        Raises:
            ValueError: If column not found
        """
        with self._lock:
            # Store original rows if this is the first operation
            if self._original_rows is None:
                self._original_rows = self.sheet.rows[:]

            # Find the column
            col = next((c for c in self.sheet.columns if c.name == column_name), None)
            if col is None:
                raise ValueError(f"Column '{column_name}' not found")

            # Start from original rows (to allow cumulative filtering)
            source_rows = self._original_rows

            # Filter rows (case-insensitive substring search)
            search_lower = search_term.lower()
            filtered = []
            for row in source_rows:
                try:
                    value = str(col.getValue(row))
                    if search_lower in value.lower():
                        filtered.append(row)
                except Exception:
                    # Skip rows that cause errors
                    continue

            self.sheet.rows = filtered
            self._current_filter = (column_name, search_term)

    def clear_filter(self) -> None:
        """
        Clear all filters and restore original rows.

        Preserves current sort order if sorting was applied.
        """
        with self._lock:
            if self._original_rows is not None:
                self.sheet.rows = self._original_rows[:]
                self._current_filter = None

                # Reapply sort if there was one
                if self._current_sort is not None:
                    column_name, ascending = self._current_sort
                    # Re-sort without storing original rows again
                    col = next((c for c in self.sheet.columns if c.name == column_name), None)
                    if col:
                        def sort_key(row: Any) -> Any:
                            try:
                                val = col.getTypedValue(row)
                                if val is None:
                                    return (1, None) if ascending else (0, None)
                                return (0, val)
                            except Exception:
                                return (0, col.getDisplayValue(row))

                        self.sheet.rows = sorted(
                            self.sheet.rows,
                            key=sort_key,
                            reverse=not ascending
                        )

    def reset(self) -> None:
        """
        Reset to original state (clear all sorts and filters).
        """
        with self._lock:
            if self._original_rows is not None:
                self.sheet.rows = self._original_rows[:]
                self._original_rows = None
            self._current_sort = None
            self._current_filter = None

    def get_state(self) -> dict[str, Any]:
        """
        Get current sort and filter state.

        Returns:
            Dictionary with 'sort' and 'filter' state
        """
        with self._lock:
            return {
                "sort": {
                    "column": self._current_sort[0] if self._current_sort else None,
                    "ascending": self._current_sort[1] if self._current_sort else None,
                } if self._current_sort else None,
                "filter": {
                    "column": self._current_filter[0] if self._current_filter else None,
                    "term": self._current_filter[1] if self._current_filter else None,
                } if self._current_filter else None,
            }


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
    if isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
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

    # VisiData's reload() is async by default. For synt
