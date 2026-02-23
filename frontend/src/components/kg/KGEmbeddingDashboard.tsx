import React, { useState, useEffect } from 'react';
import * as api from '../../services/apiService';
import { KGEmbeddingStatus, KGProjectionPoint } from '../../types/kg';
import { NODE_COLORS } from './KGSidebar';

interface Props {
  dbId: string | null;
}

const KGEmbeddingDashboard: React.FC<Props> = ({ dbId }) => {
  const [status, setStatus] = useState<KGEmbeddingStatus | null>(null);
  const [quality, setQuality] = useState<any>(null);
  const [projection, setProjection] = useState<KGProjectionPoint[]>([]);
  const [projMethod, setProjMethod] = useState<'pca' | 'tsne'>('pca');
  const [generating, setGenerating] = useState(false);
  const [genStrategy, setGenStrategy] = useState('gemini');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!dbId) return;
    loadStatus();
  }, [dbId]);

  const loadStatus = async () => {
    if (!dbId) return;
    setLoading(true);
    try {
      const s = await api.getKGEmbeddingStatus(dbId);
      setStatus(s);
    } catch { /* ignore */ }
    setLoading(false);
  };

  const loadQuality = async () => {
    if (!dbId) return;
    try {
      const q = await api.getKGEmbeddingQuality(dbId);
      setQuality(q);
    } catch { /* ignore */ }
  };

  const loadProjection = async () => {
    if (!dbId) return;
    try {
      const data = await api.getKGEmbeddingProjection(dbId, projMethod, 500);
      setProjection(data.points || []);
    } catch { /* ignore */ }
  };

  const generateEmbeddings = async () => {
    if (!dbId) return;
    setGenerating(true);
    setError('');
    try {
      await api.generateKGEmbeddings(dbId, genStrategy);
      await loadStatus();
    } catch (e: any) {
      setError(e.message || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  if (!dbId) return (
    <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--t-muted)' }}>
      Select a database for embedding analysis
    </div>
  );

  // Compute projection bounds for SVG
  const xVals = projection.map(p => p.x);
  const yVals = projection.map(p => p.y);
  const xMin = Math.min(...xVals, 0);
  const xMax = Math.max(...xVals, 1);
  const yMin = Math.min(...yVals, 0);
  const yMax = Math.max(...yVals, 1);
  const pad = 20;

  return (
    <div className="flex-1 overflow-y-auto p-3 space-y-4">
      <h3 className="text-sm font-bold" style={{ color: 'var(--t-text)' }}>Embedding Observatory</h3>

      {/* Status cards */}
      {status && (
        <div className="grid grid-cols-4 gap-2">
          <div className="p-2 rounded text-center" style={{ background: 'var(--t-surface2)' }}>
            <p className="text-lg font-bold" style={{ color: status.has_embeddings ? 'var(--t-primary)' : '#ef4444' }}>
              {status.has_embeddings ? 'Yes' : 'No'}
            </p>
            <p className="text-[10px]" style={{ color: 'var(--t-muted)' }}>Has Embeddings</p>
          </div>
          <div className="p-2 rounded text-center" style={{ background: 'var(--t-surface2)' }}>
            <p className="text-lg font-bold" style={{ color: 'var(--t-primary)' }}>{status.count}</p>
            <p className="text-[10px]" style={{ color: 'var(--t-muted)' }}>Vectors</p>
          </div>
          <div className="p-2 rounded text-center" style={{ background: 'var(--t-surface2)' }}>
            <p className="text-lg font-bold" style={{ color: 'var(--t-primary)' }}>{status.dimensions || '-'}</p>
            <p className="text-[10px]" style={{ color: 'var(--t-muted)' }}>Dimensions</p>
          </div>
          <div className="p-2 rounded text-center" style={{ background: 'var(--t-surface2)' }}>
            <p className="text-lg font-bold" style={{ color: status.coverage_pct > 80 ? 'var(--t-primary)' : '#f59e0b' }}>
              {status.coverage_pct.toFixed(0)}%
            </p>
            <p className="text-[10px]" style={{ color: 'var(--t-muted)' }}>Coverage</p>
          </div>
        </div>
      )}

      {/* Generate section */}
      <div className="p-3 rounded" style={{ background: 'var(--t-surface2)' }}>
        <p className="text-xs font-bold mb-2" style={{ color: 'var(--t-text)' }}>Generate Embeddings</p>
        <div className="flex gap-2 items-center">
          <select value={genStrategy} onChange={e => setGenStrategy(e.target.value)}
            className="px-2 py-1.5 rounded text-xs"
            style={{ background: 'var(--t-surface)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}>
            {(status?.strategies_available || ['gemini', 'model2vec']).map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button onClick={generateEmbeddings} disabled={generating}
            className="t-btn px-3 py-1.5 text-xs rounded"
            style={{ background: 'var(--t-primary)', color: '#fff' }}>
            {generating ? 'Generating...' : 'Generate'}
          </button>
        </div>
        {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
      </div>

      {/* Quality metrics */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <h4 className="text-xs font-bold" style={{ color: 'var(--t-text)' }}>Quality Metrics</h4>
          <button onClick={loadQuality} className="t-btn px-2 py-0.5 text-[10px] rounded"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>Load</button>
        </div>
        {quality && (
          <pre className="p-2 rounded text-[10px]" style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
            {JSON.stringify(quality, null, 2)}
          </pre>
        )}
      </div>

      {/* 2D Projection */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <h4 className="text-xs font-bold" style={{ color: 'var(--t-text)' }}>2D Projection</h4>
          <div className="flex gap-1">
            {(['pca', 'tsne'] as const).map(m => (
              <button key={m} onClick={() => setProjMethod(m)}
                className="t-btn px-2 py-0.5 text-[10px] rounded"
                style={projMethod === m
                  ? { background: 'var(--t-primary)', color: '#fff' }
                  : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
                {m.toUpperCase()}
              </button>
            ))}
          </div>
          <button onClick={loadProjection} className="t-btn px-2 py-0.5 text-[10px] rounded"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>Load</button>
        </div>
        {projection.length > 0 && (
          <div className="rounded overflow-hidden" style={{ background: '#0d1117', height: 350 }}>
            <svg viewBox={`0 0 500 350`} className="w-full h-full">
              {projection.map(p => {
                const x = pad + ((p.x - xMin) / (xMax - xMin || 1)) * (500 - 2 * pad);
                const y = pad + ((p.y - yMin) / (yMax - yMin || 1)) * (350 - 2 * pad);
                return (
                  <g key={p.id}>
                    <circle cx={x} cy={y} r={3}
                      fill={NODE_COLORS[p.type] || NODE_COLORS.default} opacity={0.7} />
                    <title>{p.name} ({p.type})</title>
                  </g>
                );
              })}
            </svg>
            {/* Legend */}
            <div className="flex flex-wrap gap-2 px-2 pb-2">
              {[...new Set(projection.map(p => p.type))].slice(0, 8).map(t => (
                <span key={t} className="flex items-center gap-1 text-[10px]" style={{ color: '#9ca3af' }}>
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: NODE_COLORS[t] || NODE_COLORS.default }} />
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KGEmbeddingDashboard;
