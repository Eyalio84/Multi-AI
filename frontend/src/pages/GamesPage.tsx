import React, { useState, useEffect, useCallback } from 'react';
import * as api from '../services/apiService';
import type { GameProject } from '../types/game';
import GameInterview from '../components/games/GameInterview';
import GamePreview from '../components/games/GamePreview';
import GameCodeEditor from '../components/games/GameCodeEditor';
import GameChat from '../components/games/GameChat';
import GameDesignView from '../components/games/GameDesignView';
import GameVersions from '../components/games/GameVersions';

type Tab = 'interview' | 'preview' | 'code' | 'chat' | 'gdd' | 'versions';

const TABS: { id: Tab; label: string }[] = [
  { id: 'interview', label: 'Interview' },
  { id: 'preview', label: 'Preview' },
  { id: 'code', label: 'Code' },
  { id: 'chat', label: 'Chat' },
  { id: 'gdd', label: 'GDD' },
  { id: 'versions', label: 'Versions' },
];

const STATUS_COLORS: Record<string, string> = {
  draft: '#6b7280',
  interviewing: '#f59e0b',
  generating: '#3b82f6',
  playable: '#10b981',
  editing: '#8b5cf6',
};

const GamesPage: React.FC = () => {
  const [games, setGames] = useState<GameProject[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('interview');
  const [generating, setGenerating] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);

  const selectedGame = games.find(g => g.id === selectedId) || null;

  const loadGames = useCallback(async () => {
    setLoading(true);
    try {
      const list = await api.listGames();
      setGames(list);
    } catch (e: any) {
      console.error('Failed to load games:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadGames(); }, [loadGames]);

  const handleCreate = async () => {
    const name = prompt('Game name:');
    if (!name) return;
    try {
      const game = await api.createGame(name);
      await loadGames();
      setSelectedId(game.id);
      setTab('interview');
      setPickerOpen(false);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this game project?')) return;
    await api.deleteGame(id);
    if (selectedId === id) setSelectedId(null);
    loadGames();
  };

  const handleInterviewComplete = async () => {
    await loadGames();
    if (selectedId) {
      const updated = await api.getGame(selectedId);
      setGames(prev => prev.map(g => g.id === selectedId ? updated : g));
      setTab('gdd');
    }
  };

  const handleGenerate = async () => {
    if (!selectedId || generating) return;
    setGenerating(true);
    setTab('preview');

    try {
      const stream = await api.streamGenerateGame(selectedId);
      const reader = stream.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const lines = decoder.decode(value, { stream: true }).split('\n');
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'files_complete') {
              const updated = await api.getGame(selectedId);
              setGames(prev => prev.map(g => g.id === selectedId ? updated : g));
            }
          } catch {}
        }
      }
      await loadGames();
    } catch (e: any) {
      alert('Generation failed: ' + e.message);
    } finally {
      setGenerating(false);
    }
  };

  const refreshSelected = async () => {
    if (!selectedId) return;
    const updated = await api.getGame(selectedId);
    setGames(prev => prev.map(g => g.id === selectedId ? updated : g));
  };

  // ── No game selected: show full-screen landing ──
  if (!selectedGame) {
    return (
      <div className="flex flex-col h-full">
        {/* Top bar with game picker */}
        <div className="border-b px-3 py-2" style={{ borderColor: 'var(--t-border)' }}>
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-bold" style={{ color: 'var(--t-text)' }}>Game Studio</span>
            <div className="flex items-center gap-2">
              {games.length > 0 && (
                <div className="relative">
                  <button
                    onClick={() => setPickerOpen(!pickerOpen)}
                    className="px-2 py-1 rounded text-xs"
                    style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
                  >
                    {games.length} game{games.length !== 1 ? 's' : ''} ▾
                  </button>
                  {pickerOpen && (
                    <>
                      <div className="fixed inset-0 z-30" onClick={() => setPickerOpen(false)} />
                      <div
                        className="absolute right-0 top-full mt-1 w-56 rounded-lg shadow-lg z-40 overflow-hidden"
                        style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}
                      >
                        {games.map(g => (
                          <button
                            key={g.id}
                            onClick={() => { setSelectedId(g.id); setPickerOpen(false); }}
                            className="w-full flex items-center justify-between px-3 py-2 text-left text-sm"
                            style={{ color: 'var(--t-text)' }}
                          >
                            <span className="truncate">{g.name}</span>
                            <span
                              className="text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ml-2"
                              style={{ background: STATUS_COLORS[g.status] || '#6b7280', color: '#fff' }}
                            >
                              {g.status}
                            </span>
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
              <button
                onClick={handleCreate}
                className="px-3 py-1 rounded text-xs font-medium"
                style={{ background: 'var(--t-primary)', color: '#fff' }}
              >
                + New
              </button>
            </div>
          </div>
        </div>

        {/* Landing */}
        <div className="flex-1 flex items-center justify-center px-6">
          <div className="text-center space-y-4 max-w-xs">
            <div style={{ color: 'var(--t-muted)' }}>
              <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-base font-semibold" style={{ color: 'var(--t-text)' }}>
              Phaser 3 Game Studio
            </div>
            <div className="text-xs leading-relaxed" style={{ color: 'var(--t-muted)' }}>
              Design 2D RPG games through a structured interview. AI generates Phaser 3 code with sprites, physics, NPCs, and combat.
            </div>
            <button
              onClick={handleCreate}
              className="w-full px-4 py-2.5 rounded-lg text-sm font-medium"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
            >
              Create Your First Game
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Game selected: full-screen game workspace ──
  return (
    <div className="flex flex-col h-full">
      {/* Top bar: game selector + actions */}
      <div className="border-b" style={{ borderColor: 'var(--t-border)' }}>
        <div className="flex items-center justify-between px-3 py-2 gap-2">
          {/* Left: game picker */}
          <div className="flex items-center gap-2 min-w-0">
            <div className="relative">
              <button
                onClick={() => setPickerOpen(!pickerOpen)}
                className="flex items-center gap-1 px-2 py-1 rounded text-sm font-medium min-w-0"
                style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}
              >
                <span className="truncate max-w-[120px]">{selectedGame.name}</span>
                <span style={{ color: 'var(--t-muted)' }}>▾</span>
              </button>
              {pickerOpen && (
                <>
                  <div className="fixed inset-0 z-30" onClick={() => setPickerOpen(false)} />
                  <div
                    className="absolute left-0 top-full mt-1 w-64 rounded-lg shadow-lg z-40 overflow-hidden"
                    style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}
                  >
                    {games.map(g => (
                      <button
                        key={g.id}
                        onClick={() => { setSelectedId(g.id); setPickerOpen(false); }}
                        className="w-full flex items-center justify-between px-3 py-2 text-left text-sm"
                        style={{
                          background: g.id === selectedId ? 'var(--t-primary)' : 'transparent',
                          color: g.id === selectedId ? '#fff' : 'var(--t-text)',
                        }}
                      >
                        <span className="truncate">{g.name}</span>
                        <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                          <span
                            className="text-[10px] px-1.5 py-0.5 rounded"
                            style={{ background: STATUS_COLORS[g.status] || '#6b7280', color: '#fff' }}
                          >
                            {g.status}
                          </span>
                          <button
                            onClick={(e) => handleDelete(g.id, e)}
                            className="text-[10px] px-1 rounded hover:bg-red-500/20"
                            style={{ color: '#ef4444' }}
                          >
                            x
                          </button>
                        </div>
                      </button>
                    ))}
                    <button
                      onClick={handleCreate}
                      className="w-full px-3 py-2 text-left text-sm border-t"
                      style={{ borderColor: 'var(--t-border)', color: 'var(--t-primary)' }}
                    >
                      + New Game
                    </button>
                  </div>
                </>
              )}
            </div>
            <span className="text-[10px] hidden sm:inline" style={{ color: 'var(--t-muted)' }}>
              v{selectedGame.current_version}
            </span>
          </div>

          {/* Right: generate button */}
          {(selectedGame.game_design_doc || Object.keys(selectedGame.interview_data || {}).length >= 4) && (
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex-shrink-0 px-3 py-1 rounded text-xs font-medium"
              style={{
                background: generating ? 'var(--t-surface2)' : '#10b981',
                color: '#fff',
              }}
            >
              {generating ? 'Generating...' : selectedGame.files && Object.keys(selectedGame.files).length > 0 ? 'Regen' : 'Generate'}
            </button>
          )}
        </div>

        {/* Tabs — horizontally scrollable, full-width */}
        <div
          className="flex items-center gap-0.5 px-2 pb-1.5 overflow-x-auto"
          style={{ WebkitOverflowScrolling: 'touch', scrollbarWidth: 'none' }}
        >
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className="flex-shrink-0 px-3 py-1 rounded text-xs font-medium transition-colors"
              style={{
                background: tab === t.id ? 'var(--t-primary)' : 'transparent',
                color: tab === t.id ? '#fff' : 'var(--t-muted)',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content — fills remaining space */}
      <div className="flex-1 overflow-hidden">
        {tab === 'interview' && <GameInterview game={selectedGame} onComplete={handleInterviewComplete} />}
        {tab === 'preview' && <GamePreview game={selectedGame} />}
        {tab === 'code' && <GameCodeEditor game={selectedGame} onUpdate={refreshSelected} />}
        {tab === 'chat' && <GameChat game={selectedGame} />}
        {tab === 'gdd' && <GameDesignView gdd={selectedGame.game_design_doc} />}
        {tab === 'versions' && <GameVersions game={selectedGame} onRestore={refreshSelected} />}
      </div>
    </div>
  );
};

export default GamesPage;
