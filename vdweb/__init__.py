"""
VdWeb - A fast, local-first web GUI for exploring data with VisiData.

Excel for Developers. Open any data file (CSV, Parquet, JSON, etc.)
and explore it in your browser with real-time sorting, filtering,
and virtualized scrolling for 1M+ rows.
"""

__version__ = "0.1.0"
__author__ = "VisiLens Contributors"

from .core import load_dataset, DatasetHandle

__all__ = ["load_dataset", "DatasetHandle", "__version__"]
