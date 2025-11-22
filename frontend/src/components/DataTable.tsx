import { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useQuery } from '@tanstack/react-query';
import { AlertCircle } from 'lucide-react';
import clsx from 'clsx';

interface Column {
  name: string;
  type: string;
  width?: number;
}

interface Row {
  [key: string]: unknown;
}

interface RowsResponse {
  rows: Row[];
  total: number;
}

interface ColumnsResponse {
  columns: Column[];
  count: number;
}

const API_BASE = 'http://localhost:8000';

export function DataTable() {
  const parentRef = useRef<HTMLDivElement>(null);

  // 1. Fetch Columns
  const { 
    data: columnsData, 
    isLoading: isLoadingCols, 
    error: colsError 
  } = useQuery<ColumnsResponse>({
    queryKey: ['columns'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/columns`);
      if (!res.ok) throw new Error('Failed to fetch columns');
      return res.json();
    }
  });

  // 2. Fetch Rows (Initial chunk)
  // In a real app, we'd use infinite query or pagination based on scroll
  const { 
    data: rowsData, 
    isLoading: isLoadingRows, 
    error: rowsError 
  } = useQuery<RowsResponse>({
    queryKey: ['rows'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/rows?start=0&limit=10000`);
      if (!res.ok) throw new Error('Failed to fetch rows');
      return res.json();
    }
  });

  const isLoading = isLoadingCols || isLoadingRows;
  const error = colsError || rowsError;
  const columns = columnsData?.columns || [];
  const rows = rowsData?.rows || [];

  // 3. Virtualizer
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 30, // Fixed 30px row height
    overscan: 20,
  });

  if (isLoading) {
    return (
      <div className="flex h-full flex-col">
        {/* Skeleton Header */}
        <div className="h-12 w-full bg-sidebar border-b border-border skeleton-shimmer" />
        {/* Skeleton Rows */}
        <div className="flex-1 p-0">
          {Array.from({ length: 20 }).map((_, i) => (
            <div
              key={i}
              className="h-[30px] w-full border-b border-border/30 skeleton-shimmer"
              style={{ animationDelay: `${i * 50}ms`, opacity: 1 - i * 0.03 }}
            />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center text-red-400 bg-canvas">
        <AlertCircle className="mr-2 h-5 w-5" />
        <span className="font-mono text-sm">Error: {error instanceof Error ? error.message : 'Unknown error'}</span>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-surface text-primary font-mono text-sm">
      {/* Header - Sticky */}
      <div className="flex border-b border-border bg-sidebar z-10 shrink-0">
        {columns.map((col) => (
          <div
            key={col.name}
            className="flex h-[48px] items-center px-4 border-r border-border last:border-r-0 font-sans font-bold text-xs text-secondary uppercase tracking-wider select-none"
            style={{ width: 150, minWidth: 150 }}
          >
            <div className="flex flex-col gap-0.5 truncate">
              <span>{col.name}</span>
              <span className="text-[10px] text-secondary/50 font-normal lowercase">{col.type}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Virtualized Body */}
      <div
        ref={parentRef}
        className="flex-1 overflow-auto bg-surface"
      >
        <div
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            width: 'max-content', // Allow horizontal scroll if needed
            minWidth: '100%',
            position: 'relative',
          }}
        >
          {rowVirtualizer.getVirtualItems().map((virtualRow) => {
            const row = rows[virtualRow.index];
            return (
              <div
                key={virtualRow.index}
                className={clsx(
                  "flex border-b border-border/50 hover:bg-row-hover transition-colors duration-75",
                  virtualRow.index % 2 === 0 ? "bg-surface" : "bg-surface/50" // Subtle striping
                )}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                }}
              >
                {columns.map((col) => (
                  <div
                    key={col.name}
                    className="flex items-center px-4 border-r border-border/30 last:border-r-0 text-[13px] text-primary/90 whitespace-nowrap overflow-hidden"
                    style={{ width: 150, minWidth: 150 }}
                    title={String(row[col.name] ?? '')}
                  >
                    <span className="truncate w-full">
                      {String(row[col.name] ?? '')}
                    </span>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

