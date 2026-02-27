import React, { useMemo, useState } from 'react';
import { useAppContext } from '../context/AppContext';
import type { ModelCatalogEntry } from '../context/AppContext';

const CATEGORY_ORDER = ['text', 'image', 'video', 'audio', 'agent', 'embedding'];
const CATEGORY_LABELS: Record<string, string> = {
  text: 'Text', image: 'Image', video: 'Video',
  audio: 'Audio', agent: 'Agent', embedding: 'Embedding',
};

// Fallback models when API catalog hasn't loaded yet
const FALLBACK_MODELS: Record<string, { name: string; category: string }> = {
  'gemini-2.5-flash': { name: 'Gemini 2.5 Flash', category: 'text' },
  'gemini-2.5-pro': { name: 'Gemini 2.5 Pro', category: 'text' },
  'gemini-3-pro-preview': { name: 'Gemini 3 Pro', category: 'text' },
};

type ProviderFilter = 'all' | 'gemini' | 'claude';

const ModelSelector: React.FC = () => {
  const {
    activeProvider, activeModel, thinkingEnabled, thinkingBudget, workspaceMode, modelCatalog,
    setActiveProvider, setActiveModel, setThinkingEnabled, setThinkingBudget,
  } = useAppContext();

  const [providerFilter, setProviderFilter] = useState<ProviderFilter>('all');

  // Flatten catalog into grouped entries: { provider, modelId, entry }
  const allModels = useMemo(() => {
    const items: { provider: 'gemini' | 'claude'; modelId: string; entry: ModelCatalogEntry }[] = [];
    const hasCatalog = Object.keys(modelCatalog).length > 0;

    if (hasCatalog) {
      for (const [prov, models] of Object.entries(modelCatalog)) {
        for (const [modelId, entry] of Object.entries(models)) {
          items.push({ provider: prov as 'gemini' | 'claude', modelId, entry });
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

  const providerBadge = (prov: string) => prov === 'claude' ? 'C' : 'G';

  return (
    <div className="t-card flex flex-col sm:flex-row items-start sm:items-center gap-2 p-2 rounded-lg" style={{ background: 'var(--t-surface)' }}>
      {/* Provider filter */}
      <div className="flex rounded-md overflow-hidden border" style={{ borderColor: 'var(--t-border)' }}>
        {(['all', 'gemini', 'claude'] as ProviderFilter[]).map(f => (
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
            {f === 'all' ? 'All' : f === 'gemini' ? 'Gemini' : 'Claude'}
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
    </div>
  );
};

export default ModelSelector;
