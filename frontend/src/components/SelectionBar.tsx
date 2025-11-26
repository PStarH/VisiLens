import { Download, X } from 'lucide-react';

interface SelectionBarProps {
  selectedCount: number;
  onExportCSV: () => void;
  onExportJSON: () => void;
  onClearSelection: () => void;
}

export function SelectionBar({ selectedCount, onExportCSV, onExportJSON, onClearSelection }: SelectionBarProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 rounded-lg bg-gray-900 text-white px-6 py-3 shadow-xl animate-in slide-in-from-bottom-4 fade-in duration-200 border border-gray-800">
      <div className="flex items-center gap-2 mr-2">
        <span className="font-medium text-sm">{selectedCount} rows selected</span>
        <button 
          onClick={onClearSelection}
          className="p-1 hover:bg-white/20 rounded-full transition-colors"
          title="Clear selection"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
      
      <div className="h-5 w-px bg-white/20" />
      
      <div className="flex items-center gap-2">
        <button
          onClick={onExportCSV}
          className="flex items-center gap-2 rounded bg-white/10 px-3 py-1.5 text-xs font-medium hover:bg-white/20 transition-colors"
        >
          <Download className="h-3 w-3" />
          CSV
        </button>
        <button
          onClick={onExportJSON}
          className="flex items-center gap-2 rounded bg-white/10 px-3 py-1.5 text-xs font-medium hover:bg-white/20 transition-colors"
        >
          <Download className="h-3 w-3" />
          JSON
        </button>
      </div>
    </div>
  );
}
