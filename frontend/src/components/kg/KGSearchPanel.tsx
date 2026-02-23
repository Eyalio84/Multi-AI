import React, { useState } from 'react';
import * as api from '../../services/apiService';
import { KGSearchResult, KGNode } from '../../types/kg';
import { NODE_COLORS } from './KGSidebar';

interface Props {
  dbId: string | null;
  onSelectNode: (node: KGNode) => void;
}

const KGSearchPanel: React.FC<Props> = ({ dbId, onSelectNode }) => {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'hybrid' | 'fts' | 'embedding'>('hybrid');
  const [alpha, setAlpha] = useState(0.40);
  const [beta, setBeta] = useState(0.45);
  const [gamma, setGamma] = useState(0.15);
  const [results, setResults] = useState<KGSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const doSearch = async () => {
    if (!dbId || !query.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.searchKG(dbId, query.trim(), mode, 20, alpha, beta, gamma);
      setResults(data.results || []);
    } catch (e: any) {
      setError(e.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  if (!dbId) return (
    <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--t-muted)' }}>
      Select a database to search
    </div>
  );

  return (
    <div className="flex-1 flex flex-col overflow-hidden p-3 gap-3">
      {/* Search bar */}
      <div className="flex gap-2">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && doSearch()}
          placeholder="Search the knowledge graph..."
          className="flex-1 px-3 py-2 rounded text-sm focus:outline-none focus:ring-1"
          style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', '--tw-ring-color': 'var(--t-primary)' } as React.CSSProperties}
        />
        <button onClick={doSearch} disabled={loading}
          className="t-btn px-4 py-2 rounded text-sm"
          style={{ background: 'var(--t-primary)', color: '#fff' }}>
          {loading ? '...' : 'Search'}
        </button>
      </div>

      {/* Mode + weights */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1">
          {(['hybrid', 'fts', 'embedding'] as const).map(m => (
            <button key={m} onClick={() => setMode(m)}
              className="t-btn px-2 py-1 text-[10px] rounded"
              style={mode === m
                ? { background: 'var(--t-primary)', color: '#fff' }
                : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
              {m.toUpperCase()}
            </button>
          ))}
        </div>
        {mode === 'hybrid' && (
          <div className="flex gap-3 text-[10px]" style={{ color: 'var(--t-muted)' }}>
            <label className="flex items-center gap-1">
              \u03b1<input type="range" min="0" max="1" step="0.05" value={alpha}
                onChange={e => setAlpha(+e.target.value)} className="w-12 h-1" />
              {alpha.toFixed(2)}
            </label>
            <label className="flex items-center gap-1">
              \u03b2<input type="range" min="0" max="1" step="0.05" value={beta}
                onChange={e => setBeta(+e.target.value)} className="w-12 h-1" />
              {beta.toFixed(2)}
            </label>
            <label className="flex items-center gap-1">
              \u03b3<input type="range" min="0" max="1" step="0.05" value={gamma}
                onChange={e => setGamma(+e.target.value)} className="w-12 h-1" />
              {gamma.toFixed(2)}
            </label>
          </div>
        )}
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {/* Results */}
      <div className="flex-1 overflow-y-auto space-y-1">
        {results.map((r, i) => (
          <button key={r.node.id + '-' + i}
            onClick={() => onSelectNode(r.node)}
            className="t-btn w-full text-left px-3 py-2 rounded flex items-center gap-2"
            style={{ background: 'var(--t-surface2)' }}>
            <span className="text-xs font-mono w-8 text-right" style={{ color: 'var(--t-primary)' }}>
              {(r.score * 100).toFixed(0)}%
            </span>
            <span className="h-2 w-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: NODE_COLORS[r.node.type] || NODE_COLORS.default }} />
            <div className="flex-1 min-w-0">
              <span className="text-xs truncate block" style={{ color: 'var(--t-text2)' }}>{r.node.name}</span>
              <span className="text-[10px]" style={{ color: 'var(--t-muted)' }}>{r.node.type} | {r.method}</span>
            </div>
          </button>
        ))}
        {results.length === 0 && query && !loading && (
          <p className="text-xs text-center py-4" style={{ color: 'var(--t-muted)' }}>No results</p>
        )}
      </div>
    </div>
  );
};

export default KGSearchPanel;
