/**
 * VisiLens DataTable Component
 *
 * A high-performance virtualized data grid using TanStack Virtual.
 * Communicates with the backend via WebSocket for real-time data.
 */

import { useRef, useEffect, useCallback, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { AlertCircle, WifiOff, RefreshCw, ArrowUp, ArrowDown, BarChart2 } from 'lucide-react';
import clsx from 'clsx';
import { useVisiLensSocket, type ConnectionStatus } from '../hooks/useVisiLensSocket';
import { HeaderStats } from './HeaderStats';
import { SelectionBar } from './SelectionBar';
import { ContextMenu } from './ContextMenu';

// --- Constants ---

const ROW_HEIGHT = 30;
const HEADER_HEIGHT = 48;
const COLUMN_WIDTH = 150;
const CHECKBOX_WIDTH = 48;
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
    reconnect,
    analyzeColumn,
    getColumnStats,
    subscribeToStats,
    getCachedStats,
    renameColumn,
    setColumnType,
  } = socket;

  // Selection state
  const [selectedRowIndices, setSelectedRowIndices] = useState<Set<number>>(new Set());
  const [isSelectionMode, setIsSelectionMode] = useState(false);

  // Column Management State
  const [editingColumn, setEditingColumn] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; colName: string; type: string } | null>(null);

  // Long press handler refs
  const longPressTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isLongPressRef = useRef(false);
  
  // Drag state for overlay and logic
  const [isDragging, setIsDragging] = useState(false);
  const [dragStartIndex, setDragStartIndex] = useState<number | null>(null);
  const [dragCurrentIndex, setDragCurrentIndex] = useState<number | null>(null);
  const [hasDragged, setHasDragged] = useState(false); // Track if user actually moved mouse

  // Reset selection when total changes (e.g. filter applied)
  useEffect(() => {
    setSelectedRowIndices(new Set());
    setIsSelectionMode(false);
  }, [total]);

  const toggleRow = useCallback((index: number) => {
    setSelectedRowIndices(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      
      // If deselecting the last item, exit selection mode?
      // User might want to keep selection mode open even if empty, 
      // but usually if they clear all, they might want to exit.
      // Let's keep it simple: manual exit via 'X' in SelectionBar.
      
      return newSet;
    });
  }, []);

  const handleRowMouseDown = useCallback((index: number, e: React.MouseEvent | React.TouchEvent) => {
    // Prevent native text selection
    if (e.type === 'mousedown') {
      // Only handle left-click (button 0), ignore right-click (button 2)
      const mouseEvent = e as React.MouseEvent;
      if (mouseEvent.button !== 0) {
        return; // Ignore non-left clicks
      }
      e.preventDefault();
    }

    // If already in selection mode, handle drag start
    if (isSelectionMode) {
      setIsDragging(true);
      // If holding Shift/Ctrl, we might want different logic, but for now just toggle/select
      toggleRow(index); 
      return;
    }

    // If NOT in selection mode:
    // Check if it's a mouse event (Desktop)
    // We can check e.type or use a heuristic. React.MouseEvent has 'button' property.
    const isMouse = e.type === 'mousedown';
    
    if (isMouse) {
      // Desktop: Start drag tracking but don't select yet
      setIsDragging(true);
      setDragStartIndex(index);
      setDragCurrentIndex(index);
      setHasDragged(false); // Reset drag flag
      // Don't set selectedRowIndices yet - wait for actual drag movement
    } else {
      // Touch: Use existing Long Press logic
      isLongPressRef.current = false;
      longPressTimerRef.current = setTimeout(() => {
        isLongPressRef.current = true;
        setIsSelectionMode(true);
        setSelectedRowIndices(new Set([index]));
        // Vibrate if supported
        if (navigator.vibrate) navigator.vibrate(50);
      }, 500); // 500ms long press
    }
  }, [isSelectionMode, toggleRow]);

  const handleRowMouseEnter = useCallback((index: number) => {
    if (isDragging && dragStartIndex !== null) {
      setHasDragged(true); // Mark that user has moved mouse
      setDragCurrentIndex(index);
      setSelectedRowIndices(prev => {
        const newSet = new Set(prev);
        // Add all rows between start and current
        const start = Math.min(dragStartIndex, index);
        const end = Math.max(dragStartIndex, index);
        for (let i = start; i <= end; i++) {
          newSet.add(i);
        }
        return newSet;
      });
    }
  }, [isDragging, dragStartIndex]);

  const handleRowMouseUp = useCallback(() => {
    const wasDragging = isDragging;
    const actuallyDragged = hasDragged;
    
    setIsDragging(false);
    setDragStartIndex(null);
    setDragCurrentIndex(null);
    setHasDragged(false);
    
    // Only enter selection mode if user actually dragged (not just clicked)
    if (wasDragging && actuallyDragged && selectedRowIndices.size > 0) {
      setIsSelectionMode(true);
    } else if (wasDragging && !actuallyDragged) {
      // Clear selection if it was just a click without drag
      setSelectedRowIndices(new Set());
    }
    
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  }, [isDragging, hasDragged, selectedRowIndices.size]);

  const toggleAll = useCallback(() => {
    setSelectedRowIndices(prev => {
      if (prev.size === total && total > 0) {
        return new Set();
      } else {
        // Select all indices
        const newSet = new Set<number>();
        for (let i = 0; i < total; i++) {
          newSet.add(i);
        }
        return newSet;
      }
    });
  }, [total]);

  const handleExportCSV = useCallback(() => {
    if (selectedRowIndices.size === 0) return;
    
    const header = columns.map(c => c.name).join(',');
    const csvRows = [];
    
    for (const index of selectedRowIndices) {
      const row = rows.get(index);
      if (row) {
        const values = columns.map(c => {
          const val = row[c.name];
          const str = String(val ?? '');
          if (str.includes(',') || str.includes('"') || str.includes('\n')) {
            return `"${str.replace(/"/g, '""')}"`;
          }
          return str;
        });
        csvRows.push(values.join(','));
      }
    }
    
    const csvContent = [header, ...csvRows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'export.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [selectedRowIndices, columns, rows]);

  const handleExportJSON = useCallback(() => {
    if (selectedRowIndices.size === 0) return;
    
    const jsonRows = [];
    for (const index of selectedRowIndices) {
      const row = rows.get(index);
      if (row) {
        jsonRows.push(row);
      }
    }
    
    const jsonContent = JSON.stringify(jsonRows, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'export.json');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [selectedRowIndices, rows]);

  // Log stats reception
  useEffect(() => {
    // console.log(`[DataTable] Stats cache updated`, statsCache);
  }, []);

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

  // Prefetching wrapper
  const handleFetchStats = useCallback((columnName: string) => {
    // Fetch requested column
    getColumnStats(columnName);
    
    // Predictive prefetch: Fetch next column too
    const idx = columns.findIndex(c => c.name === columnName);
    if (idx !== -1 && idx < columns.length - 1) {
      const nextCol = columns[idx + 1];
      // Small delay to prioritize the hovered column's request on the network
      setTimeout(() => {
        getColumnStats(nextCol.name);
      }, 50);
    }
  }, [columns, getColumnStats]);

  const handleRenameSubmit = useCallback((newName: string) => {
    if (editingColumn && newName && newName.trim() !== '' && newName !== editingColumn) {
      renameColumn(editingColumn, newName);
    }
    setEditingColumn(null);
  }, [editingColumn, renameColumn]);

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
      {/* Error Banner */}
      {error && (
        <div className="bg-destructive/10 border-b border-destructive/20 px-4 py-2 text-xs text-destructive flex items-center justify-between">
          <span>{error}</span>
          <button 
            onClick={reconnect}
            className="hover:underline font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Connection Status Badge */}
      <ConnectionStatusBadge status={status} onReconnect={reconnect} />

      {/* Header - Sticky */}
      <div
        className="flex border-b border-border bg-sidebar z-10 shrink-0"
        style={{ height: HEADER_HEIGHT }}
      >

        {isSelectionMode && (
          <div
            className="flex items-center justify-center border-r border-border bg-sidebar z-10 shrink-0"
            style={{ width: CHECKBOX_WIDTH, minWidth: CHECKBOX_WIDTH }}
          >
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-gray-500 bg-transparent text-accent focus:ring-accent focus:ring-offset-0"
              checked={total > 0 && selectedRowIndices.size === total}
              onChange={toggleAll}
              title="Select All"
            />
          </div>
        )}
        {columns.map((col) => {
          const isSorted = sortState?.column === col.name;
          const isAscending = sortState?.ascending ?? true;

          return (
            <div
              key={col.name}
              className="group border-r border-border last:border-r-0 font-sans font-bold text-xs text-secondary uppercase tracking-wider select-none transition-colors relative hover:bg-row-hover/50"
              style={{ width: COLUMN_WIDTH, minWidth: COLUMN_WIDTH }}
              onContextMenu={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setContextMenu({ x: e.clientX, y: e.clientY, colName: col.name, type: col.type });
              }}
            >
              <HeaderStats
                columnName={col.name}
                columnType={col.type}
                onFetchStats={handleFetchStats}
                registerStatsListener={subscribeToStats}
                getCachedStats={getCachedStats}
                disabled={editingColumn === col.name}
              >
                <div 
                  className="flex items-center px-4 w-full h-full cursor-pointer"
                  onClick={() => {
                    if (editingColumn !== col.name) {
                      const ascending = isSorted ? !isAscending : true;
                      sortColumn(col.name, ascending);
                    }
                  }}
                  onDoubleClick={(e) => {
                    e.stopPropagation();
                    if (editingColumn !== col.name) {
                      setEditingColumn(col.name);
                    }
                  }}
                >
                  {editingColumn === col.name ? (
                    <input
                      autoFocus
                      defaultValue={col.name}
                      className="w-full bg-surface text-primary px-1 py-0.5 text-xs border border-accent rounded outline-none"
                      onBlur={(e) => handleRenameSubmit(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleRenameSubmit(e.currentTarget.value);
                        } else if (e.key === 'Escape') {
                          setEditingColumn(null);
                        }
                      }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <div className="flex w-full items-center justify-between gap-2">
                      <div className="flex min-w-0 flex-col gap-0.5">
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

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            analyzeColumn(col.name);
                          }}
                          className="p-1 text-secondary hover:text-accent rounded hover:bg-accent/10 opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Analyze Column Distribution"
                        >
                          <BarChart2 className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </HeaderStats>
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
          onMouseLeave={handleRowMouseUp} // Stop drag if leaving the grid area
        >
          {/* Drag Overlay */}
          {isDragging && dragStartIndex !== null && dragCurrentIndex !== null && (
            <div
              className="absolute left-0 right-0 bg-accent/20 border border-accent/30 pointer-events-none z-20"
              style={{
                top: Math.min(dragStartIndex, dragCurrentIndex) * ROW_HEIGHT,
                height: (Math.abs(dragCurrentIndex - dragStartIndex) + 1) * ROW_HEIGHT,
              }}
            />
          )}

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
                    width: columns.length * COLUMN_WIDTH + (isSelectionMode ? CHECKBOX_WIDTH : 0),
                  }}
                >
                  {isSelectionMode && (
                    <div
                      className="flex items-center justify-center border-r border-border/30"
                      style={{ width: CHECKBOX_WIDTH, minWidth: CHECKBOX_WIDTH }}
                    >
                      <div className="h-4 w-4 rounded bg-border/30 skeleton-shimmer" />
                    </div>
                  )}
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
                  "flex border-b border-border/50 hover:bg-row-hover transition-colors duration-75 select-none",
                  virtualRow.index % 2 === 0 ? "bg-surface" : "bg-surface/50"
                )}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                }}
                onMouseDown={(e) => handleRowMouseDown(virtualRow.index, e)}
                onMouseEnter={() => handleRowMouseEnter(virtualRow.index)}
                onMouseUp={handleRowMouseUp}
                onTouchStart={(e) => handleRowMouseDown(virtualRow.index, e)}
                onTouchEnd={handleRowMouseUp}
              >
                {/* Checkbox Cell */}
                {isSelectionMode && (
                  <div
                    className="flex items-center justify-center border-r border-border/30"
                    style={{ width: CHECKBOX_WIDTH, minWidth: CHECKBOX_WIDTH }}
                  >
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-gray-500 bg-transparent text-accent focus:ring-accent focus:ring-offset-0 cursor-pointer"
                      checked={selectedRowIndices.has(virtualRow.index)}
                      onChange={() => toggleRow(virtualRow.index)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                )}

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


      {!isDragging && (
        <SelectionBar
          selectedCount={selectedRowIndices.size}
          onExportCSV={handleExportCSV}
          onExportJSON={handleExportJSON}
          onClearSelection={() => {
            setSelectedRowIndices(new Set());
            setIsSelectionMode(false);
          }}
        />
      )}

      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          colName={contextMenu.colName}
          currentType={contextMenu.type}
          onClose={() => setContextMenu(null)}
          onRename={() => setEditingColumn(contextMenu.colName)}
          onTypeChange={(type) => setColumnType(contextMenu.colName, type)}
        />
      )}
    </div>
  );
}
