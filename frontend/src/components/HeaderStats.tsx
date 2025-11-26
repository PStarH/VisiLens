import React, { useState, useRef, useEffect, type ReactNode } from 'react';
import { Activity, Hash, Type, AlertTriangle } from 'lucide-react';

interface StatsData {
  scanned_rows: number;
  total_rows?: number;
  is_sample?: boolean;
  null_count: number;
  null_percent: number;
  unique_count: number;
  type: string;
  min?: number;
  max?: number;
  mean?: number;
}

interface HeaderStatsProps {
  columnName: string;
  columnType: string;
  onFetchStats: (col: string) => void;
  registerStatsListener: (col: string, cb: (s: StatsData) => void) => () => void;
  getCachedStats: (col: string) => StatsData | undefined;
  children: ReactNode;
  disabled?: boolean;
}

export const HeaderStats = React.memo(function HeaderStats({
  columnName,
  columnType,
  onFetchStats,
  registerStatsListener,
  getCachedStats,
  children,
  disabled,
}: HeaderStatsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [stats, setStats] = useState<StatsData | null>(() => getCachedStats(columnName) || null);
  
  
  // Use useRef for timer to avoid re-renders
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const unsubscribe = registerStatsListener(columnName, (newStats) => {
      setStats(newStats);
    });
    return () => {
      unsubscribe();
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [columnName, registerStatsListener]);

  const handleMouseEnter = () => {
    if (disabled) return;
    
    // OPTIMIZATION: Check cache first - if hit, show immediately without network request
    const cached = getCachedStats(columnName);
    if (cached) {
      setStats(cached);
      setIsOpen(true);
      return; // Early return prevents any WebSocket request
    }
    
    // CACHE MISS: Clear any existing timer first
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    
    // Set new timer with 500ms debounce for cache miss
    timerRef.current = setTimeout(() => {
      setIsOpen(true);
      console.log(`[HeaderStats] Cache miss - Fetching stats for: ${columnName}`);
      onFetchStats(columnName);
    }, 500);
  };

  const handleMouseLeave = () => {
    // Clear timer on mouse leave
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    setIsOpen(false);
  };

  // Calculate derived values
  const nullPercent = stats ? stats.null_percent : 0;
  const isHighNulls = nullPercent > 10;
  const isLoading = isOpen && !stats;

  const formatNumber = (num: number | undefined) => {
    if (num === undefined) return '-';
    if (Number.isInteger(num)) return num.toString();
    // Use scientific notation for very large or very small numbers
    if (Math.abs(num) > 100000 || (Math.abs(num) < 0.001 && num !== 0)) {
      return num.toExponential(2);
    }
    // Round to 4 decimal places and strip trailing zeros
    return parseFloat(num.toFixed(4)).toString();
  };

  return (
    <div
      className="relative flex h-full w-full items-center"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 z-50 w-64 rounded-lg border border-slate-700 bg-slate-800 p-4 shadow-xl text-xs animate-in fade-in zoom-in-95 duration-200">
          {/* Header */}
          <div className="mb-3 flex items-center justify-between border-b border-slate-700 pb-2">
            <span className="font-semibold text-slate-200">{columnName}</span>
            <span className="rounded bg-slate-700 px-1.5 py-0.5 text-[10px] font-medium text-slate-300 uppercase">
              {stats?.type || columnType}
            </span>
          </div>

          {isLoading ? (
            <div className="space-y-2.5">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded bg-slate-700/50 animate-pulse" />
                <div className="space-y-1 flex-1">
                  <div className="h-2 w-3/4 rounded bg-slate-700/50 animate-pulse" />
                  <div className="h-2 w-1/2 rounded bg-slate-700/50 animate-pulse" />
                </div>
              </div>
              <div className="h-2 w-full rounded bg-slate-700/50 animate-pulse" />
            </div>
          ) : stats ? (
            <div className="grid grid-cols-2 gap-3">
              {/* Nulls */}
              <div className="flex flex-col gap-1">
                <span className="flex items-center gap-1 text-[10px] text-slate-400 uppercase tracking-wider">
                  <AlertTriangle className="h-3 w-3" /> Nulls
                </span>
                <span
                  className={`font-mono font-medium ${
                    isHighNulls ? 'text-red-400' : 'text-slate-200'
                  }`}
                >
                  {nullPercent}% <span className="text-slate-500">({stats.null_count})</span>
                </span>
              </div>

              {/* Unique */}
              <div className="flex flex-col gap-1">
                <span className="flex items-center gap-1 text-[10px] text-slate-400 uppercase tracking-wider">
                  <Hash className="h-3 w-3" /> Unique
                </span>
                <span className="font-mono font-medium text-slate-200">
                  ~{stats.unique_count}
                </span>
              </div>

              {/* Numeric Stats */}
              {stats.type === 'float' || stats.type === 'integer' || stats.type === 'numeric' ? (
                <>
                  <div className="col-span-2 flex flex-col gap-1 border-t border-slate-700/50 pt-2">
                    <span className="flex items-center gap-1 text-[10px] text-slate-400 uppercase tracking-wider">
                      <Activity className="h-3 w-3" /> Range
                    </span>
                    <div className="flex justify-between font-mono text-slate-200 text-xs">
                      <span className="truncate max-w-[45%]" title={stats.min?.toString()}>
                        {formatNumber(stats.min)}
                      </span>
                      <span className="text-slate-500">-</span>
                      <span className="truncate max-w-[45%] text-right" title={stats.max?.toString()}>
                        {formatNumber(stats.max)}
                      </span>
                    </div>
                  </div>
                  <div className="col-span-2 flex justify-between border-t border-slate-700/50 pt-2">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider">Mean</span>
                    <span className="font-mono text-slate-200 truncate max-w-[60%] text-right" title={stats.mean?.toString()}>
                      {formatNumber(stats.mean)}
                    </span>
                  </div>
                </>
              ) : (
                <div className="col-span-2 border-t border-slate-700/50 pt-2">
                  <span className="flex items-center gap-1 text-[10px] text-slate-400 uppercase tracking-wider">
                    <Type className="h-3 w-3" /> String Data
                  </span>
                </div>
              )}
              
              <div className="col-span-2 mt-1 text-[10px] text-slate-500 text-right italic">
                Scanned {stats.scanned_rows} rows {stats.is_sample && '(Sampled)'}
              </div>
            </div>
          ) : (
            <div className="text-center text-slate-500 py-2">No data available</div>
          )}
        </div>
      )}
    </div>
  );
});
