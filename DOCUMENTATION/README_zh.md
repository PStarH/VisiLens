<div align="center">
  <img src="https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/banner.svg" alt="VisiLens Logo" width="100%" />
  
  # VisiLens

  **开发者专属的 Excel**

  > **秒开百万行数据 · 本地优先、极速、轻量。**
  
  VisiLens 是一款面向数据集探索的高性能、本地优先 Web GUI。它依靠 [VisiData](https://www.visidata.org/) 的强大能力，让你可以实时查看和过滤 CSV、Parquet、Excel 和 JSON 文件。

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![VisiData Engine](https://img.shields.io/badge/Engine-VisiData-orange.svg)](https://www.visidata.org/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://reactjs.org/)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
  [![PyPI](https://img.shields.io/pypi/v/vdweb.svg)](https://pypi.org/project/vdweb/0.1.1/)

  [English](../README.md) • [简体中文](README_zh.md) • [Español](README_es.md) • [日本語](README_ja.md) • [Русский](README_ru.md)

  [特性](#特性) • [安装](#安装) • [使用](#使用) • [架构](#架构) • [贡献](#贡献)
</div>

---

## 🚀 为什么选择 VisiLens？

探索数据时，你不再需要编写大量样板式的 Pandas 代码，也不用苦等像 Excel 这样臃肿的电子表格软件慢慢加载。**VisiLens** 是一款现代化的 **CSV 查看器** 和 **Parquet 浏览器**，它融合了 **VisiData** 的疾速性能与轻量级 Web 界面。

- **⚡️ 数秒内加载百万行数据：** 内置高度优化的 VisiData 引擎。
- **🔒 完全本地化：** 数据始终留在本机，无需上传云端。
- **🛠 零配置：** CLI 优先的工作流：通过管道传入数据，快速探索，然后继续编码。
- **🔌 广泛格式支持：** 支持 CSV、TSV、JSON、Parquet、Excel、SQLite 以及 [50+ 种其他格式](https://www.visidata.org/formats/)。

## ✨ 特性

- **即时数据可视化：** 只需运行 `vdweb data.csv`，即可瞬间可视化大型数据集。
- **超强的后端排序与过滤：** 依托 VisiData 引擎，对数百万行数据执行复杂查询依然流畅。
- **虚拟化表格组件：** 基于 React 的虚拟化表格（数据网格），长表滚动依然顺滑。
- **零配置上手：** 无需额外数据库或服务，直接作为独立的 CSV/Parquet 查看器使用。

### 📂 支持的格式
VisiLens 依托 VisiData 的加载器，开箱即用地支持多种格式：
- **表格类：** `.csv`, `.tsv`, `.xlsx` (Excel), `.parquet`
- **结构化数据：** `.json`, `.jsonl`, `.yaml`
- **数据库：** `.sqlite`, `.db`
- **代码 / 其他：** `.pcap` (Wireshark), `.xml`, `.html` 表格

## 📊 基准测试

我们对性能有着极致的追求。以下是在一台标准 MacBook Air (M2) 上打开 **一百万行** CSV 数据集时，VisiLens 与常用工具的对比：

| 工具 | 加载时间 (100 万行) | 内存占用 | 交互式排序 |
| :--- | :--- | :--- | :--- |
| **VisiLens** | **~1.7s** | **极低 (< 50MB 总计)** | **即时** (后端: < 0.4s) |
| Excel | > 30s (经常崩溃) | 高 (占用大量 RAM) | 缓慢/无响应 |
| **基于 Pandas 的 GUI** | > 15s (冷启动) | 高 (整个 DataFrame 载入 RAM) | 迟缓 (非虚拟化) |
| Jupyter (print df) | 快 | 中等 | 静态文本 |

*测试数据：100 万行、3 列（混合类型）。数据来自开发过程中在 MacBook Air M2 上的真实场景。*

## 📦 安装

VisiLens 已发布为 Python 包。

```bash
pip install vdweb
```

*注意：VisiLens 需要 Python 3.10 或更高版本。*

## 💻 使用

### 命令行界面 (CLI)

VisiLens 的核心使用方式是通过命令行。

```bash
# 打开一个 CSV 文件
vdweb data.csv

# 打开一个 Parquet 文件
vdweb large-dataset.parquet

# 打开一个 Excel 文件
vdweb spreadsheet.xlsx

# 启动时不自动打开浏览器
vdweb data.json --no-browser

# 指定自定义端口
vdweb data.csv --port 9000
```

### Web 界面

启动后，VisiLens 会在您的默认浏览器中自动打开（通常是 `http://localhost:8000`）。

1.  **查看数据：** 高效流畅地滚动浏览您的数据集。
2.  **排序：** 点击列标题即可进行升序/降序排序。
3.  **过滤：** 使用过滤输入框在列内进行搜索。
4.  **加载新数据：** (即将推出) 直接将文件拖放到窗口中。

## 🏗 架构

VisiLens 建立在为性能而生的强大现代技术栈之上：

*   **后端：** FastAPI 服务器作为 VisiData 和浏览器之间的桥梁。
*   **通信：** WebSockets 按需流式传输数据切片。
*   **前端：** React 网格仅渲染视口内可见的内容。

![架构图](https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/diagram.png)

## 🗺 路线图

我们正在积极努力，致力于将 VisiLens 打造成最强的本地数据浏览工具。

- [x] **v0.1:** 核心引擎，虚拟滚动，排序，过滤。
- [ ] **Jupyter 集成：** 直接从 Notebook 单元格启动 VisiLens (`visilens.view(df)`)。
- [ ] **拖放文件加载**
- [ ] **绘图：** 通过 Vega-Lite 快速绘制直方图和散点图。
- [ ] **编辑：** 编辑单元格并将更改保存回 CSV/Parquet。
- [ ] **SQL 支持：** 直接连接到 SQLite/Postgres/DuckDB。

## 🛠 开发

如果你有任何精彩的想法，以下是如何设置开发环境。

### 先决条件

- Python 3.10+
- Node.js 18+
- npm 或 pnpm

### 设置

1.  **克隆仓库**
    ```bash
    git clone https://github.com/PStarH/VisiLens.git
    cd VisiLens
    ```

2.  **后端设置**
    ```bash
    # 创建虚拟环境
    python -m venv .venv
    source .venv/bin/activate  # 或者在 Windows 上使用 .venv\Scriptsctivate

    # 安装依赖
    pip install -e ".[dev]"
    ```

3.  **前端设置**
    ```bash
    cd frontend
    npm install
    ```

4.  **本地运行**

  终端 1 (后端):
  ```bash
  uvicorn backend.main:app --reload --port 8000
  ```

  终端 2 (前端):
  ```bash
  cd frontend
  npm run dev
  ```

5.  **构建前端资源 (可选)**

  如果您只想运行 Python CLI（无需单独的 Vite 开发服务器），您可以构建一次前端：

  ```bash
  cd frontend
  npm run build
  ```

  这会在 `frontend/dist/` 下生成一个生产包，该包会被复制到 `vdweb/static/` 以供发布。最终用户只需运行：

  ```bash
  vdweb path/to/data.csv
  ```

## 🤝 贡献

### 对于贡献者：项目结构

- **Python 包 (`vdweb/`):** 这是发布到 PyPI 的可安装包。CLI 入口点 `vdweb` / `visilens` 都解析为 `vdweb.cli:main`，如 `pyproject.toml` 中配置的那样。
- **开发后端 (`backend/`):** 一个仅用于本地开发的独立 FastAPI 应用程序 (`uvicorn backend.main:app`)。它镜像了打包后后端的行为，但并非用户安装 `vdweb` 时导入的内容。
- **核心逻辑：** VisiData 驱动的数据访问层位于 `vdweb/core.py`（并在 `backend/core.py` 中为开发应用程序镜像）。如果您想更改数据的加载/排序/过滤方式，请从这里开始。

### 典型的贡献者工作流程

1. 在 `vdweb/` 中编辑后端/核心逻辑（如果需要保持开发环境一致，也请更新 `backend/`）。
2. 按照 [开发](#-开发) 中的描述在本地运行开发后端 + 前端。
3. 如果您更改了 React 应用程序并希望发布这些更改，请在 `frontend/` 中运行 `npm run build`，以便将复制到 `vdweb/static/` 的包更新为最新版本。

## 📄 许可证

本项目根据 MIT 许可证授权 - 有关详细信息，请参阅 [LICENSE](../LICENSE) 文件。

---

<div align="center">
  由 <a href="https://github.com/PStarH">PStarH</a> 和开源社区用 ❤️ 制作。
</div>
