import React from 'react';
import { useAppContext } from '../context/AppContext';

const geminiModels = [
  { id: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
  { id: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
  { id: 'gemini-3-pro-preview', label: 'Gemini 3 Pro' },
];

const claudeModels = [
  { id: 'claude-haiku-4-5-20251001', label: 'Haiku 4.5' },
  { id: 'claude-sonnet-4-6', label: 'Sonnet 4.6' },
  { id: 'claude-opus-4-6', label: 'Opus 4.6' },
];

const ModelSelector: React.FC = () => {
  const {
    activeProvider, activeModel, thinkingEnabled, thinkingBudget, workspaceMode,
    setActiveProvider, setActiveModel, setThinkingEnabled, setThinkingBudget,
  } = useAppContext();

  const models = activeProvider === 'claude' ? claudeModels : geminiModels;

  return (
    <div className="t-card flex flex-col sm:flex-row items-start sm:items-center gap-2 p-2 rounded-lg" style={{ background: 'var(--t-surface)' }}>
      {/* Provider toggle */}
      <div className="flex rounded-md overflow-hidden border" style={{ borderColor: 'var(--t-border)' }}>
        <button
          onClick={() => setActiveProvider('gemini')}
          className="t-btn px-3 py-1 text-xs font-medium transition-colors"
          style={{
            background: activeProvider === 'gemini' ? 'var(--t-primary)' : 'var(--t-surface2)',
            color: activeProvider === 'gemini' ? 'var(--t-text)' : 'var(--t-muted)',
          }}
        >
          Gemini
        </button>
        <button
          onClick={() => setActiveProvider('claude')}
          disabled={workspaceMode === 'claude-code'}
          className={`t-btn px-3 py-1 text-xs font-medium transition-colors ${workspaceMode === 'claude-code' ? 'opacity-50 cursor-not-allowed' : ''}`}
          style={{
            background: activeProvider === 'claude' ? 'var(--t-accent2)' : 'var(--t-surface2)',
            color: activeProvider === 'claude' ? 'var(--t-text)' : 'var(--t-muted)',
          }}
        >
          Claude
        </button>
      </div>

      {/* Model select */}
      <select
        value={activeModel}
        onChange={e => setActiveModel(e.target.value)}
        className="text-xs rounded px-2 py-1 border"
        style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', borderColor: 'var(--t-border)' }}
      >
        {models.map(m => (
          <option key={m.id} value={m.id}>{m.label}</option>
        ))}
      </select>

      {/* Thinking toggle (Claude only) */}
      {activeProvider === 'claude' && (
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1 text-xs cursor-pointer" style={{ color: 'var(--t-muted)' }}>
            <input
              type="checkbox"
              checked={thinkingEnabled}
              onChange={e => setThinkingEnabled(e.target.checked)}
              className="rounded"
            />
            Think
          </label>
          {thinkingEnabled && (
            <input
              type="range"
              min={1024}
              max={32768}
              step={1024}
              value={thinkingBudget}
              onChange={e => setThinkingBudget(Number(e.target.value))}
              className="w-20"
              title={`${(thinkingBudget / 1024).toFixed(0)}K tokens`}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default ModelSelector;
