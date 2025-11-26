import { useState, useEffect, useRef, useCallback } from 'react';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface Column {
  name: string;
  type: string;
  width?: number;
}

interface Row {
  [key: string]: unknown;
}

interface WebSocketMessage {
  action: string;
  success: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data?: any;
  error?: string;
}

interface SortState {
  column: string;
  ascending: boolean;
}

interface FilterState {
  column: string;
  term: string;
}

const WS_URL = 'ws://localhost:8000/ws';

interface AnalysisItem {
  name: string;
  count: number;
  percent: number;
}

interface ColumnStats {
  null_count: number;
  null_percent: number;
  unique_count: number;
  is_sample: boolean;
  scanned_rows: number;
  total_rows: number;
  min?: number;
  max?: number;
  mean?: number;
  type: 'numeric' | 'string';
}

export function useVisiLensSocket() {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [error, setError] = useState<string | null>(null);
  const [columns, setColumns] = useState<Column[]>([]);
  const [rows, setRows] = useState<Map<number, Row>>(new Map());
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [sortState, setSortState] = useState<SortState | null>(null);
  const [filterState, setFilterState] = useState<FilterState | null>(null);
  const [analysisData, setAnalysisData] = useState<{ column: string; data: AnalysisItem[] } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Use refs for stats to avoid re-rendering the entire table when one column updates
  // Use Map for LRU cache (preserves insertion order)
  const statsCacheRef = useRef<Map<string, ColumnStats>>(new Map());
  const statsListenersRef = useRef<Map<string, Set<(stats: ColumnStats) => void>>>(new Map());
  const MAX_CACHE_SIZE = 100;
  const MAX_ROWS_CACHED = 2000; // Window size for row cache

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Store rows in a map for random access by index
  // This is crucial for virtualization where we might receive chunks out of order
  const rowsMapRef = useRef<Map<number, Row>>(new Map());

  // Use a ref to hold the connect function to avoid circular dependency in useCallback
  const connectRef = useRef<() => void>(() => { });

  const connect = useCallback(() => {
    try {
      setStatus('connecting');
      setError(null);

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        setIsLoading(false);
        // Initial data fetch
        ws.send(JSON.stringify({ action: 'get_columns' }));
        ws.send(JSON.stringify({ action: 'get_rows', start: 0, limit: 100 }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (!message.success) {
            console.error('WebSocket Error:', message.error);
            setError(message.error || 'Unknown error');
            // If analysis failed, stop the spinner
            if (message.action === 'analysis_result') {
              setIsAnalyzing(false);
            }
            return;
          }

          switch (message.action) {
            case 'columns':
              setColumns(message.data.columns);
              break;
            case 'rows': {
              const { header, rows: newRowsData, start, total: totalRows, reset } = message.data;

              if (reset) {
                rowsMapRef.current.clear();
              }

              setTotal(totalRows);

              // Convert array-of-arrays to objects using header
              // This is done lazily here, but could be deferred to render time for more memory savings
              // For now, we keep the Row interface compatible
              newRowsData.forEach((rowValues: unknown[], index: number) => {
                const rowObj: Row = {};
                header.forEach((colName: string, colIdx: number) => {
                  rowObj[colName] = rowValues[colIdx];
                });
                rowsMapRef.current.set(start + index, rowObj);
              });

              // Eviction Policy: Keep cache size within limits
              // We remove rows that are furthest from the current viewport (approximated by 'start')
              // Simple strategy: If size > MAX, delete keys outside [start - 1000, start + 1000]
              if (rowsMapRef.current.size > MAX_ROWS_CACHED) {
                const keysToDelete: number[] = [];
                const keepStart = Math.max(0, start - MAX_ROWS_CACHED / 2);
                const keepEnd = start + MAX_ROWS_CACHED / 2;

                for (const key of rowsMapRef.current.keys()) {
                  if (key < keepStart || key > keepEnd) {
                    keysToDelete.push(key);
                  }
                }
                keysToDelete.forEach(k => rowsMapRef.current.delete(k));
              }

              // Update state with a new Map to trigger re-render
              setRows(new Map(rowsMapRef.current));
              break;
            }
            case 'sorted': {
              // Update sort state
              if (message.data.state?.sort) {
                setSortState({
                  column: message.data.state.sort.column,
                  ascending: message.data.state.sort.ascending
                });
              }
              statsCacheRef.current.clear(); // Clear stats cache on sort
              break;
            }
            case 'filtered': {
              // Clear rows map - will be refilled with filtered data
              rowsMapRef.current.clear();
              setRows(new Map());
              setTotal(message.data.total);
              if (message.data.state?.filter) {
                setFilterState({
                  column: message.data.state.filter.column,
                  term: message.data.state.filter.term
                });
              } else {
                setFilterState(null);
              }
              statsCacheRef.current.clear(); // Clear stats cache on filter
              break;
            }
            case 'reset': {
              // Clear sort state and rows map
              setSortState(null);
              setFilterState(null);
              rowsMapRef.current.clear();
              setRows(new Map());
              setTotal(message.data.total);
              statsCacheRef.current.clear(); // Clear stats cache on reset
              break;
            }
            case 'analysis_result': {
              setAnalysisData({
                column: message.data.column,
                data: message.data.data
              });
              setIsAnalyzing(false);
              break;
            }
            case 'stats_result': {
              const { column, data } = message.data;

              // LRU Logic
              const cache = statsCacheRef.current;
              if (cache.has(column)) {
                cache.delete(column); // Re-insert to update order (mark as recently used)
              } else if (cache.size >= MAX_CACHE_SIZE) {
                const oldestKey = cache.keys().next().value;
                if (oldestKey) cache.delete(oldestKey);
              }
              cache.set(column, data);

              // Notify listeners
              const listeners = statsListenersRef.current.get(column);
              if (listeners) {
                listeners.forEach(cb => cb(data));
              }
              break;
            }
            case 'info':
              // Handle dataset info if needed
              break;
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onclose = () => {
        setStatus('disconnected');
        wsRef.current = null;
        // Attempt reconnect after 3s
        reconnectTimeoutRef.current = setTimeout(() => connectRef.current(), 3000);
      };

      ws.onerror = (e) => {
        console.error('WebSocket connection error:', e);
        setStatus('error');
        setError('Failed to connect to server');
      };

    } catch (e) {
      setStatus('error');
      setError(e instanceof Error ? e.message : 'Connection failed');
    }
  }, []);

  // Update the ref whenever connect changes
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    // Use setTimeout to avoid synchronous state updates during render
    const timer = setTimeout(() => {
      connect();
    }, 0);

    return () => {
      clearTimeout(timer);
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const fetchRows = useCallback((start: number, limit: number) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'get_rows',
        start,
        limit
      }));
    }
  }, []);

  const sortColumn = useCallback((column: string, ascending: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'sort',
        column,
        ascending
      }));
    }
  }, []);

  const applyFilter = useCallback((payload: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'apply_filter',
        filter_payload: payload
      }));
    }
  }, []);

  const analyzeColumn = useCallback((column: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setIsAnalyzing(true);
      setAnalysisData(null); // Clear previous data
      wsRef.current.send(JSON.stringify({
        action: 'analyze',
        column
      }));
    }
  }, []);

  const getColumnStats = useCallback((column: string) => {
    // Check cache first (handled by component, but good to have here too if we want to prevent redundant calls)
    // However, since we don't have access to the latest statsCache in this callback without adding it to dependency array
    // (which would cause re-creation of callback), we rely on the component to check cache.

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const reqId = Math.floor(Math.random() * 1000000);
      console.log(`[useVisiLensSocket] Sending get_stats for: ${column} (req_id: ${reqId})`);
      wsRef.current.send(JSON.stringify({
        action: 'get_stats',
        column,
        req_id: reqId,
        force: false // Use backend cache if available
      }));
    }
  }, []);

  const renameColumn = useCallback((oldName: string, newName: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'rename_col',
        col_id: oldName,
        new_name: newName
      }));
    }
  }, []);

  const setColumnType = useCallback((column: string, type: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'set_col_type',
        col_id: column,
        type: type
      }));
    }
  }, []);

  const subscribeToStats = useCallback((column: string, callback: (stats: ColumnStats) => void) => {
    if (!statsListenersRef.current.has(column)) {
      statsListenersRef.current.set(column, new Set());
    }
    statsListenersRef.current.get(column)!.add(callback);
    return () => {
      const listeners = statsListenersRef.current.get(column);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          statsListenersRef.current.delete(column);
        }
      }
    };
  }, []);

  const getCachedStats = useCallback((column: string) => {
    return statsCacheRef.current.get(column);
  }, []);

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    connect();
  }, [connect]);

  return {
    status,
    error,
    columns,
    rows,
    total,
    isLoading,
    fetchRows,
    sortColumn,
    sortState,
    applyFilter,
    filterState,
    reconnect,
    analyzeColumn,
    analysisData,
    isAnalyzing,
    getColumnStats,
    subscribeToStats,
    getCachedStats,
    renameColumn,
    setColumnType,
  };
}
