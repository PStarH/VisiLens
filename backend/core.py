"""
VisiData Core Wrapper Module

This module wraps VisiData's internal API for programmatic use,
without launching the TUI. All data operations (loading, filtering,
sorting) happen here - the browser is just a renderer.
"""

from __future__ import annotations

import collections
import math
import threading
import random
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
    _stats_cache: dict[str, Any] = field(default_factory=dict, init=False)
    _sample_rows: list[Any] | None = field(default=None, init=False)

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

    def get_rows(self, start: int = 0, limit: int = 50) -> dict[str, Any]:
        """
        Return a slice of rows in columnar format.

        Returns:
            Dict with 'header' (list of col names) and 'rows' (list of lists of values).
        """
        with self._lock:
            rows = self.sheet.rows[start:start + limit]
            columns = self.sheet.columns

            header = [c.name for c in columns]
            result_rows = []
            
            # Optimization: Pre-calculate column indices for fast access
            col_indices = []
            for col in columns:
                if hasattr(col, 'expr') and isinstance(col.expr, int):
                    col_indices.append((col.expr, True))
                else:
                    col_indices.append((col, False))

            for row in rows:
                row_values = []
                is_list_row = isinstance(row, list)
                
                for col_or_idx, is_index in col_indices:
                    try:
                        if is_list_row and is_index:
                            val = row[col_or_idx]
                            row_values.append(_serialize_value(val))
                        else:
                            col = col_or_idx
                            value = col.getTypedValue(row)
                            row_values.append(_serialize_value(value))
                    except Exception:
                        col = col_or_idx if not is_index else next(c for c in columns if c.expr == col_or_idx)
                        row_values.append(col.getDisplayValue(row))
                result_rows.append(row_values)
                
            return {
                "header": header,
                "rows": result_rows
            }

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

            # Optimization: Fast path for list-based rows (CSV)
            # Direct index access avoids VisiData's getter overhead
            if hasattr(col, 'expr') and isinstance(col.expr, int) and self.sheet.rows and isinstance(self.sheet.rows[0], list):
                idx = col.expr
                
                # Define key function optimized for direct access
                # We use a tuple (type_group, value) to handle mixed types safely
                # Group 0: Numbers (int, float)
                # Group 1: Strings/Others
                # Group 2: None (always last if ascending)
                
                # Pre-calculate constants to avoid closure lookup overhead
                NONE_KEY = (2, None) if ascending else (0, None)
                
                def fast_key(row):
                    try:
                        val = row[idx]
                        if val is None:
                            return NONE_KEY
                        
                        if isinstance(val, (int, float)):
                            return (0, val)
                        
                        # Fallback for strings or other types
                        return (1, str(val))
                    except IndexError:
                        return NONE_KEY

                # In-place sort is slightly faster than sorted()
                self.sheet.rows.sort(key=fast_key, reverse=not ascending)

            else:
                # Slow path: use VisiData's column value getter
                # Handle potential errors in getTypedValue by falling back to string comparison
                def sort_key(row: Any) -> Any:
                    try:
                        val = col.getTypedValue(row)
                        # Handle None values (sort them to the end)
                        if val is None:
                            return (2, None) if ascending else (0, None)
                        
                        # Check if value matches column type (e.g. float)
                        # If column type is float but val is string (conversion failed),
                        # we treat it as a different group to avoid comparison errors.
                        if isinstance(val, (int, float)):
                            return (0, val)
                        else:
                            # Failed conversion or other type
                            return (1, str(val))
                    except Exception:
                        # Fallback to display value for comparison
                        return (1, col.getDisplayValue(row))

                self.sheet.rows.sort(
                    key=sort_key,
                    reverse=not ascending
                )

            # Track current sort state
            self._current_sort = (column_name, ascending)
            # Invalidate stats cache as order/sample might change (though distribution of full col doesn't, sample might)
            self._stats_cache.clear()
            self._sample_rows = None

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
            self._stats_cache.clear()
            self._sample_rows = None

    def apply_structured_filter(self, filter_payload: dict[str, Any] | None) -> None:
        """
        Apply a structured filter to the dataset.

        Args:
            filter_payload: Dict with 'column', 'operator', 'value'
        """
        with self._lock:
            # Reset if payload is None or "reset"
            if not filter_payload or filter_payload == "reset":
                self.clear_filter()
                return

            column_name = filter_payload.get("column")
            operator = filter_payload.get("operator")
            value = filter_payload.get("value")

            if not column_name or not operator:
                return

            # Store original rows if this is the first operation
            if self._original_rows is None:
                self._original_rows = self.sheet.rows[:]

            # Reset to original rows before applying new filter
            self.sheet.rows = self._original_rows[:]
            
            # Clear any existing selection
            if hasattr(self.sheet, 'selected'):
                self.sheet.selected = []

            col = next((c for c in self.sheet.columns if c.name == column_name), None)
            if col is None:
                raise ValueError(f"Column '{column_name}' not found")

            # Determine target type for casting
            col_type_name = _get_type_name(col.type)
            is_numeric = col_type_name in ('float', 'integer', 'currency')

            # Helper to cast value safely
            def safe_cast(val, to_type):
                try:
                    if to_type == 'float':
                        return float(val)
                    elif to_type == 'int':
                        return int(val)
                    elif to_type == 'str':
                        return str(val)
                    return val
                except (ValueError, TypeError):
                    return val

            # Cast the filter value
            target_val = safe_cast(value, 'float' if is_numeric else 'str')

            rows_to_select = []
            for row in self.sheet.rows:
                try:
                    cell_val = col.getTypedValue(row)
                    
                    # Handle None/Empty
                    if cell_val is None:
                        if operator == 'is_empty':
                            rows_to_select.append(row)
                        continue

                    # Comparison Logic
                    match = False
                    if operator == 'eq':
                        match = cell_val == target_val
                    elif operator == 'neq':
                        match = cell_val != target_val
                    elif operator == 'gt':
                        if is_numeric and isinstance(cell_val, (int, float)):
                            match = cell_val > target_val
                    elif operator == 'lt':
                        if is_numeric and isinstance(cell_val, (int, float)):
                            match = cell_val < target_val
                    elif operator == 'contains':
                        match = str(target_val).lower() in str(cell_val).lower()
                    elif operator == 'is_empty':
                        match = cell_val == ""

                    if match:
                        rows_to_select.append(row)

                except Exception:
                    continue

            # Use VisiData API to select rows
            if hasattr(self.sheet, 'select'):
                self.sheet.select(rows_to_select)
            
            # Filter to show only selected (equivalent to sheet.only_selected())
            self.sheet.rows = rows_to_select
            
            self._current_filter = (column_name, f"{operator} {value}")
            self._stats_cache.clear()
            self._sample_rows = None

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
            self._stats_cache.clear()
            self._sample_rows = None

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
            self._stats_cache.clear()
            self._sample_rows = None

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

    def get_column_frequency(self, col_name: str, limit: int = 20) -> list[dict[str, Any]]:
        """
        Calculate frequency distribution for a column.
        Returns top `limit` most frequent values.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Starting frequency analysis for column: {col_name}")

        with self._lock:
            col = next((c for c in self.sheet.columns if c.name == col_name), None)
            if col is None:
                raise ValueError(f"Column '{col_name}' not found")

            # Use Counter to count values
            counter = collections.Counter()
            
            # Optimization: Fast path for list-based rows
            if hasattr(col, 'expr') and isinstance(col.expr, int) and self.sheet.rows and isinstance(self.sheet.rows[0], list):
                logger.info("Using fast path for frequency analysis")
                idx = col.expr
                for row in self.sheet.rows:
                    try:
                        val = row[idx]
                        # Handle None/NaN
                        if val is None:
                            val = "(empty)"
                        elif isinstance(val, float) and math.isnan(val):
                            val = "(empty)"
                        
                        # Ensure value is hashable
                        if not isinstance(val, (str, int, float, bool, bytes)):
                            val = str(val)
                            
                        counter[val] += 1
                    except (IndexError, TypeError):
                        pass
            else:
                logger.info("Using slow path for frequency analysis")
                # Slow path
                for row in self.sheet.rows:
                    try:
                        val = col.getValue(row)
                        if val is None:
                            val = "(empty)"
                        elif isinstance(val, float) and math.isnan(val):
                            val = "(empty)"
                            
                        # Ensure value is hashable
                        if not isinstance(val, (str, int, float, bool, bytes)):
                            val = str(val)
                            
                        counter[val] += 1
                    except Exception:
                        pass

            total_count = sum(counter.values())
            logger.info(f"Analysis complete. Total count: {total_count}")
            
            if total_count == 0:
                return []

            # Get top N
            most_common = counter.most_common(limit)
            
            result = []
            for val, count in most_common:
                percent = (count / total_count) * 100
                result.append({
                    "name": str(val), # Ensure name is string for UI
                    "count": count,
                    "percent": round(percent, 2)
                })
                
            return result

    def _get_sample(self, size: int) -> list[Any]:
        """Get a random sample of rows, cached per sheet state."""
        if self._sample_rows is not None:
            return self._sample_rows
            
        total_rows = len(self.sheet.rows)
        if total_rows <= size:
            self._sample_rows = self.sheet.rows
        else:
            # Use random.sample for uniform random sampling without replacement
            self._sample_rows = random.sample(self.sheet.rows, size)
            
        return self._sample_rows

    def get_column_stats_sample(self, col_name: str, sample_size: int = 10000) -> dict[str, Any]:
        """
        Calculate quick statistics for a column using sampling.
        Optimized for performance (< 50ms).
        """
        with self._lock:
            # Check cache first
            if col_name in self._stats_cache:
                return self._stats_cache[col_name]

            col = next((c for c in self.sheet.columns if c.name == col_name), None)
            if col is None:
                raise ValueError(f"Column '{col_name}' not found")

            # Determine rows to scan using cached random sample
            total_rows = len(self.sheet.rows)
            rows_to_scan = self._get_sample(sample_size)
            is_sample = total_rows > len(rows_to_scan)
            scanned_count = len(rows_to_scan)
            
            null_count = 0
            unique_set = set()
            numeric_values = []
            
            # Optimization: Fast path for list-based rows
            if hasattr(col, 'expr') and isinstance(col.expr, int) and self.sheet.rows and isinstance(self.sheet.rows[0], list):
                idx = col.expr
                for row in rows_to_scan:
                    try:
                        val = row[idx]
                        if val is None or val == "":
                            null_count += 1
                        else:
                            # Use set for uniqueness (no truncation to preserve accuracy)
                            # We convert to string to ensure hashability for mixed types
                            unique_set.add(str(val))
                            
                            if isinstance(val, (int, float)) and not (isinstance(val, float) and math.isnan(val)):
                                numeric_values.append(val)
                    except IndexError:
                        null_count += 1
            else:
                # Slow path
                for row in rows_to_scan:
                    try:
                        val = col.getValue(row)
                        if val is None or val == "":
                            null_count += 1
                        else:
                            unique_set.add(str(val))
                            
                            if isinstance(val, (int, float)) and not (isinstance(val, float) and math.isnan(val)):
                                numeric_values.append(val)
                    except Exception:
                        null_count += 1

            # Calculate stats
            unique_count = len(unique_set)
            null_percent = round((null_count / scanned_count) * 100, 1) if scanned_count > 0 else 0
            
            stats = {
                "column": col_name,
                "scanned_rows": scanned_count,
                "total_rows": total_rows,
                "is_sample": is_sample,
                "null_count": null_count,
                "null_percent": null_percent,
                "unique_count": unique_count,
                "type": "string"
            }
            
            if numeric_values:
                stats["min"] = min(numeric_values)
                stats["max"] = max(numeric_values)
                stats["mean"] = round(sum(numeric_values) / len(numeric_values), 2)
                stats["type"] = "float" if any(isinstance(x, float) for x in numeric_values) else "integer"
            
            # Cache the result
            self._stats_cache[col_name] = stats
            return stats


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

    # Infer column types to ensure correct sorting (e.g. numeric vs string)
    _infer_column_types(sheet)

    return DatasetHandle(
        sheet=sheet,
        path=str(filepath.absolute())
    )


def _infer_column_types(sheet: Any, sample_size: int = 1000) -> None:
    """
    Infer column types by sampling data.
    
    Uses random sampling (reservoir sampling equivalent) to avoid bias 
    from sorted data or header-heavy files.
    """
    # Determine rows to sample
    total_rows = len(sheet.rows)
    if total_rows <= sample_size:
        rows_to_sample = sheet.rows
    else:
        rows_to_sample = random.sample(sheet.rows, sample_size)

    for col in sheet.columns:
        # Skip if type is already set to something specific (not anytype)
        type_name = getattr(col.type, '__name__', str(col.type))
        if type_name not in ('anytype', 'str', 'string', ''):
             continue

        # Get sample values (skip empty/None)
        values = []
        for row in rows_to_sample:
            try:
                val = col.getValue(row)
                if val is not None and val != '':
                    values.append(val)
            except Exception:
                pass
        
        if not values:
            continue
            
        # Helper to check type consistency
        def check_type(type_func, threshold=0.8):
            valid_count = 0
            for v in values:
                try:
                    type_func(v)
                    valid_count += 1
                except ValueError:
                    pass
            return valid_count / len(values) >= threshold

        # Try int first
        if check_type(int):
            col.type = int
            _convert_column_data(col, sheet.rows)
            continue

        # Try float
        if check_type(float):
            col.type = float
            _convert_column_data(col, sheet.rows)
            continue


def _convert_column_data(col: Any, rows: list[Any]) -> None:
    """
    Convert column data to the column's type.
    This ensures that the underlying data matches the metadata type.
    """
    # Optimization: Fast path for standard list-based rows (like CSV)
    # col.expr holds the index for ItemColumn in VisiData
    if hasattr(col, 'expr') and isinstance(col.expr, int) and rows and isinstance(rows[0], list):
        idx = col.expr
        type_func = col.type
        
        for row in rows:
            try:
                val = row[idx]
                # Only convert if it's a string (or not already the right type)
                # and not None/empty. 
                # We check for str specifically to avoid re-converting already converted values
                if isinstance(val, str) and val:
                    row[idx] = type_func(val)
            except (ValueError, TypeError, IndexError):
                pass
    else:
        # Fallback for other row types or complex columns
        for row in rows:
            try:
                # getTypedValue uses the column's type to convert the raw value
                val = col.getTypedValue(row)
                # setValue updates the underlying storage (e.g. the list representing the row)
                col.setValue(row, val)
            except Exception:
                # Leave original value on error
                pass


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
