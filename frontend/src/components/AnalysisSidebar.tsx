import { X, BarChart2 } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface AnalysisData {
  name: string;
  count: number;
  percent: number;
}

interface AnalysisSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  columnName: string | null;
  data: AnalysisData[];
  isLoading?: boolean;
}

// Truncate helper to prevent layout breaks (CRITICAL FIX)
const truncate = (text: string | number, length: number = 15): string => {
  const str = String(text);
  if (str.length <= length) return str;
  return str.substring(0, length) + '...';
};

// Format long decimal values to max 10 decimal places
const formatValue = (value: string | number): string => {
  const str = String(value);
  const num = parseFloat(str);
  
  // If it's not a valid number, truncate it
  if (isNaN(num)) return truncate(str, 15);
  
  // If it's an integer, return as-is (but truncate if too long)
  if (Number.isInteger(num)) return truncate(str, 15);
  
  // For decimals, limit to 10 decimal places and remove trailing zeros
  const formatted = num.toFixed(10);
  const result = parseFloat(formatted).toString();
  return truncate(result, 15);
};

// Custom tooltip component with proper styling
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length > 0) {
    const data = payload[0].payload as AnalysisData;
    return (
      <div
        style={{
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '6px',
          padding: '8px 12px',
          fontSize: '12px',
        }}
      >
        <div style={{ color: '#f8fafc', marginBottom: '4px', fontWeight: 500 }}>
          {formatValue(data.name)}
        </div>
        <div style={{ color: '#94a3b8' }}>
          Count: <span style={{ color: '#f8fafc', fontWeight: 600 }}>{data.count}</span>
        </div>
        <div style={{ color: '#94a3b8' }}>
          Percent: <span style={{ color: '#f8fafc', fontWeight: 600 }}>{data.percent}%</span>
        </div>
      </div>
    );
  }
  return null;
};

export function AnalysisSidebar({
  isOpen,
  onClose,
  columnName,
  data,
  isLoading = false,
}: AnalysisSidebarProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-96 border-l border-border bg-sidebar shadow-xl transition-transform duration-300 ease-in-out">
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div>
            <h2 className="text-sm font-semibold text-primary">
              {isLoading ? 'Analyzing...' : `Analysis: ${columnName}`}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-secondary hover:bg-accent/10 hover:text-accent"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-secondary">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
              <span className="text-xs animate-pulse">Calculating distribution...</span>
            </div>
          ) : data.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-secondary">
              <BarChart2 className="h-8 w-8 opacity-20" />
              <p className="text-sm">No data found in this column</p>
            </div>
          ) : (
            <div className="h-[600px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                >
                  <XAxis type="number" hide />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={80}
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    interval={0}
                    tickFormatter={formatValue}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: '#334155', opacity: 0.2 }} />
                  <Bar dataKey="count" barSize={20} radius={[0, 4, 4, 0]}>
                    {data.map((_, index) => (
                      <Cell key={`cell-${index}`} fill="#3b82f6" />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Footer / Legend */}
        {!isLoading && data.length > 0 && (
          <div className="border-t border-border bg-surface/50 px-4 py-3 text-xs text-secondary">
            <div className="flex justify-between font-medium text-primary mb-2">
              <span>Value</span>
              <span>Count (%)</span>
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {data.map((item, i) => (
                <div key={i} className="flex justify-between">
                  <span className="truncate pr-2" title={item.name}>
                    {formatValue(item.name)}
                  </span>
                  <span className="whitespace-nowrap font-mono">
                    {item.count} ({item.percent}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
