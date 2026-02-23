/** StudioEditorTabs — Open file tabs with close/dirty indicators */
import React from 'react';
import { useStudio } from '../../context/StudioContext';

const StudioEditorTabs: React.FC = () => {
  const { openTabs, activeTab, setActiveTab, closeTab } = useStudio();

  if (openTabs.length === 0) {
    return (
      <div
        className="h-8 flex-shrink-0 flex items-center px-3"
        style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
      >
        <span className="text-xs" style={{ color: 'var(--t-muted)' }}>No files open</span>
      </div>
    );
  }

  const getFileName = (path: string): string => {
    const parts = path.split('/');
    return parts[parts.length - 1] || path;
  };

  const getFileColor = (name: string): string => {
    const ext = name.split('.').pop()?.toLowerCase() || '';
    const map: Record<string, string> = {
      tsx: '#3b82f6', ts: '#3b82f6', jsx: '#f59e0b', js: '#f59e0b',
      css: '#8b5cf6', html: '#ef4444', json: '#22c55e', md: '#6b7280',
      py: '#22d3ee', sql: '#f97316',
    };
    return map[ext] || 'var(--t-muted)';
  };

  return (
    <div
      className="flex items-center h-8 flex-shrink-0 overflow-x-auto"
      style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
    >
      {openTabs.map(tab => {
        const isActive = tab.path === activeTab;
        const fileName = getFileName(tab.path);
        const dotColor = getFileColor(fileName);

        return (
          <div
            key={tab.path}
            className="flex items-center gap-1.5 px-3 h-full cursor-pointer group flex-shrink-0"
            style={{
              background: isActive ? 'var(--t-bg)' : 'transparent',
              borderRight: '1px solid var(--t-border)',
              borderBottom: isActive ? '2px solid var(--t-primary)' : '2px solid transparent',
            }}
            onClick={() => setActiveTab(tab.path)}
          >
            {/* File color dot */}
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: dotColor }} />

            {/* File name */}
            <span
              className="text-xs truncate max-w-[120px]"
              style={{ color: isActive ? 'var(--t-text)' : 'var(--t-muted)' }}
            >
              {fileName}
            </span>

            {/* Dirty indicator */}
            {tab.isDirty && (
              <div
                className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                style={{ background: 'var(--t-warning)' }}
                title="Unsaved changes"
              />
            )}

            {/* Close button */}
            <button
              onClick={(e) => { e.stopPropagation(); closeTab(tab.path); }}
              className="opacity-0 group-hover:opacity-60 hover:opacity-100 p-0.5 rounded transition-opacity flex-shrink-0"
              style={{ color: 'var(--t-muted)' }}
              title="Close tab"
            >
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        );
      })}
    </div>
  );
};

export default StudioEditorTabs;
