/**
 * VisiLens App
 *
 * Main application layout with header, data grid, and status bar.
 * Uses WebSocket for real-time communication with the backend.
 */

import { DataTable } from './components/DataTable';
import { Database, Zap } from 'lucide-react';
import { useVisiLensSocket } from './hooks/useVisiLensSocket';

function App() {
  const socket = useVisiLensSocket();
  const { total } = socket;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-canvas text-primary font-sans">
      {/* App Header */}
      <header className="flex h-12 items-center border-b border-border bg-sidebar px-4 shrink-0">
        <div className="flex items-center gap-2 font-semibold">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-accent text-white">
            <Database className="h-4 w-4" />
          </div>
          <span className="text-sm tracking-tight text-primary">VisiLens</span>
        </div>
        <div className="ml-auto flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs text-secondary">
            <Zap className="h-3 w-3 text-accent" />
            <span>WebSocket</span>
          </div>
          <div className="text-xs text-secondary">
            Local-first Data Explorer
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden relative">
        <DataTable socket={socket} />
      </main>

      {/* Status Bar */}
      <footer className="flex h-6 items-center border-t border-border bg-sidebar/50 px-3 text-[11px] text-secondary shrink-0 select-none">
        <div className="flex items-center gap-3">
          <span>ws://localhost:8000</span>
          <span className="text-border">|</span>
          <span>Total Rows: {total.toLocaleString()}</span>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <span>UTF-8</span>
          <span>VisiData Engine</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
