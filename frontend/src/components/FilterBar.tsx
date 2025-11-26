import React, { useState } from 'react';
import { Filter, X, Play, Code, Layers, ChevronDown, Plus, Trash2 } from 'lucide-react';
import clsx from 'clsx';
import { v4 as uuidv4 } from 'uuid';

interface Column {
  name: string;
  type: string;
}

export type FilterPayload = 
  | { type: 'basic'; conditions: { id: string; column: string; operator: string; value: string }[] }
  | { type: 'expression'; expression: string };

interface FilterBarProps {
  columns: Column[];
  onApplyFilter: (filter: FilterPayload) => void;
  onResetFilter: () => void;
}

interface FilterRow {
  id: string;
  column: string;
  operator: string;
  value: string;
}

const FilterBarComponent = ({ columns, onApplyFilter, onResetFilter }: FilterBarProps) => {
  const [mode, setMode] = useState<'basic' | 'advanced'>('basic');
  
  // Basic Mode State
  const [filters, setFilters] = useState<FilterRow[]>([
    { id: uuidv4(), column: '', operator: '', value: '' }
  ]);

  // Advanced Mode State
  const [expression, setExpression] = useState<string>('');

  const handleAddFilter = () => {
    setFilters([...filters, { id: uuidv4(), column: '', operator: '', value: '' }]);
  };

  const handleRemoveFilter = (id: string) => {
    if (filters.length === 1) {
      // If it's the last one, just clear it
      setFilters([{ id: uuidv4(), column: '', operator: '', value: '' }]);
    } else {
      setFilters(filters.filter(f => f.id !== id));
    }
  };

  const updateFilter = (id: string, field: keyof FilterRow, value: string) => {
    setFilters(filters.map(f => {
      if (f.id === id) {
        const updated = { ...f, [field]: value };
        // Reset operator and value if column changes
        if (field === 'column') {
          updated.operator = '';
          updated.value = '';
        }
        return updated;
      }
      return f;
    }));
  };

  // Determine operators based on column type
  const getOperators = (colName: string) => {
    if (!colName) return [];
    
    const col = columns.find(c => c.name === colName);
    if (!col) return [];

    const isNumeric = ['float', 'integer', 'currency', 'int'].includes(col.type);

    if (isNumeric) {
      return [
        { label: 'Greater Than (>)', value: 'gt' },
        { label: 'Less Than (<)', value: 'lt' },
        { label: 'Equals (=)', value: 'eq' },
        { label: 'Not Equals (!=)', value: 'neq' },
      ];
    } else {
      return [
        { label: 'Contains', value: 'contains' },
        { label: 'Equals', value: 'eq' },
        { label: 'Regex Match (~)', value: 'regex' },
        { label: 'Is Empty', value: 'is_empty' },
      ];
    }
  };

  const handleApply = () => {
    console.log('[FilterBar] handleApply triggered', { mode, filters, expression });

    if (mode === 'basic') {
      // validate filters
      const validFilters = filters.filter(f => f.column && f.operator && (f.operator === 'is_empty' || f.value !== ''));
      
      if (validFilters.length === 0) {
        console.warn('[FilterBar] No valid filters found');
        return;
      }

      const payload: FilterPayload = {
        type: 'basic',
        conditions: validFilters
      };
      console.log('[FilterBar] Applying basic filter:', payload);
      onApplyFilter(payload);
    } else {
      if (!expression.trim()) {
        console.warn('[FilterBar] Advanced mode missing expression');
        return;
      }
      const payload: FilterPayload = {
        type: 'expression',
        expression: expression.trim()
      };
      console.log('[FilterBar] Applying expression filter:', payload);
      onApplyFilter(payload);
    }
  };

  const handleClear = () => {
    if (mode === 'basic') {
      setFilters([{ id: uuidv4(), column: '', operator: '', value: '' }]);
    } else {
      setExpression('');
    }
    onResetFilter();
  };

  return (
    <div className="flex flex-col w-full border-b border-border bg-surface shadow-sm">
      {/* Header / Mode Switcher */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/50">
        <div className="flex items-center gap-2 text-secondary">
          <Filter className="h-3.5 w-3.5" />
          <span className="text-[11px] font-bold uppercase tracking-widest">Power Filter</span>
        </div>

        <div className="flex bg-canvas rounded-lg p-0.5 border border-border/50">
          <button
            onClick={() => setMode('basic')}
            className={clsx(
              "flex items-center gap-1.5 px-3 py-1 rounded-md text-[10px] font-medium transition-all duration-200",
              mode === 'basic' 
                ? "bg-surface text-primary shadow-sm border border-border/50" 
                : "text-secondary hover:text-primary hover:bg-surface/50"
            )}
          >
            <Layers className="h-3 w-3" /> Basic
          </button>
          <button
            onClick={() => setMode('advanced')}
            className={clsx(
              "flex items-center gap-1.5 px-3 py-1 rounded-md text-[10px] font-medium transition-all duration-200",
              mode === 'advanced' 
                ? "bg-surface text-accent shadow-sm border border-border/50" 
                : "text-secondary hover:text-primary hover:bg-surface/50"
            )}
          >
            <Code className="h-3 w-3" /> Advanced
          </button>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="flex flex-col gap-2 px-4 py-3 bg-surface/50">
        {mode === 'basic' ? (
          <div className="flex flex-col gap-2 w-full">
            {filters.map((filter) => {
              const operators = getOperators(filter.column);
              const showInput = filter.operator !== 'is_empty';

              return (
                <div key={filter.id} className="flex items-center gap-2 w-full animate-in fade-in slide-in-from-top-1 duration-200">
                  {/* Column Selector */}
                  <div className="relative group">
                    <select
                      value={filter.column}
                      onChange={(e) => updateFilter(filter.id, 'column', e.target.value)}
                      className="h-8 pl-3 pr-8 rounded-md border border-border bg-canvas text-xs text-primary focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none appearance-none min-w-[140px] cursor-pointer hover:border-border/80 transition-colors"
                    >
                      <option value="" disabled>Select Column</option>
                      {columns.map((col) => (
                        <option key={col.name} value={col.name}>
                          {col.name}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-secondary pointer-events-none group-hover:text-primary transition-colors" />
                  </div>

                  {/* Operator Selector */}
                  <div className="relative group">
                    <select
                      value={filter.operator}
                      onChange={(e) => updateFilter(filter.id, 'operator', e.target.value)}
                      disabled={!filter.column}
                      className="h-8 pl-3 pr-8 rounded-md border border-border bg-canvas text-xs text-primary focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none appearance-none w-[140px] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer hover:border-border/80 transition-colors"
                    >
                      <option value="" disabled>Operator</option>
                      {operators.map((op) => (
                        <option key={op.value} value={op.value}>
                          {op.label}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-secondary pointer-events-none group-hover:text-primary transition-colors" />
                  </div>

                  {/* Value Input */}
                  {showInput && (
                    <input
                      type="text"
                      value={filter.value}
                      onChange={(e) => updateFilter(filter.id, 'value', e.target.value)}
                      placeholder="Enter value..."
                      disabled={!filter.operator}
                      onKeyDown={(e) => e.key === 'Enter' && handleApply()}
                      className="h-8 w-64 rounded-md border border-border bg-canvas px-3 text-xs text-primary placeholder-secondary/50 focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none disabled:opacity-50 transition-all"
                    />
                  )}

                  {/* Remove Button */}
                  <button
                    onClick={() => handleRemoveFilter(filter.id)}
                    className="p-1.5 text-secondary hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
                    title="Remove filter"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })}

            {/* Add Filter Button */}
            <button
              onClick={handleAddFilter}
              className="flex items-center gap-1.5 text-xs font-medium text-accent hover:text-accent/80 w-fit mt-1 px-1"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Condition
            </button>
          </div>
        ) : (
          /* Advanced Mode Input */
          <div className="flex-1 relative group">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 p-1 rounded bg-border/30">
              <Code className="h-3.5 w-3.5 text-accent" />
            </div>
            <input
              type="text"
              value={expression}
              onChange={(e) => setExpression(e.target.value)}
              placeholder="Enter Python expression (e.g. len(Name) > 5 and Status == 'Error')"
              onKeyDown={(e) => e.key === 'Enter' && handleApply()}
              className="h-9 w-full rounded-md border border-border bg-canvas pl-10 pr-4 text-xs font-mono text-accent placeholder-secondary/40 focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none transition-all"
            />
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-2 pt-3 mt-2 border-t border-border/50">
          <button
            onClick={handleClear}
            className="flex h-8 items-center gap-1.5 rounded-md px-3 text-xs font-medium text-secondary hover:text-primary hover:bg-white/5 transition-colors"
          >
            <X className="h-3.5 w-3.5" />
            Clear All
          </button>
          
          <button
            onClick={handleApply}
            disabled={mode === 'basic' ? filters.every(f => !f.column || !f.operator) : !expression.trim()}
            className="flex h-8 items-center gap-1.5 rounded-md bg-accent px-4 text-xs font-medium text-white shadow-lg shadow-accent/20 hover:bg-blue-500 hover:shadow-accent/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none transition-all active:scale-95"
          >
            <Play className="h-3 w-3 fill-current" />
            Apply Filter
          </button>
        </div>
      </div>
    </div>
  );
};

// OPTIMIZATION: Wrap with React.memo to prevent unnecessary re-renders
// when parent (App) updates but FilterBar props haven't changed
export const FilterBar = React.memo(FilterBarComponent);
FilterBar.displayName = 'FilterBar';
