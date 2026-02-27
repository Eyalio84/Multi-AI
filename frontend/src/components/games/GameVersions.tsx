import React, { useState, useEffect } from 'react';
import * as api from '../../services/apiService';
import type { GameProject, GameVersion } from '../../types/game';

interface Props {
  game: GameProject;
  onRestore: () => void;
}

const GameVersions: React.FC<Props> = ({ game, onRestore }) => {
  const [versions, setVersions] = useState<GameVersion[]>([]);
  const [saving, setSaving] = useState(false);

  const loadVersions = () => {
    api.listGameVersions(game.id).then(setVersions);
  };

  useEffect(() => { loadVersions(); }, [game.id]);

  const save = async () => {
    setSaving(true);
    try {
      await api.saveGameVersion(game.id);
      loadVersions();
    } finally {
      setSaving(false);
    }
  };

  const restore = async (vn: number) => {
    await api.restoreGameVersion(game.id, vn);
    onRestore();
  };

  const download = async () => {
    const blob = await api.exportGame(game.id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${game.name.replace(/\s+/g, '_').toLowerCase()}.zip`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full overflow-y-auto p-3">
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <button
          onClick={save}
          disabled={saving}
          className="px-3 py-1.5 rounded text-sm font-medium"
          style={{ background: 'var(--t-primary)', color: '#fff' }}
        >
          {saving ? 'Saving...' : 'Save Version'}
        </button>
        <button
          onClick={download}
          className="px-3 py-1.5 rounded text-sm"
          style={{ background: 'var(--t-surface)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
        >
          Export ZIP
        </button>
      </div>

      <div className="text-xs font-medium mb-2" style={{ color: 'var(--t-muted)' }}>
        Version History ({versions.length})
      </div>

      <div className="space-y-2">
        {versions.map(v => (
          <div
            key={v.id}
            className="flex items-center justify-between p-3 rounded"
            style={{ background: 'var(--t-surface)' }}
          >
            <div>
              <div className="text-sm font-medium" style={{ color: 'var(--t-text)' }}>
                Version {v.version_number}
              </div>
              <div className="text-xs" style={{ color: 'var(--t-muted)' }}>
                {v.message || new Date(v.timestamp).toLocaleString()}
              </div>
            </div>
            <button
              onClick={() => restore(v.version_number)}
              className="text-xs px-2 py-1 rounded"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}
            >
              Restore
            </button>
          </div>
        ))}
        {versions.length === 0 && (
          <div className="text-sm text-center py-4" style={{ color: 'var(--t-muted)' }}>
            No versions saved yet
          </div>
        )}
      </div>
    </div>
  );
};

export default GameVersions;
