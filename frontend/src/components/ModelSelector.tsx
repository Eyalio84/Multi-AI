import React, { useMemo, useState } from 'react';
import { useAppContext } from '../context/AppContext';
import type { ModelCatalogEntry } from '../context/AppContext';

const CATEGORY_ORDER = ['text', 'reasoning', 'image', 'video', 'audio', 'agent', 'embedding'];
const CATEGORY_LABELS: Record<string, string> = {
  text: 'Text', reasoning: 'Reasoning', image: 'Image', video: 'Video',
  audio: 'Audio', agent: 'Agent', embedding: 'Embedding',
};

// Fallback models when API catalog hasn't loaded yet
const FALLBACK_MODELS: Record<string, { name: string; category: string }> = {
  'gemini-2.5-flash': { name: 'Gemini 2.5 Flash', category: 'text' },
  'gemini-2.5-pro': { name: 'Gemini 2.5 Pro', category: 'text' },
  'gemini-3-pro-preview': { name: 'Gemini 3 Pro', category: 'text' },
};

type ProviderFilter = 'all' | 'gemini' | 'claude' | 'openai';

const ModelSelector: React.FC = () => {
  const {
    activeProvider, activeModel, thinkingEnabled, thinkingBudget, workspaceMode, modelCatalog,
    setActiveProvider, setActiveModel, setThinkingEnabled, setThinkingBudget,
  } = useAppContext();

  const [providerFilter, setProviderFilter] = useState<ProviderFilter>('all');

  // Flatten catalog into grouped entries: { provider, modelId, entry }
  const allModels = useMemo(() => {
    const items: { provider: 'gemini' | 'claude' | 'openai'; modelId: string; entry: ModelCatalogEntry }[] = [];
    const hasCatalog = Object.keys(modelCatalog).length > 0;

    if (hasCatalog) {
      for (const [prov, models] of Object.entries(modelCatalog)) {
        for (const [modelId, entry] of Object.entries(models)) {
          items.push({ provider: prov as 'gemini' | 'claude' | 'openai', modelId, entry });
        }
      }
    } else {
      // Fallback before API loads
      for (const [modelId, info] of Object.entries(FALLBACK_MODELS)) {
        items.push({
          provider: 'gemini',
          modelId,
          entry: { name: info.name, category: info.category, context: '', cost_in: '', cost_out: '', use_case: '' },
        });
      }
    }
    return items;
  }, [modelCatalog]);

  // Filter by provider
  const filtered = useMemo(() => {
    if (providerFilter === 'all') return allModels;
    return allModels.filter(m => m.provider === providerFilter);
  }, [allModels, providerFilter]);

  // Group by category
  const grouped = useMemo(() => {
    const groups = new Map<string, typeof filtered>();
    for (const cat of CATEGORY_ORDER) groups.set(cat, []);
    for (const item of filtered) {
      const cat = item.entry.category || 'text';
      if (!groups.has(cat)) groups.set(cat, []);
      groups.get(cat)!.push(item);
    }
    // Remove empty groups
    for (const [key, val] of groups) {
      if (val.length === 0) groups.delete(key);
    }
    return groups;
  }, [filtered]);

  const handleModelChange = (modelId: string) => {
    // Find the provider for this model and set both
    const item = allModels.find(m => m.modelId === modelId);
    if (item) {
      setActiveProvider(item.provider);
      // setActiveProvider resets model — override immediately
      setActiveModel(modelId);
    } else {
      setActiveModel(modelId);
    }
  };

  const providerBadge = (prov: string) => prov === 'claude' ? 'C' : prov === 'openai' ? 'O' : 'G';

  // Check if current model is a reasoning model (o3/o4)
  const isReasoningModel = activeModel.startsWith('o3') || activeModel.startsWith('o4');
  const [reasoningEffort, setReasoningEffort] = useState<'low' | 'medium' | 'high'>('medium');

  return (
    <div className="t-card flex flex-col sm:flex-row items-start sm:items-center gap-2 p-2 rounded-lg" style={{ background: 'var(--t-surface)' }}>
      {/* Provider filter */}
      <div className="flex rounded-md overflow-hidden border" style={{ borderColor: 'var(--t-border)' }}>
        {(['all', 'gemini', 'claude', 'openai'] as ProviderFilter[]).map(f => (
          <button
            key={f}
            onClick={() => setProviderFilter(f)}
            disabled={f === 'claude' && workspaceMode === 'claude-code'}
            className={`t-btn px-3 py-1 text-xs font-medium transition-colors ${f === 'claude' && workspaceMode === 'claude-code' ? 'opacity-50 cursor-not-allowed' : ''}`}
            style={{
              background: providerFilter === f ? 'var(--t-primary)' : 'var(--t-surface2)',
              color: providerFilter === f ? 'var(--t-text)' : 'var(--t-muted)',
            }}
          >
            {f === 'all' ? 'All' : f === 'gemini' ? 'Gemini' : f === 'openai' ? 'OpenAI' : 'Claude'}
          </button>
        ))}
      </div>

      {/* Grouped model select */}
      <select
        value={activeModel}
        onChange={e => handleModelChange(e.target.value)}
        className="text-xs rounded px-2 py-1 border min-w-[180px]"
        style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', borderColor: 'var(--t-border)' }}
      >
        {Array.from(grouped.entries()).map(([cat, items]) => (
          <optgroup key={cat} label={CATEGORY_LABELS[cat] || cat}>
            {items.map(m => (
              <option
                key={m.modelId}
                value={m.modelId}
                disabled={cat === 'embedding'}
              >
                [{providerBadge(m.provider)}] {m.entry.name}
                {m.entry.use_case ? ` — ${m.entry.use_case}` : ''}
              </option>
            ))}
          </optgroup>
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

      {/* Reasoning effort (OpenAI o-series only) */}
      {isReasoningModel && (
        <div className="flex items-center gap-2">
          <label className="text-xs" style={{ color: 'var(--t-muted)' }}>Effort</label>
          <select
            value={reasoningEffort}
            onChange={e => setReasoningEffort(e.target.value as 'low' | 'medium' | 'high')}
            className="text-xs rounded px-2 py-1 border"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', borderColor: 'var(--t-border)' }}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      )}
    </div>
  );
};

export default ModelSelector;
