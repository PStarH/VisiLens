/**
 * VisiLens DataTable Component
 *
 * A high-performance virtualized data grid using TanStack Virtual.
 * Communicates with the backend via WebSocket for real-time data.
 */

import { useRef, useEffect, useCallback, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { AlertCircle, WifiOff, RefreshCw, ArrowUp, ArrowDown, Filter, X } from 'lucide-react';
import clsx from 'clsx';
import { useVisiLensSocket, type ConnectionStatus } from '../hooks/useVisiLensSocket';

// --- Constants ---

const ROW_HEIGHT = 30;
const HEADER_HEIGHT = 48;
const COLUMN_WIDTH = 150;
const OVERSCAN = 20;

// --- Sub-components ---

interface ConnectionStatusBadgeProps {
  status: ConnectionStatus;
  onReconnect: () => void;
}

function ConnectionStatusBadge({ status, onReconnect }: ConnectionStatusBadgeProps) {
  if (status === 'connected') return null;

  return (
    <div className="absolute top-2 right-2 z-20 flex items-center gap-2 rounded bg-sidebar/90 px-3 py-1.5 text-xs backdrop-blur">
      {status === 'connecting' && (
        <>
          <RefreshCw className="h-3 w-3 animate-spin text-accent" />
          <span className="text-secondary">Connecting...</span>
        </>
      )}
      {status === 'disconnected' && (
        <>
          <WifiOff className="h-3 w-3 text-yellow-500" />
          <span className="text-secondary">Disconnected</span>
          <button
            onClick={onReconnect}
            className="ml-2 rounded bg-accent/20 px-2 py-0.5 text-accent hover:bg-accent/30"
          >
            Retry
          </button>
        </>
      )}
      {status === 'error' && (
        <>
          <AlertCircle className="h-3 w-3 text-red-500" />
          <span className="text-red-400">Connection Error</span>
          <button
            onClick={onReconnect}
            className="ml-2 rounded bg-accent/20 px-2 py-0.5 text-accent hover:bg-accent/30"
          >
            Retry
          </button>
        </>
      )}
    </div>
  );
}

function SkeletonLoader() {
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

interface ErrorDisplayProps {
  message: string;
  onRetry: () => void;
}

function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 bg-canvas text-center">
      <AlertCircle className="h-12 w-12 text-red-500/50" />
      <div>
        <p className="font-mono text-sm text-red-400">{message}</p>
        <p className="mt-1 text-xs text-secondary">
          Make sure the backend is running on localhost:8000
        </p>
      </div>
      <button
        onClick={onRetry}
        className="flex items-center gap-2 rounded bg-accent/20 px-4 py-2 text-sm text-accent hover:bg-accent/30"
      >
        <RefreshCw className="h-4 w-4" />
        Retry Connection
      </button>
    </div>
  );
}

// --- Main Component ---

