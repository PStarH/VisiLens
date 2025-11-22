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
  data?: any;
  error?: string;
}

interface SortState {
  column: string;
  ascending: boolean;
}

const WS_URL = 'ws://localhost:8000/ws';

export function useVisiLensSocket() {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [error, setError] = useState<string | null>(null);
  const [columns, setColumns] = useState<Column[]>([]);
  const [rows, setRows] = useState<Row[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [sortState, setSortState] = useState<SortState | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Store rows in a map for random access by index
  // This is crucial for virtualization where we might receive chunks out of order
  const rowsMapRef = useRef<Map<number, Row>>(new Map());

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
            return;
          }

          switch (message.action) {
            case 'columns':
              setColumns(message.data.columns);
              break;
            case 'rows': {
              const { rows: newRows, start, total: totalRows, reset } = message.data;
              
              if (reset) {
                rowsMapRef.current.clear();
              }

              setTotal(totalRows);
              
              // Update rows map
              newRows.forEach((row: Row, index: number) => {
                rowsMapRef.current.set(start + index, row);
              });

              // Convert map to array (sparse)
              // We create an array of size 'total' and fill it with known rows
              const sparseRows = new Array(totalRows);
              rowsMapRef.current.forEach((row, index) => {
                if (index < totalRows) {
                  sparseRows[index] = row;
                }
              });
              setRows(sparseRows);
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
              break;
            }
            case 'filtered': {
              // Clear rows map - will be refilled with filtered data
              rowsMapRef.current.clear();
              setTotal(message.data.total);
              break;
            }
            case 'reset': {
              // Clear sort state and rows map
              setSortState(null);
              rowsMapRef.current.clear();
              setTotal(message.data.total);
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
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
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

  useEffect(() => {
    connect();
    return () => {
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
    reconnect
  };
}
