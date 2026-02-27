import React from 'react';
import type { GameProject } from '../../types/game';

const STATUS_COLORS: Record<string, string> = {
  draft: '#6b7280',
  interviewing: '#f59e0b',
  generating: '#3b82f6',
  playable: '#10b981',
  editing: '#8b5cf6',
};

interface Props {
  games: GameProject[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  loading: boolean;
}

const GameList: React.FC<Props> = ({ games, selectedId, onSelect, onCreate, onDelete, loading }) => {
  if (loading) {
    return (
      <div className="p-4 text-center text-sm" style={{ color: 'var(--t-muted)' }}>
        Loading...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b" style={{ borderColor: 'var(--t-border)' }}>
        <button
          onClick={onCreate}
          className="w-full px-3 py-2 rounded text-sm font-medium"
          style={{ background: 'var(--t-primary)', color: '#fff' }}
        >
          + New Game
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {games.length === 0 && (
          <div className="text-xs text-center p-4" style={{ color: 'var(--t-muted)' }}>
            No games yet
          </div>
        )}
        {games.map(g => (
          <div
            key={g.id}
            onClick={() => onSelect(g.id)}
            className="p-2 rounded cursor-pointer group flex items-center justify-between"
            style={{
              background: selectedId === g.id ? 'var(--t-primary)' : 'transparent',
              color: selectedId === g.id ? '#fff' : 'var(--t-text)',
            }}
          >
            <div className="min-w-0">
              <div className="text-sm font-medium truncate">{g.name}</div>
              <div className="flex items-center gap-2 mt-0.5">
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded"
                  style={{
                    background: STATUS_COLORS[g.status] || '#6b7280',
                    color: '#fff',
                  }}
                >
                  {g.status}
                </span>
                {g.current_version > 0 && (
                  <span className="text-[10px]" style={{ color: selectedId === g.id ? '#ddd' : 'var(--t-muted)' }}>
                    v{g.current_version}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(g.id); }}
              className="text-xs px-1.5 py-0.5 rounded opacity-50 hover:opacity-100 active:opacity-100"
              style={{ color: selectedId === g.id ? '#fca5a5' : 'var(--t-error, #ef4444)' }}
            >
              x
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GameList;
