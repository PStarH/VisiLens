import { useEffect, useRef, useState } from 'react';

interface ContextMenuProps {
  x: number;
  y: number;
  colName: string;
  currentType: string;
  onClose: () => void;
  onRename: () => void;
  onTypeChange: (type: string) => void;
}

export function ContextMenu({ x, y, colName, currentType, onClose, onRename, onTypeChange }: ContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [showTypeSubmenu, setShowTypeSubmenu] = useState(false);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        onClose();
      }
    }
    // Use mousedown to capture click before it triggers other things
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  return (
    <div
      ref={ref}
      className="fixed z-50 w-48 rounded-md border border-border bg-sidebar p-1 text-primary shadow-xl animate-in fade-in-80 zoom-in-95"
      style={{ top: y, left: x }}
      onContextMenu={(e) => e.preventDefault()}
    >
      <div className="px-2 py-1.5 text-xs font-semibold text-secondary">
        Column: {colName}
      </div>
      <div className="h-px bg-border my-1" />
      
      <button
        onClick={() => { onRename(); onClose(); }}
        className="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent/20 hover:text-accent text-left"
      >
        Rename
      </button>
      
      <div 
        className="relative"
        onMouseEnter={() => setShowTypeSubmenu(true)}
        onMouseLeave={() => setShowTypeSubmenu(false)}
      >
        <button
          className="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent/20 hover:text-accent justify-between text-left"
        >
          Change Type
          <span className="ml-auto text-[10px] text-secondary">▶</span>
        </button>
        {/* Submenu */}
        {showTypeSubmenu && (
          <div className="absolute left-full top-0 ml-1 w-32 rounded-md border border-border bg-sidebar p-1 shadow-xl">
             {['int', 'float', 'string', 'date'].map(t => (
               <button
                  key={t}
                  onClick={() => { onTypeChange(t); onClose(); }}
                  className="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent/20 hover:text-accent text-left"
               >
                 <span className="flex-1">{t}</span>
                 {currentType === t && <span className="text-accent">✓</span>}
               </button>
             ))}
          </div>
        )}
      </div>
    </div>
  );
}
