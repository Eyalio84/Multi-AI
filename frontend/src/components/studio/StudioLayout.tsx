/** StudioLayout — Resizable 3-panel CSS grid with drag handles */
import React, { useState, useCallback, useRef } from 'react';

interface Props {
  left: React.ReactNode;
  center: React.ReactNode;
  right: React.ReactNode;
  showRight?: boolean;
}

const StudioLayout: React.FC<Props> = ({ left, center, right, showRight = true }) => {
  const [leftWidth, setLeftWidth] = useState(340);
  const [rightWidth, setRightWidth] = useState(340);
  const containerRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef<'left' | 'right' | null>(null);

  const handleMouseDown = useCallback((side: 'left' | 'right') => {
    draggingRef.current = side;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current || !draggingRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();

      if (draggingRef.current === 'left') {
        const w = Math.max(240, Math.min(600, e.clientX - rect.left));
        setLeftWidth(w);
      } else {
        const w = Math.max(240, Math.min(600, rect.right - e.clientX));
        setRightWidth(w);
      }
    };

    const handleMouseUp = () => {
      draggingRef.current = null;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, []);

  return (
    <div ref={containerRef} className="flex h-full overflow-hidden" style={{ background: 'var(--t-bg)' }}>
      {/* Left panel */}
      <div className="flex-shrink-0 overflow-hidden flex flex-col" style={{ width: leftWidth, borderRight: '1px solid var(--t-border)' }}>
        {left}
      </div>

      {/* Left drag handle */}
      <div
        className="flex-shrink-0 hover:opacity-100 transition-opacity"
        style={{
          width: 4,
          cursor: 'col-resize',
          background: 'var(--t-border)',
          opacity: 0.5,
        }}
        onMouseDown={() => handleMouseDown('left')}
      />

      {/* Center panel */}
      <div className="flex-1 min-w-0 overflow-hidden flex flex-col">
        {center}
      </div>

      {/* Right panel */}
      {showRight && (
        <>
          <div
            className="flex-shrink-0 hover:opacity-100 transition-opacity"
            style={{
              width: 4,
              cursor: 'col-resize',
              background: 'var(--t-border)',
              opacity: 0.5,
            }}
            onMouseDown={() => handleMouseDown('right')}
          />
          <div className="flex-shrink-0 overflow-hidden flex flex-col" style={{ width: rightWidth, borderLeft: '1px solid var(--t-border)' }}>
            {right}
          </div>
        </>
      )}
    </div>
  );
};

export default StudioLayout;
