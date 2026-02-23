/** StudioMobileLayout — Single-panel mobile layout with bottom tab bar */
import React, { useState } from 'react';
import { useStudio } from '../../context/StudioContext';
import StudioChatPanel from './StudioChatPanel';
import StudioPreviewPanel from './StudioPreviewPanel';
import StudioCodeEditor from './StudioCodeEditor';
import StudioFilesPanel from './StudioFilesPanel';
import StudioVisualMode from './StudioVisualMode';

type MobileTab = 'chat' | 'preview' | 'code' | 'visual' | 'files';

interface TabDef {
  id: MobileTab;
  label: string;
  icon: string;
}

const TABS: TabDef[] = [
  {
    id: 'chat',
    label: 'Chat',
    icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  },
  {
    id: 'preview',
    label: 'Preview',
    icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z',
  },
  {
    id: 'code',
    label: 'Code',
    icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
  },
  {
    id: 'visual',
    label: 'Visual',
    icon: 'M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z',
  },
  {
    id: 'files',
    label: 'Files',
    icon: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
  },
];

const StudioMobileLayout: React.FC = () => {
  const { mode, setMode, isStreaming, files } = useStudio();
  // Map the global mode to a mobile tab, with extra tabs for preview/files
  const [subTab, setSubTab] = useState<'preview' | 'files' | null>(null);

  const fileCount = Object.keys(files).length;

  // Determine which tab is effectively active
  const activeTab: MobileTab = subTab || mode;

  const handleTabChange = (tab: MobileTab) => {
    if (tab === 'preview' || tab === 'files') {
      // These are mobile-only sub-tabs, not global modes
      setSubTab(tab);
    } else {
      // Chat, Code, Visual are global modes
      setSubTab(null);
      setMode(tab as 'chat' | 'code' | 'visual');
    }
  };

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Main content — only one panel visible at a time */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' && <StudioChatPanel />}
        {activeTab === 'preview' && <StudioPreviewPanel />}
        {activeTab === 'code' && <StudioCodeEditor />}
        {activeTab === 'visual' && <StudioVisualMode />}
        {activeTab === 'files' && <StudioFilesPanel />}
      </div>

      {/* Bottom tab bar */}
      <div
        className="flex items-center justify-around flex-shrink-0 h-14 safe-area-bottom"
        style={{
          background: 'var(--t-surface)',
          borderTop: '1px solid var(--t-border)',
        }}
      >
        {TABS.map(tab => {
          const isActive = tab.id === activeTab;
          const showBadge = tab.id === 'chat' && isStreaming;
          const showCount = tab.id === 'files' && fileCount > 0;

          return (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className="flex flex-col items-center justify-center gap-0.5 flex-1 h-full relative transition-colors"
              style={{ color: isActive ? 'var(--t-primary)' : 'var(--t-muted)' }}
            >
              {/* Active indicator line */}
              {isActive && (
                <div
                  className="absolute top-0 w-8 h-0.5 rounded-b"
                  style={{ background: 'var(--t-primary)' }}
                />
              )}

              {/* Icon */}
              <div className="relative">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={isActive ? 2 : 1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={tab.icon} />
                </svg>

                {/* Streaming badge */}
                {showBadge && (
                  <div
                    className="absolute -top-0.5 -right-1 w-2 h-2 rounded-full animate-pulse"
                    style={{ background: 'var(--t-primary)' }}
                  />
                )}

                {/* File count badge */}
                {showCount && (
                  <div
                    className="absolute -top-1 -right-2 px-1 rounded-full text-center"
                    style={{
                      background: 'var(--t-primary)',
                      color: '#fff',
                      fontSize: 8,
                      lineHeight: '14px',
                      minWidth: 14,
                    }}
                  >
                    {fileCount}
                  </div>
                )}
              </div>

              {/* Label */}
              <span className="text-xs" style={{ fontSize: 10 }}>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default StudioMobileLayout;
