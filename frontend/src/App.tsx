/**
 * VisiLens App
 *
 * Main application layout with header, data grid, and status bar.
 * Uses WebSocket for real-time communication with the backend.
 */

import { DataTable } from './components/DataTable';
import { AnalysisSidebar } from './components/AnalysisSidebar';
import { FilterBar, type FilterPayload } from './components/FilterBar';
import { Database, Zap, Filter, ChevronUp, ChevronDown } from 'lucide-react';
import { useVisiLensSocket } from './hooks/useVisiLensSocket';
import { useState, useEffect } from 'react';

function App() {
  const socket = useVisiLensSocket();
  const { total, analysisData, isAnalyzing, columns } = socket;
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Open sidebar when analysis starts or new data arrives
  useEffect(() => {
    if (isAnalyzing || analysisData) {
      const timer = setTimeout(() => setIsSidebarOpen(true), 0);
      return () => clearTimeout(timer);
    }
  }, [isAnalyzing, analysisData]);

  // Handler for filter bar
  // Handler for filter bar
  const handleApplyFilter = (filter: FilterPayload) => {
    console.log('[App] handleApplyFilter received:', filter);
    if (socket.applyFilter) {
      console.log('[App] Calling socket.applyFilter');
      socket.applyFilter(filter);
    } else {
      console.error('[App] socket.applyFilter is not defined');
    }
  };

  const handleResetFilter = () => {
    // Reset filter
    if (socket.applyFilter) {
      socket.applyFilter("reset");
    }
  };

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
          <button
            onClick={() => setIsFilterOpen(!isFilterOpen)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              isFilterOpen 
                ? 'bg-accent text-white shadow-sm' 
                : 'bg-surface text-secondary hover:text-primary hover:bg-surface/80 border border-border/50'
            }`}
          >
            <Filter className="h-3.5 w-3.5" />
            <span>Filter</span>
            {isFilterOpen ? <ChevronUp className="h-3 w-3 ml-0.5" /> : <ChevronDown className="h-3 w-3 ml-0.5" />}
          </button>
          
          <div className="h-4 w-px bg-border/50" />

          <div className="flex items-center gap-1.5 text-xs text-secondary">
            <Zap className="h-3 w-3 text-accent" />
            <span>WebSocket</span>
          </div>
          <div className="text-xs text-secondary">
            Local-first Data Explorer
          </div>
        </div>
      </header>

      {/* FilterBar - Collapsible */}
      {isFilterOpen && (
        <div className="border-b border-border bg-surface animate-in slide-in-from-top-2 duration-200">
          <div className="px-4 py-4">
            <FilterBar
              columns={columns}
              onApplyFilter={handleApplyFilter}
              onResetFilter={handleResetFilter}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-hidden relative flex">
        <div className="flex-1 overflow-hidden relative">
          <DataTable socket={socket} />
        </div>
        <AnalysisSidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          columnName={analysisData?.column ?? (isAnalyzing ? "..." : null)}
          data={analysisData?.data ?? []}
          isLoading={isAnalyzing}
        />
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
