<div align="center">
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
  <img src="https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/banner.svg" alt="VisiLens Logo" width="100%" />
</div>  
  # VisiLens

  **Excel for Developers**

  > **Open 1M+ rows in seconds. Local-first, zero-config, instant preview.**
  
  A high-performance, **local-first** web GUI for exploring datasets. Instantly view, filter, and analyze CSV, Parquet, Excel, and JSON files using the power of [VisiData](https://www.visidata.org/) without installing heavy spreadsheet software.

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![VisiData Engine](https://img.shields.io/badge/Engine-VisiData-orange.svg)](https://www.visidata.org/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://reactjs.org/)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
  [![PyPI](https://img.shields.io/pypi/v/vdweb.svg)](https://pypi.org/project/vdweb/)
  
  <!-- Growth Badges -->
  [![GitHub stars](https://img.shields.io/github/stars/PStarH/VisiLens.svg?style=social&label=Star&maxAge=2592000)](https://github.com/PStarH/VisiLens/stargazers/)
  [![GitHub forks](https://img.shields.io/github/forks/PStarH/VisiLens.svg?style=social&label=Fork&maxAge=2592000)](https://github.com/PStarH/VisiLens/network/)
  [![GitHub watchers](https://img.shields.io/github/watchers/PStarH/VisiLens.svg?style=social&label=Watch&maxAge=2592000)](https://github.com/PStarH/VisiLens/watchers/)
  [![GitHub issues](https://img.shields.io/github/issues/PStarH/VisiLens.svg)](https://github.com/PStarH/VisiLens/issues)

  [English](README.md) • [简体中文](DOCUMENTATION/README_zh.md) • [Español](DOCUMENTATION/README_es.md) • [日本語](DOCUMENTATION/README_ja.md) • [Русский](DOCUMENTATION/README_ru.md)

  [Quickstart](#-quickstart) • [Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Contributing](#-contributing)


<div align="center">
  <img src="https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/demo.gif" alt="VisiLens Demo" width="100%" />
</div>

---

## ⚡ Quickstart

Get up and running in seconds. No database setup, no configuration.

```bash
# 1. Install via pip
pip install visilens

# 2. Open any file
visilens data.csv
```

> **Note:** The PyPI package name is **`vdweb`**, but the CLI tool is **`visilens`**.

---

## 🚀 Why VisiLens?

Data exploration shouldn't require writing boilerplate Pandas code or waiting for heavy spreadsheet software like Excel to load. **VisiLens** is a modern **CSV viewer** and **Parquet explorer** that combines the raw speed of **VisiData** with a lightweight web interface.

- **⚡️ Load 1M rows in under 2 seconds:** Powered by VisiData's highly optimized engine.
- **🔒 Local-First & Secure:** Your data never leaves your machine. No cloud uploads, no external dependencies.
- **🛠 Zero Config:** CLI-first workflow. Pipe data in, explore, and get back to coding.
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

### 📂 Project Structure

A quick look at the codebase to help you navigate:

```
VisiLens/
├── vdweb/               # 📦 The Python Package (PyPI)
│   ├── cli.py           #    Entry point (visilens command)
│   ├── core.py          #    VisiData integration logic
│   └── static/          #    Compiled frontend assets
├── backend/             # 🛠 Development Backend
│   └── main.py          #    FastAPI app for local dev
├── frontend/            # ⚛️ React Frontend
│   ├── src/             #    Source code
│   └── vite.config.ts   #    Build configuration
└── DOCUMENTATION/       # 📚 Multi-language docs & guides
```

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

## ❓ FAQ
 
**Q: Why is the package named `vdweb` but the command is `visilens`?**  
A: The project started as `vdweb` (VisiData Web). We rebranded to **VisiLens** to better reflect our vision. We kept the package name `vdweb` on PyPI to avoid breaking existing installs, but we recommend using the `visilens` command.
 
**Q: Can I use this on a remote server?**  
A: Yes! You can run `visilens data.csv --port 8080 --no-browser` on a remote server and access it via SSH tunneling or directly if the port is exposed.
 
**Q: Does it support editing data?**  
A: Currently, VisiLens is primarily for **exploration and analysis**. Basic cell editing is on our roadmap.
 
## 🌍 Help Us Improve Translations!
 
VisiLens is used globally, and we want to make it accessible to everyone. Our documentation is currently available in English, Chinese, Spanish, Japanese, and Russian, but we need your help to keep them accurate!
 
*   **Found a typo?** Please submit a PR!
*   **Want to add a new language?** We'd love to support it.
 
See [DOCUMENTATION/](DOCUMENTATION/) for existing translations.
 
## 🤝 Contributing
 
We welcome contributions of all kinds! Whether it's fixing a bug, improving documentation, or adding a new feature.
 
👉 **[Read our Contributing Guide](DOCUMENTATION/CONTRIBUTING.md)** to get started.
 
## 💬 Community & Support
 
We'd love to hear from you!
 
*   **⭐ [Star us on GitHub](https://github.com/PStarH/VisiLens):** If you find VisiLens useful, please give us a star! It helps us reach more developers.
*   **[GitHub Discussions](https://github.com/PStarH/VisiLens/discussions):** The best place for Q&A, feature requests, and showing off what you've built.
*   **[Issues](https://github.com/PStarH/VisiLens/issues):** Report bugs or suggest specific enhancements.
 
## ✨ Contributors
 
Thanks goes to these wonderful people:
 
<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://pstarh.github.io/website"><img src="https://avatars.githubusercontent.com/u/176644217?v=4?s=32" width="32px;" alt="Xinghan Pan"/><br /><sub><b>Xinghan Pan</b></sub></a><br /><a href="https://github.com/PStarH/VisiLens/commits?author=PStarH" title="Code">💻</a> <a href="https://github.com/PStarH/VisiLens/commits?author=PStarH" title="Documentation">📖</a> <a href="#design-PStarH" title="Design">🎨</a> <a href="#ideas-PStarH" title="Ideas, Planning, & Feedback">🤔</a> <a href="#infra-PStarH" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#maintenance-PStarH" title="Maintenance">🚧</a></td>
    </tr>
  </tbody>
  <tfoot>
    <tr>
      <td align="center" size="13px" colspan="7">
        <img src="https://raw.githubusercontent.com/all-contributors/all-contributors-cli/1b8533af435da9854653492b1327a23a4dbd0a10/assets/logo-small.svg">
          <a href="DOCUMENTATION/CONTRIBUTING.md">Add your contributions</a>
        </img>
      </td>
    </tr>
  </tfoot>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
 
This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!

### For Contributors: where things live
 
<details>
<summary>Click to expand technical details</summary>
 
- **Python package (`vdweb/`):** This is the installable package published to PyPI as `vdweb`. The CLI entrypoints `visilens` and `vdweb` both resolve to `vdweb.cli:main` as configured in `pyproject.toml`.
- **Dev backend (`backend/`):** A separate FastAPI app used only for local development (`uvicorn backend.main:app`). It mirrors the behavior of the packaged backend but is not what users import when they install `visilens`.
- **Core logic:** The VisiData-powered data access layer lives in `vdweb/core.py` (and is mirrored in `backend/core.py` for the dev app). If you want to change how data is loaded/sorted/filtered, start here.
 
#### Typical contributor workflow
 
1. Edit backend / core logic in `vdweb/` (and update `backend/` if needed for dev parity).
2. Run the dev backend + frontend locally as described in [Development](#-development).
3. If you change the React app and want those changes to ship, run `npm run build` in `frontend/` so the bundle that will be copied into `vdweb/static/` is up to date.
</details>
 
## 📈 Star History
 
[![Star History Chart](https://api.star-history.com/svg?repos=PStarH/VisiLens&type=Date)](https://star-history.com/#PStarH/VisiLens&Date)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  Made with ❤️ by <a href="https://github.com/PStarH">PStarH</a> and the Open Source Community.
</div>

