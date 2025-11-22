import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DataTable } from './components/DataTable';
import { Database, CheckCircle2 } from 'lucide-react';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
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
            <div className="text-xs text-secondary">
              Local-first Data Explorer
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden relative">
          <DataTable />
        </main>

        {/* Status Bar */}
        <footer className="flex h-6 items-center border-t border-border bg-accent/10 px-3 text-[11px] text-secondary shrink-0 select-none">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3 w-3 text-accent" />
            <span>Ready</span>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <span>UTF-8</span>
            <span>Python 3.12</span>
          </div>
        </footer>
      </div>
    </QueryClientProvider>
  );
}

export default App;
