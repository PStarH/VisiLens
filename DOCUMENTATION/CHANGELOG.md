# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-11-27

### Added
- **Column Type Conversion:** New `set_column_type()` function allows changing column data types (int, float, string, date, bool) with automatic data conversion.
- **Column Renaming:** New `rename_column()` function enables renaming columns in the dataset with proper validation and cache management.
- **Enhanced Context Menu:** Right-click context menu on column headers for quick access to column operations.
- **Improved Type System:** Better VisiData type system integration with proper cache clearing to ensure type changes persist across all operations.
- **Advanced Filtering:** Support for multiple filter conditions with AND logic in Basic filter mode.
- **Regex Filter:** Added regex matching operator for advanced pattern matching in string columns.

### Changed
- **Package Name:** Renamed from `vdweb` to `visilens` for better brand consistency.
- **CLI Command:** Primary command changed from `vdweb` to `visilens`.
- **Performance Improvements:** Optimized column data conversion with fast path for list-based rows.
- **Cache Management:** Enhanced stats cache clearing mechanism to ensure UI consistency after column modifications.

### Fixed
- Column type changes now correctly update underlying data and clear VisiData's cache.
- Column renames properly synchronize between backend and frontend.
- Filter operations maintain correct state after column modifications.

## [0.1.1] - 2025-11-25

### Added
- Initial release of VisiLens.
- Fast, local-first web GUI for VisiData.
- Support for CSV, Parquet, Excel, JSON, and more.
- Real-time sorting and filtering via WebSockets.
- React-based frontend with virtualized data grid.
- FastAPI backend acting as a bridge to VisiData core.
- CLI tool `vdweb` for easy launching.
