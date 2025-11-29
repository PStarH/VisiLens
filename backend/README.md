# VisiLens Backend (Development)

This directory contains the development backend for VisiLens. It is a **FastAPI** application that serves as the bridge between the **VisiData** engine and the React frontend during local development.

> **Note:** The actual production backend logic is packaged in `../vdweb/`, but this directory mirrors that logic for easier debugging and feature development.

## 🛠 Setup

1.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Running Locally

Start the development server with hot-reloading:

```bash
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

## 📂 Key Files

*   **`main.py`**: The FastAPI application entry point. Handles WebSocket connections and HTTP endpoints.
*   **`core.py`**: Contains the core logic for interacting with VisiData (loading sheets, sorting, filtering). This file should be kept in sync with `../vdweb/core.py`.
