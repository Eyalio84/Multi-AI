import React, { useState } from 'react';
import type { GameProject } from '../../types/game';
import * as api from '../../services/apiService';

interface Props {
  game: GameProject;
  onUpdate: () => void;
}

const GameCodeEditor: React.FC<Props> = ({ game, onUpdate }) => {
  const files = game.files || {};
  const fileNames = Object.keys(files).sort();
  const [selectedFile, setSelectedFile] = useState(fileNames[0] || '');
  const [editContent, setEditContent] = useState('');
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const startEdit = (fileName: string) => {
    setSelectedFile(fileName);
    setEditContent(files[fileName] || '');
    setEditing(true);
  };

  const saveEdit = async () => {
    setSaving(true);
    try {
      const updated = { ...files, [selectedFile]: editContent };
      await api.updateGame(game.id, { files: updated, status: 'editing' });
      setEditing(false);
      onUpdate();
    } finally {
      setSaving(false);
    }
  };

  if (fileNames.length === 0) {
    return (
      <div className="flex items-center justify-center h-full" style={{ color: 'var(--t-muted)' }}>
        <div className="text-sm">No files generated yet</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* File selector — horizontal scroll on mobile, sidebar on desktop */}
      <div className="border-b" style={{ borderColor: 'var(--t-border)', background: 'var(--t-surface)' }}>
        <div className="flex items-center justify-between px-2 py-1.5">
          <div className="flex items-center gap-1 overflow-x-auto flex-1 min-w-0" style={{ WebkitOverflowScrolling: 'touch' }}>
            {fileNames.map(f => (
              <button
                key={f}
                onClick={() => startEdit(f)}
                className="flex-shrink-0 px-2 py-1 rounded text-[11px] font-mono"
                style={{
                  background: selectedFile === f ? 'var(--t-primary)' : 'transparent',
                  color: selectedFile === f ? '#fff' : 'var(--t-muted)',
                }}
              >
                {f.replace('js/', '')}
              </button>
            ))}
          </div>
          <div className="flex gap-1 flex-shrink-0 ml-2">
            {editing && (
              <>
                <button
                  onClick={() => setEditing(false)}
                  className="text-[11px] px-2 py-0.5 rounded"
                  style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
                >
                  Cancel
                </button>
                <button
                  onClick={saveEdit}
                  disabled={saving}
                  className="text-[11px] px-2 py-0.5 rounded"
                  style={{ background: 'var(--t-primary)', color: '#fff' }}
                >
                  {saving ? '...' : 'Save'}
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Editor */}
      <textarea
        value={editing ? editContent : (files[selectedFile] || '')}
        onChange={e => setEditContent(e.target.value)}
        readOnly={!editing}
        className="flex-1 p-3 font-mono text-xs resize-none"
        style={{
          background: 'var(--t-bg)',
          color: 'var(--t-text)',
          border: 'none',
          outline: 'none',
        }}
        spellCheck={false}
      />
    </div>
  );
};

export default GameCodeEditor;