export function DataTable({ socket }: { socket: ReturnType<typeof useVisiLensSocket> }) {
  const parentRef = useRef<HTMLDivElement>(null);

  // WebSocket connection and data
  const {
    status,
    error,
    columns,
    rows,
    total,
    isLoading,
    fetchRows,
    sortColumn,
    sortState,
    filterColumn,
    filterState,
    reconnect,
  } = socket;

  // Local state for filter input
  const [activeFilterColumn, setActiveFilterColumn] = useState<string | null>(null);
  const [filterValue, setFilterValue] = useState('');
  const filterInputRef = useRef<HTMLInputElement>(null);

  // Focus input when opening filter
  useEffect(() => {
    if (activeFilterColumn && filterInputRef.current) {
      filterInputRef.current.focus();
    }
  }, [activeFilterColumn]);

  // Virtualizer for row virtualization
  // eslint-disable-next-line react-hooks/incompatible-library
  const rowVirtualizer = useVirtualizer({
    count: total,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: OVERSCAN,
  });

  // Track visible range and fetch data when it changes
  const virtualItems = rowVirtualizer.getVirtualItems();
  const visibleStartIndex = virtualItems[0]?.index ?? 0;
  const visibleEndIndex = virtualItems[virtualItems.length - 1]?.index ?? 0;

  // Fetch rows when visible range changes (debounced via effect)
  const lastFetchRef = useRef({ start: -1, end: -1 });

  const fetchVisibleRows = useCallback(() => {
    // Calculate the range we need (with some buffer)
    const buffer = OVERSCAN * 2;
    const start = Math.max(0, visibleStartIndex - buffer);
    const end = Math.min(total, visibleEndIndex + buffer);
    const limit = end - start + 1;

    // Skip if we already have this data
    if (lastFetchRef.current.start === start && lastFetchRef.current.end === end) {
      return;
    }

    // Check if we need to fetch (if any row in range is missing)
    let needsFetch = false;
    if (rows.size === 0) {
      needsFetch = true;
    } else {
      for (let i = start; i < end; i++) {
        if (!rows.has(i)) {
          needsFetch = true;
          break;
        }
      }
    }

    if (needsFetch && status === 'connected' && limit > 0) {
      lastFetchRef.current = { start, end };
      fetchRows(start, limit);
    }
  }, [visibleStartIndex, visibleEndIndex, total, rows, status, fetchRows]);

  useEffect(() => {
    // Debounce fetch requests
    const timer = setTimeout(fetchVisibleRows, 50);
    return () => clearTimeout(timer);
  }, [fetchVisibleRows]);

  // --- Render States ---

  // Show skeleton while initially loading
  if (isLoading && rows.size === 0) {
    return (
      <div className="relative h-full">
        <ConnectionStatusBadge status={status} onReconnect={reconnect} />
        <SkeletonLoader />
      </div>
    );
  }

  // Show error state
  if (error && rows.size === 0) {
    return <ErrorDisplay message={error} onRetry={reconnect} />;
  }

  // Show No Data state
  if (!isLoading && total === 0 && status === 'connected') {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 bg-canvas text-center">
        <div className="text-secondary text-lg">No Data</div>
        <div className="text-secondary/50 text-sm">The dataset is empty.</div>
      </div>
    );
  }

  // --- Main Grid Render ---

  return (
    <div className="relative flex h-full flex-col bg-surface text-primary font-mono text-sm">
      {/* Connection Status Badge */}
      <ConnectionStatusBadge status={status} onReconnect={reconnect} />

      {/* Header - Sticky */}
      <div
        className="flex border-b border-border bg-sidebar z-10 shrink-0"
        style={{ height: HEADER_HEIGHT }}
      >
        {columns.map((col) => {
          const isSorted = sortState?.column === col.name;
          const isAscending = sortState?.ascending ?? true;
          const isFiltered = filterState?.column === col.name;
          const isFiltering = activeFilterColumn === col.name;

          return (
            <div
              key={col.name}
              className={clsx(
                "group flex items-center px-4 border-r border-border last:border-r-0 font-sans font-bold text-xs text-secondary uppercase tracking-wider select-none transition-colors",
                isFiltering ? "bg-surface" : "hover:bg-row-hover/50"
              )}
              style={{ width: COLUMN_WIDTH, minWidth: COLUMN_WIDTH }}
            >
              {isFiltering ? (
                <div className="flex w-full items-center gap-2">
                  <input
                    ref={filterInputRef}
                    type="text"
                    value={filterValue}
                    onChange={(e) => setFilterValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        filterColumn(col.name, filterValue);
                        setActiveFilterColumn(null);
                      } else if (e.key === 'Escape') {
                        setActiveFilterColumn(null);
                      }
                    }}
                    onBlur={() => {
                      setActiveFilterColumn(null);
                    }}
                    className="h-6 w-full rounded border border-accent/50 bg-canvas px-2 text-xs text-primary focus:border-accent focus:outline-none"
                    placeholder="Filter..."
                  />
                  <button
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => setActiveFilterColumn(null)}
                    className="text-secondary hover:text-primary"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ) : (
                <div className="flex w-full items-center justify-between gap-2">
                  <div
                    className="flex min-w-0 cursor-pointer flex-col gap-0.5"
                    onClick={() => {
                      const ascending = isSorted ? !isAscending : true;
                      sortColumn(col.name, ascending);
                    }}
                  >
                    <span className="truncate text-left">{col.name}</span>
                    <span className="text-left text-[10px] font-normal lowercase text-secondary/50">
                      {col.type}
                    </span>
                  </div>

                  <div className="flex items-center gap-1">
                    {isSorted && (
                      <div className="shrink-0">
                        {isAscending ? (
                          <ArrowUp className="h-3 w-3 text-accent" />
                        ) : (
                          <ArrowDown className="h-3 w-3 text-accent" />
                        )}
                      </div>
                    )}

                    {isFiltered ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          filterColumn(col.name, '');
                        }}
                        className="flex items-center gap-1 rounded border border-accent/40 bg-accent/10 px-2 py-1 text-[10px] font-semibold text-accent hover:bg-accent/20"
                        title={`Filtered by: ${filterState?.term}`}
                      >
                        <Filter className="h-3 w-3" />
                        <span>FILTER</span>
                      </button>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveFilterColumn(col.name);
                          setFilterValue('');
                        }}
                        className="flex items-center gap-1 rounded border border-border/40 bg-sidebar/60 px-2 py-1 text-[10px] font-semibold text-secondary hover:border-accent hover:text-accent"
                      >
                        <Filter className="h-3 w-3" />
                        <span>FILTER</span>
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Virtualized Body */}
      <div
        ref={parentRef}
        className="flex-1 overflow-auto bg-surface"
      >
        <div
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            width: 'max-content',
            minWidth: '100%',
            position: 'relative',
          }}
        >
          {virtualItems.map((virtualRow) => {
            const row = rows.get(virtualRow.index);

            // Show skeleton for rows not yet loaded
            if (!row) {
              return (
                <div
                  key={virtualRow.index}
                  className="flex border-b border-border/30 bg-surface/30"
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    height: `${virtualRow.size}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                    width: columns.length * COLUMN_WIDTH,
                  }}
                >
                  {columns.map((col) => (
                    <div
                      key={col.name}
                      className="flex items-center px-4 border-r border-border/30 last:border-r-0"
                      style={{ width: COLUMN_WIDTH, minWidth: COLUMN_WIDTH }}
                    >
                      <div className="h-3 w-3/4 rounded bg-border/30 skeleton-shimmer" />
                    </div>
                  ))}
                </div>
              );
            }

            return (
              <div
                key={virtualRow.index}
                className={clsx(
                  "flex border-b border-border/50 hover:bg-row-hover transition-colors duration-75",
                  virtualRow.index % 2 === 0 ? "bg-surface" : "bg-surface/50"
                )}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                }}
              >
                {columns.map((col) => {
                  return (
                    <div
                      key={col.name}
                      className={clsx(
                        "flex items-center px-4 border-r border-border/30 last:border-r-0 text-[13px] text-primary/90 whitespace-nowrap overflow-hidden justify-start text-left"
                      )}
                      style={{ width: COLUMN_WIDTH, minWidth: COLUMN_WIDTH }}
                      title={String(row[col.name] ?? '')}
                    >
                      <span className="truncate w-full">
                        {String(row[col.name] ?? '')}
                      </span>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
