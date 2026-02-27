/** StudioToolbar — Mode switcher, project name, model selector, save/export */
import React, { useState } from 'react';
import { useStudio } from '../../context/StudioContext';
import { useAppContext } from '../../context/AppContext';
import type { StudioMode } from '../../types/studio';

const modes: { id: StudioMode; label: string; icon: string }[] = [
  { id: 'chat', label: 'Chat', icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' },
  { id: 'code', label: 'Code', icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4' },
  { id: 'visual', label: 'Visual', icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z' },
];

const StudioToolbar: React.FC = () => {
  const { mode, setMode, project, isDirty, isLoading, saveProject, isStreaming, closeProject } = useStudio();
  const { activeProvider, activeModel } = useAppContext();
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveProject();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="flex items-center justify-between px-3 h-10 flex-shrink-0"
      style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
    >
      {/* Left: Project info + back */}
      <div className="flex items-center gap-2 min-w-0">
        {project && (
          <button
            onClick={closeProject}
            className="p-1 rounded hover:opacity-80 transition-opacity"
            style={{ color: 'var(--t-muted)' }}
            title="Back to projects"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}
        <span className="text-sm font-medium truncate" style={{ color: 'var(--t-text)' }}>
          {project ? project.name : 'Studio'}
        </span>
        {isDirty && (
          <span className="text-xs px-1.5 py-0.5 rounded" style={{ background: 'var(--t-warning)', color: '#000' }}>
            Unsaved
          </span>
        )}
        {isStreaming && (
          <span className="text-xs px-1.5 py-0.5 rounded animate-pulse" style={{ background: 'var(--t-primary)', color: '#fff' }}>
            Generating...
          </span>
        )}
      </div>

      {/* Center: Mode tabs */}
      <div className="flex items-center gap-0.5 rounded-lg p-0.5" style={{ background: 'var(--t-surface2)' }}>
        {modes.map(m => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            className="flex items-center gap-1 px-3 py-1 rounded text-xs font-medium transition-all"
            style={{
              background: mode === m.id ? 'var(--t-primary)' : 'transparent',
              color: mode === m.id ? '#fff' : 'var(--t-muted)',
            }}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d={m.icon} />
            </svg>
            {m.label}
          </button>
        ))}
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Model badge */}
        <span className="text-xs px-2 py-0.5 rounded hidden sm:inline" style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}>
          {activeProvider === 'claude' ? 'Claude' : activeProvider === 'openai' ? 'OpenAI' : 'Gemini'} / {activeModel.split('-').slice(-2).join('-')}
        </span>

        {/* Save button */}
        {project && (
          <button
            onClick={handleSave}
            disabled={!isDirty || saving || isLoading}
            className="flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium transition-colors disabled:opacity-40"
            style={{
              background: isDirty ? 'var(--t-primary)' : 'var(--t-surface2)',
              color: isDirty ? '#fff' : 'var(--t-muted)',
            }}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
            </svg>
            {saving ? 'Saving...' : 'Save'}
          </button>
        )}
      </div>
    </div>
  );
};

export default StudioToolbar;
