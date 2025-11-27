<div align="center">
  <img src="https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/banner.svg" alt="VisiLens Logo" width="100%" />
  
  # VisiLens

  **Excel for Developers**

  > **Open 1M+ rows in seconds. Local, fast, simple.**
  
  A high-performance, local-first web GUI for exploring datasets. Instantly view and filter CSV, Parquet, Excel, and JSON files using the power of [VisiData](https://www.visidata.org/).

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![VisiData Engine](https://img.shields.io/badge/Engine-VisiData-orange.svg)](https://www.visidata.org/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://reactjs.org/)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
  [![PyPI](https://img.shields.io/pypi/v/vdweb.svg)](https://pypi.org/project/vdweb/)

  [English](README.md) • [简体中文](DOCUMENTATION/README_zh.md) • [Español](DOCUMENTATION/README_es.md) • [日本語](DOCUMENTATION/README_ja.md) • [Русский](DOCUMENTATION/README_ru.md)

  [Features](#features) • [Installation](#installation) • [Usage](#usage) • [Architecture](#architecture) • [Contributing](#contributing)
</div>

---

> **📦 Package Name Notice**  
> The PyPI package name is **`vdweb`** (install with `pip install vdweb`), but you can use either `visilens` or `vdweb` as the command-line tool after installation. We recommend using `visilens` for consistency with the project name.

---

## 🚀 Why VisiLens?

Data exploration shouldn't require writing boilerplate Pandas code or waiting for heavy spreadsheet software like Excel to load. **VisiLens** is a modern **CSV viewer** and **Parquet explorer** that combines the raw speed of **VisiData** with a lightweight web interface.

- **⚡️ Load 1M rows in under 2 seconds:** Powered by VisiData's highly optimized engine.
- **🔒 All local:** Your data never leaves your machine. No cloud uploads.
- **🛠 Zero config:** CLI-first workflow. Pipe data in, explore, and get back to coding.
- **🔌 Universal Support:** Open CSV, TSV, JSON, Parquet, Excel, SQLite, and [50+ other formats](https://www.visidata.org/formats/).

## ✨ Features

- **Instant Data Visualization:** Just run `visilens data.csv` to visualize large datasets instantly.
- **Backend-powered Sorting & Filtering:** Perform complex queries on millions of rows using the VisiData engine.
- **Column Manipulation:** Change column types, rename columns, and edit data with an intuitive context menu.
- **Advanced Filtering:** Apply multiple filter conditions with support for regex pattern matching.
- **Lightweight Data Grid:** A virtualized React-based table view for smooth scrolling.
- **Zero Config:** No database setup required. Works as a standalone CSV/Parquet viewer.

### 📂 Supported Formats
VisiLens leverages VisiData's loaders to support a wide range of formats out of the box:
- **Tabular:** `.csv`, `.tsv`, `.xlsx` (Excel), `.parquet`
- **Structured:** `.json`, `.jsonl`, `.yaml`
- **Database:** `.sqlite`, `.db`
- **Code:** `.pcap` (Wireshark), `.xml`, `.html` tables

## 📊 Benchmarks

We take performance seriously. Here is how VisiLens compares when opening a **1,000,000 row** CSV dataset on a standard MacBook Air (M2).

| Tool | Load Time (1M Rows) | Memory Footprint | Interactive Sorting |
| :--- | :--- | :--- | :--- |
| **VisiLens** | **~1.7s** | **Minimal (< 50MB Total)** | **Instant** (Backend: < 0.4s) |
| Excel | > 30s (Often Fails) | High (Blocking RAM) | Slow/Unresponsive |
| **Pandas-based GUI** | > 15s (Cold Start) | High (Entire DF in RAM) | Sluggish (Non-Virtualized) |
| Jupyter (print df) | Fast | Medium | Static Text |

*Test Data: 1M rows, 3 columns (Mixed types). Numbers are from my MacBook Air M2 during real development use.*

## 📦 Installation

VisiLens is available as a Python package.

```bash
pip install visilens
```

*Note: VisiLens requires Python 3.10 or higher.*

## 💻 Usage

### Command Line Interface

The primary way to use VisiLens is via the command line.

```bash
# Open a CSV file
visilens data.csv

# Open a Parquet file
visilens large-dataset.parquet

# Open an Excel file
visilens spreadsheet.xlsx

# Launch without opening the browser automatically
visilens data.json --no-browser

# Specify a custom port
visilens data.csv --port 9000
```

### Web Interface

Once launched, VisiLens opens in your default browser (usually `http://localhost:8000`).

1.  **View Data:** Scroll through your dataset efficiently.
2.  **Sort:** Click column headers to sort ascending/descending.
3.  **Filter:** Use the power filter bar to apply complex queries with multiple conditions.
4.  **Column Operations:** Right-click column headers to change types, rename columns, or access advanced options.
5.  **Load New Data:** (Coming Soon) Drag and drop files directly into the window.

## 🏗 Architecture

VisiLens is built on a robust modern stack designed for performance:

*   **Backend:** FastAPI server bridges VisiData and the browser.
*   **Communication:** WebSockets stream slices on demand.
*   **Frontend:** React grid renders only what you see.

![Architecture Diagram](https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/diagram.png)

## 🗺 Roadmap

We are actively working on making VisiLens the ultimate local data companion.

For a detailed breakdown of our feature strategy and technical implementation plan, please see [ROADMAP.md](DOCUMENTATION/ROADMAP.md).

- [x] **v0.1:** Core Engine, Virtual Scrolling, Sorting, Filtering.
- [x] **v0.2:** Column Type Conversion, Column Renaming, Advanced Filtering, Context Menu.
- [ ] **Jupyter Integration:** Launch VisiLens directly from a notebook cell (`visilens.view(df)`).
- [ ] **Drag-and-drop file loading**
- [ ] **Plotting:** Quick histograms and scatter plots via Vega-Lite.
- [ ] **Cell Editing:** Edit cells and save changes back to CSV/Parquet.
- [ ] **SQL Support:** Connect directly to SQLite/Postgres/DuckDB.

## 🛠 Development

Want to contribute? Great! Here's how to set up the development environment.

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or pnpm

### Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/PStarH/VisiLens.git
    cd VisiLens
    ```

2.  **Backend Setup**
    ```bash
    # Create virtual environment
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows

    # Install dependencies
    pip install -e ".[dev]"
    ```

3.  **Frontend Setup**
    ```bash
    cd frontend
    npm install
    ```

4.  **Run Locally**

  Terminal 1 (Backend):
  ```bash
  uvicorn backend.main:app --reload --port 8000
  ```

  Terminal 2 (Frontend):
  ```bash
  cd frontend
  npm run dev
  ```

5.  **Build frontend assets (optional)**

  If you prefer to run only the Python CLI (without a separate Vite dev server), you can build the frontend once:

  ```bash
  cd frontend
  npm run build
  ```

  This produces a production bundle under `frontend/dist/` which is copied into `vdweb/static/` for releases. End users then just run:

  ```bash
  visilens path/to/data.csv
  ```

## 🤝 Contributing

For more details, please see [CONTRIBUTING.md](DOCUMENTATION/CONTRIBUTING.md).

### For Contributors: where things live

- **Python package (`vdweb/`):** This is the installable package published to PyPI as `vdweb`. The CLI entrypoints `visilens` and `vdweb` both resolve to `vdweb.cli:main` as configured in `pyproject.toml`.
- **Dev backend (`backend/`):** A separate FastAPI app used only for local development (`uvicorn backend.main:app`). It mirrors the behavior of the packaged backend but is not what users import when they install `visilens`.
- **Core logic:** The VisiData-powered data access layer lives in `vdweb/core.py` (and is mirrored in `backend/core.py` for the dev app). If you want to change how data is loaded/sorted/filtered, start here.

### Typical contributor workflow

1. Edit backend / core logic in `vdweb/` (and update `backend/` if needed for dev parity).
2. Run the dev backend + frontend locally as described in [Development](#-development).
3. If you change the React app and want those changes to ship, run `npm run build` in `frontend/` so the bundle that will be copied into `vdweb/static/` is up to date.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  Made with ❤️ by <a href="https://github.com/PStarH">PStarH</a> and the Open Source Community.
</div>



