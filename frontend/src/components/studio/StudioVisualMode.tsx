/** StudioVisualMode — Visual layout with preview, selection overlay, and inspector */
import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useStudio } from '../../context/StudioContext';
import StudioPreviewPanel from './StudioPreviewPanel';
import StudioElementInspector from './StudioElementInspector';
import StudioSelectionOverlay from './StudioSelectionOverlay';
import StudioQuickActions from './StudioQuickActions';
import StudioComponentTree from './StudioComponentTree';
import type { StudioSelection } from '../../types/studio';

type SidebarTab = 'inspector' | 'tree';

const StudioVisualMode: React.FC = () => {
  const { selectedElement, setSelectedElement, sendMessage, isStreaming } = useStudio();
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>('inspector');
  const [chatInput, setChatInput] = useState('');
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const draggingRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Listen for postMessage from Sandpack preview iframe
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      if (event.data?.type === 'studio-element-select') {
        const data = event.data;
        const selection: StudioSelection = {
          componentName: data.componentName || 'Unknown',
          elementTag: data.elementTag || 'div',
          filePath: data.filePath || '',
          lineNumber: data.lineNumber,
          props: data.props || {},
          styles: data.styles || {},
          text: data.text || '',
        };
        setSelectedElement(selection);
        setSidebarTab('inspector');
      }

      if (event.data?.type === 'studio-element-hover') {
        // Could be used for hover preview - currently just logging
      }
    };

    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, [setSelectedElement]);

  // Drag handle for sidebar resize
  const handleMouseDown = useCallback(() => {
    draggingRef.current = true;

    const handleMouseMove = (e: MouseEvent) => {
      if (!draggingRef.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const w = Math.max(200, Math.min(400, rect.right - e.clientX));
      setSidebarWidth(w);
    };

    const handleMouseUp = () => {
      draggingRef.current = false;
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

  // Targeted chat for selected element
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = chatInput.trim();
    if (!text || isStreaming) return;

    let prompt = text;
    if (selectedElement) {
      prompt = `[Visual Mode - Targeting ${selectedElement.componentName} <${selectedElement.elementTag}> in ${selectedElement.filePath}${selectedElement.lineNumber ? ` line ${selectedElement.lineNumber}` : ''}]\n\n${text}`;
    }

    setChatInput('');
    await sendMessage(prompt);
  };

  return (
    <div ref={containerRef} className="flex h-full overflow-hidden" style={{ background: 'var(--t-bg)' }}>
      {/* Preview area with overlay */}
      <div className="flex-1 min-w-0 flex flex-col relative">
        {/* Header */}
        <div
          className="flex items-center justify-between px-3 h-8 flex-shrink-0"
          style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
        >
          <span className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>
            Visual Editor
          </span>
          {selectedElement && (
            <span className="text-xs" style={{ color: 'var(--t-primary)' }}>
              Selected: &lt;{selectedElement.elementTag}&gt; in {selectedElement.componentName}
            </span>
          )}
        </div>

        {/* Preview */}
        <div className="flex-1 relative overflow-hidden">
          <StudioPreviewPanel />
          <StudioSelectionOverlay />
        </div>

        {/* Quick actions bar */}
        {selectedElement && <StudioQuickActions />}

        {/* Chat input for targeted changes */}
        <form
          onSubmit={handleChatSubmit}
          className="flex-shrink-0 px-3 py-2"
          style={{ borderTop: '1px solid var(--t-border)' }}
        >
          <div className="flex gap-2 items-center">
            <input
              type="text"
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              placeholder={
                selectedElement
                  ? `Change ${selectedElement.componentName}...`
                  : 'Select an element, then describe changes...'
              }
              className="flex-1 px-3 py-1.5 rounded text-xs outline-none"
              style={{
                background: 'var(--t-surface)',
                color: 'var(--t-text)',
                border: '1px solid var(--t-border)',
                fontFamily: 'var(--t-font)',
              }}
              disabled={isStreaming}
            />
            <button
              type="submit"
              disabled={!chatInput.trim() || isStreaming}
              className="px-3 py-1.5 rounded text-xs font-medium transition-colors disabled:opacity-40"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
            >
              Apply
            </button>
          </div>
        </form>
      </div>

      {/* Resize handle */}
      <div
        className="flex-shrink-0 hover:opacity-100 transition-opacity"
        style={{
          width: 4,
          cursor: 'col-resize',
          background: 'var(--t-border)',
          opacity: 0.5,
        }}
        onMouseDown={handleMouseDown}
      />

      {/* Sidebar */}
      <div
        className="flex-shrink-0 flex flex-col overflow-hidden"
        style={{ width: sidebarWidth, borderLeft: '1px solid var(--t-border)' }}
      >
        {/* Sidebar tabs */}
        <div
          className="flex items-center h-8 flex-shrink-0 px-1"
          style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
        >
          {(['inspector', 'tree'] as SidebarTab[]).map(tab => (
            <button
              key={tab}
              onClick={() => setSidebarTab(tab)}
              className="px-2.5 py-1 rounded text-xs capitalize transition-colors"
              style={{
                background: sidebarTab === tab ? 'var(--t-primary)' : 'transparent',
                color: sidebarTab === tab ? '#fff' : 'var(--t-muted)',
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Sidebar content */}
        <div className="flex-1 overflow-y-auto">
          {sidebarTab === 'inspector' && <StudioElementInspector />}
          {sidebarTab === 'tree' && <StudioComponentTree />}
        </div>
      </div>
    </div>
  );
};

export default StudioVisualMode;
