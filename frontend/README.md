# VisiLens Frontend

The frontend for VisiLens is a high-performance **React** application built with **Vite** and **TypeScript**. It uses a virtualized grid to render millions of rows efficiently.

## 🛠 Setup

1.  **Install dependencies:**
    ```bash
    npm install
    ```

## 🚀 Running Locally

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173` (proxies API requests to `http://localhost:8000`).

## 📦 Building for Production

To build the frontend assets for the Python package:

```bash
npm run build
```

This generates the production bundle in `dist/`, which is then copied to `../vdweb/static/` for distribution.

## 📂 Key Components

*   **`src/components/DataTable.tsx`**: The main virtualized grid component.
*   **`src/components/FilterBar.tsx`**: The advanced filtering interface.
*   **`src/api/socket.ts`**: WebSocket client for communicating with the backend.
*   **`src/App.tsx`**: Main application layout and state management.
