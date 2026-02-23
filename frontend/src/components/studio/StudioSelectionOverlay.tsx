/** StudioSelectionOverlay — Highlight hovered/selected elements over the preview */
import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useStudio } from '../../context/StudioContext';
import type { StudioSelection } from '../../types/studio';

interface OverlayRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

interface HoverInfo {
  rect: OverlayRect;
  tag: string;
  name: string;
}

const StudioSelectionOverlay: React.FC = () => {
  const { selectedElement, setSelectedElement, mode } = useStudio();
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);
  const [selectionRect, setSelectionRect] = useState<OverlayRect | null>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  // Listen for messages from the Sandpack preview iframe
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      if (event.data?.type === 'studio-element-hover') {
        const { rect, tag, name } = event.data;
        if (rect) {
          setHoverInfo({ rect, tag: tag || 'div', name: name || '' });
        } else {
          setHoverInfo(null);
        }
      }

      if (event.data?.type === 'studio-element-select') {
        const { rect } = event.data;
        if (rect) {
          setSelectionRect(rect);
        }
      }

      if (event.data?.type === 'studio-element-deselect') {
        setSelectionRect(null);
        setHoverInfo(null);
      }
    };

    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  // Clear overlay when mode changes away from visual
  useEffect(() => {
    if (mode !== 'visual') {
      setHoverInfo(null);
      setSelectionRect(null);
    }
  }, [mode]);

  // Clear selection rect when selectedElement is cleared
  useEffect(() => {
    if (!selectedElement) {
      setSelectionRect(null);
    }
  }, [selectedElement]);

  // Handle click on overlay to deselect
  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    // Only deselect if clicking the overlay background, not a highlighted region
    if (e.target === overlayRef.current) {
      setSelectedElement(null);
      setSelectionRect(null);
    }
  }, [setSelectedElement]);

  if (mode !== 'visual') return null;

  return (
    <div
      ref={overlayRef}
      className="absolute inset-0 pointer-events-none"
      style={{ zIndex: 10 }}
    >
      {/* Hover highlight - blue dashed border */}
      {hoverInfo && (
        <div
          className="absolute transition-all duration-75"
          style={{
            top: hoverInfo.rect.top,
            left: hoverInfo.rect.left,
            width: hoverInfo.rect.width,
            height: hoverInfo.rect.height,
            border: '1.5px dashed var(--t-primary)',
            background: 'rgba(14, 165, 233, 0.05)',
            pointerEvents: 'none',
          }}
        >
          {/* Tooltip */}
          <div
            className="absolute px-1.5 py-0.5 rounded text-xs whitespace-nowrap"
            style={{
              top: -22,
              left: 0,
              background: 'var(--t-primary)',
              color: '#fff',
              fontSize: 10,
              lineHeight: '1.4',
              pointerEvents: 'none',
            }}
          >
            &lt;{hoverInfo.tag}&gt;{hoverInfo.name ? ` ${hoverInfo.name}` : ''}
          </div>
        </div>
      )}

      {/* Selection highlight - solid blue border */}
      {selectionRect && (
        <div
          className="absolute"
          style={{
            top: selectionRect.top,
            left: selectionRect.left,
            width: selectionRect.width,
            height: selectionRect.height,
            border: '2px solid var(--t-primary)',
            background: 'rgba(14, 165, 233, 0.08)',
            pointerEvents: 'none',
            boxShadow: '0 0 0 1px rgba(14, 165, 233, 0.3)',
          }}
        >
          {/* Corner handles */}
          {['top-left', 'top-right', 'bottom-left', 'bottom-right'].map(corner => {
            const [v, h] = corner.split('-');
            return (
              <div
                key={corner}
                className="absolute w-2 h-2 rounded-full"
                style={{
                  [v]: -4,
                  [h]: -4,
                  background: 'var(--t-primary)',
                  border: '1.5px solid #fff',
                  pointerEvents: 'none',
                }}
              />
            );
          })}

          {/* Element info label */}
          {selectedElement && (
            <div
              className="absolute px-1.5 py-0.5 rounded text-xs whitespace-nowrap"
              style={{
                bottom: -22,
                left: 0,
                background: 'var(--t-primary)',
                color: '#fff',
                fontSize: 10,
                lineHeight: '1.4',
                pointerEvents: 'none',
              }}
            >
              {selectedElement.componentName} &middot; &lt;{selectedElement.elementTag}&gt;
              {selectedElement.filePath && ` &middot; ${selectedElement.filePath.split('/').pop()}`}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StudioSelectionOverlay;
