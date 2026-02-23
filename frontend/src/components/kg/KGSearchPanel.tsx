import React, { useState } from 'react';
import * as api from '../../services/apiService';
import { KGDatabase, KGSearchResult, KGNode } from '../../types/kg';
import { NODE_COLORS } from './KGSidebar';

interface Props {
  dbId: string | null;
  databases?: KGDatabase[];
  onSelectNode: (node: KGNode) => void;
}

interface MultiResult {
  dbId: string;
  results: KGSearchResult[];
  error?: string;
}

const KGSearchPanel: React.FC<Props> = ({ dbId, databases = [], onSelectNode }) => {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'hybrid' | 'fts' | 'embedding'>('hybrid');
  const [alpha, setAlpha] = useState(0.40);
  const [beta, setBeta] = useState(0.45);
  const [gamma, setGamma] = useState(0.15);
  const [results, setResults] = useState<KGSearchResult[]>([]);
  const [multiResults, setMultiResults] = useState<MultiResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [multiMode, setMultiMode] = useState(false);
  const [selectedDbs, setSelectedDbs] = useState<Set<string>>(new Set());
  const [showDbPicker, setShowDbPicker] = useState(false);

  const toggleDb = (id: string) => {
    setSelectedDbs(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const selectAllDbs = () => {
    if (selectedDbs.size === databases.length) {
      setSelectedDbs(new Set());
    } else {
      setSelectedDbs(new Set(databases.map(d => d.id)));
    }
  };

  const doSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setResults([]);
    setMultiResults([]);

    try {
      if (multiMode && selectedDbs.size > 0) {
        const data = await api.multiSearchKG(query.trim(), Array.from(selectedDbs), mode, 10);
        const grouped: MultiResult[] = [];
        for (const [dbKey, val] of Object.entries(data)) {
          if ((val as any).error) {
            grouped.push({ dbId: dbKey, results: [], error: (val as any).error });
          } else {
            grouped.push({ dbId: dbKey, results: (val as any).results || [] });
          }
        }
        grouped.sort((a, b) => {
          const aMax = a.results[0]?.score || 0;
          const bMax = b.results[0]?.score || 0;
          return bMax - aMax;
        });
        setMultiResults(grouped);
      } else if (dbId) {
        const data = await api.searchKG(dbId, query.trim(), mode, 20, alpha, beta, gamma);
        setResults(data.results || []);
      }
    } catch (e: any) {
      setError(e.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const canSearch = multiMode ? selectedDbs.size > 0 : !!dbId;

  if (!multiMode && !dbId) return (
    <div className="flex-1 flex flex-col items-center justify-center gap-2" style={{ color: 'var(--t-muted)' }}>
      <p className="text-sm">Select a database to search</p>
      {databases.length > 1 && (
        <button onClick={() => setMultiMode(true)}
          className="t-btn px-3 py-1.5 text-xs rounded"
          style={{ background: 'var(--t-primary)', color: '#fff' }}>
          or search across multiple KGs
        </button>
      )}
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
          placeholder={multiMode ? `Search across ${selectedDbs.size} KGs...` : 'Search the knowledge graph...'}
          className="flex-1 px-3 py-2 rounded text-sm focus:outline-none focus:ring-1"
          style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', '--tw-ring-color': 'var(--t-primary)' } as React.CSSProperties}
        />
        <button onClick={doSearch} disabled={loading || !canSearch}
          className="t-btn px-4 py-2 rounded text-sm"
          style={{ background: 'var(--t-primary)', color: '#fff', opacity: canSearch ? 1 : 0.5 }}>
          {loading ? '...' : 'Search'}
        </button>
      </div>

      {/* Mode + weights + multi toggle */}
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
        {databases.length > 1 && (
          <button onClick={() => { setMultiMode(!multiMode); setResults([]); setMultiResults([]); }}
            className="t-btn px-2 py-1 text-[10px] rounded"
            style={multiMode
              ? { background: 'var(--t-accent1, #8b5cf6)', color: '#fff' }
              : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
            MULTI-KG
          </button>
        )}
        {mode === 'hybrid' && !multiMode && (
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

      {/* Multi-KG database picker */}
      {multiMode && (
        <div className="border rounded p-2" style={{ borderColor: 'var(--t-border)' }}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold" style={{ color: 'var(--t-muted)' }}>
              Databases ({selectedDbs.size}/{databases.length})
            </span>
            <div className="flex gap-1">
              <button onClick={selectAllDbs} className="t-btn text-[10px] px-1.5 py-0.5 rounded"
                style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
                {selectedDbs.size === databases.length ? 'Deselect All' : 'Select All'}
              </button>
              <button onClick={() => setShowDbPicker(!showDbPicker)}
                className="t-btn text-[10px] px-1.5 py-0.5 rounded"
                style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
                {showDbPicker ? 'Collapse' : 'Expand'}
              </button>
            </div>
          </div>
          {showDbPicker && (
            <div className="max-h-32 overflow-y-auto space-y-0.5">
              {databases.map(db => (
                <label key={db.id} className="flex items-center gap-2 px-1 py-0.5 rounded text-[10px] cursor-pointer"
                  style={{ color: selectedDbs.has(db.id) ? 'var(--t-text)' : 'var(--t-muted)',
                           background: selectedDbs.has(db.id) ? 'var(--t-surface2)' : undefined }}>
                  <input type="checkbox" checked={selectedDbs.has(db.id)}
                    onChange={() => toggleDb(db.id)} className="w-3 h-3" />
                  <span className="truncate">{db.id}</span>
                  <span className="ml-auto">{db.size_mb.toFixed(1)}MB</span>
                </label>
              ))}
            </div>
          )}
          {!showDbPicker && selectedDbs.size > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {Array.from(selectedDbs).slice(0, 5).map(id => (
                <span key={id} className="text-[9px] px-1.5 py-0.5 rounded"
                  style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>{id}</span>
              ))}
              {selectedDbs.size > 5 && (
                <span className="text-[9px]" style={{ color: 'var(--t-muted)' }}>+{selectedDbs.size - 5} more</span>
              )}
            </div>
          )}
        </div>
      )}

      {error && <p className="text-xs text-red-400">{error}</p>}

      {/* Single-DB Results */}
      {!multiMode && (
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
      )}

      {/* Multi-DB Results */}
      {multiMode && (
        <div className="flex-1 overflow-y-auto space-y-3">
          {multiResults.map(group => (
            <div key={group.dbId}>
              <p className="text-[10px] font-bold mb-1 px-1 sticky top-0"
                style={{ color: 'var(--t-primary)', background: 'var(--t-bg)' }}>
                {group.dbId} {group.error && <span className="text-red-400">({group.error})</span>}
                {!group.error && <span style={{ color: 'var(--t-muted)' }}> ({group.results.length} results)</span>}
              </p>
              <div className="space-y-1">
                {group.results.map((r, i) => (
                  <button key={`${group.dbId}-${r.node.id}-${i}`}
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
              </div>
            </div>
          ))}
          {multiResults.length === 0 && query && !loading && (
            <p className="text-xs text-center py-4" style={{ color: 'var(--t-muted)' }}>No results across selected KGs</p>
          )}
        </div>
      )}
    </div>
  );
};

export default KGSearchPanel;
