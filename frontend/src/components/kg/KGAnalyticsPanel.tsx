import React, { useState, useEffect } from 'react';
import * as api from '../../services/apiService';
import { showToast } from '../../hooks/useToast';
import { KGAnalyticsSummary, KGCentralityNode, KGCommunity, KGNode } from '../../types/kg';
import { NODE_COLORS } from './KGSidebar';

interface Props {
  dbId: string | null;
  onSelectNode: (node: KGNode) => void;
}

const KGAnalyticsPanel: React.FC<Props> = ({ dbId, onSelectNode }) => {
  const [summary, setSummary] = useState<KGAnalyticsSummary | null>(null);
  const [centrality, setCentrality] = useState<KGCentralityNode[]>([]);
  const [communities, setCommunities] = useState<KGCommunity[]>([]);
  const [metric, setMetric] = useState('degree');
  const [pathSource, setPathSource] = useState('');
  const [pathTarget, setPathTarget] = useState('');
  const [pathResult, setPathResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!dbId) return;
    loadAnalytics();
  }, [dbId]);

  const loadAnalytics = async () => {
    if (!dbId) return;
    setLoading(true);
    setError('');
    try {
      const [s, c] = await Promise.all([
        api.getKGAnalyticsSummary(dbId),
        api.getKGCentrality(dbId, metric, 15),
      ]);
      setSummary(s);
      setCentrality(c.nodes || []);
    } catch (e: any) {
      setError(e.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const loadCommunities = async () => {
    if (!dbId) return;
    try {
      const data = await api.getKGCommunities(dbId);
      setCommunities(data.communities || []);
    } catch (e: any) { showToast(e.message || 'Failed to detect communities'); }
  };

  const findPath = async () => {
    if (!dbId || !pathSource || !pathTarget) return;
    try {
      const data = await api.findKGPath(dbId, pathSource, pathTarget);
      setPathResult(data);
    } catch (e: any) {
      setPathResult({ error: e.message });
    }
  };

  const changMetric = async (m: string) => {
    setMetric(m);
    if (!dbId) return;
    try {
      const c = await api.getKGCentrality(dbId, m, 15);
      setCentrality(c.nodes || []);
    } catch (e: any) { showToast(e.message || 'Failed to load centrality'); }
  };

  if (!dbId) return (
    <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--t-muted)' }}>
      Select a database for analytics
    </div>
  );

  return (
    <div className="flex-1 overflow-y-auto p-3 space-y-4">
      {error && <p className="text-xs text-red-400">{error}</p>}

      {/* Summary */}
      {summary && (
        <div className="grid grid-cols-3 gap-2">
          {[
            ['Nodes', summary.node_count],
            ['Edges', summary.edge_count],
            ['Density', summary.density?.toFixed(4)],
            ['Components', summary.components],
            ['Avg Degree', summary.avg_degree?.toFixed(2)],
            ['Clustering', summary.clustering?.toFixed(4)],
          ].map(([label, val]) => (
            <div key={String(label)} className="p-2 rounded text-center" style={{ background: 'var(--t-surface2)' }}>
              <p className="text-lg font-bold" style={{ color: 'var(--t-primary)' }}>{val}</p>
              <p className="text-[10px]" style={{ color: 'var(--t-muted)' }}>{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Centrality */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <h4 className="text-xs font-bold" style={{ color: 'var(--t-text)' }}>Centrality</h4>
          <div className="flex gap-1">
            {['degree', 'betweenness', 'pagerank'].map(m => (
              <button key={m} onClick={() => changMetric(m)}
                className="t-btn px-2 py-0.5 text-[10px] rounded"
                style={metric === m
                  ? { background: 'var(--t-primary)', color: '#fff' }
                  : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
                {m}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-1">
          {centrality.map((n, i) => {
            const maxScore = centrality[0]?.score || 1;
            return (
              <button key={n.id} onClick={() => onSelectNode({ id: n.id, name: n.name, type: n.type, properties: {} })}
                className="t-btn w-full flex items-center gap-2 px-2 py-1 rounded text-xs"
                style={{ background: 'var(--t-surface2)' }}>
                <span className="w-4 text-right" style={{ color: 'var(--t-muted)' }}>{i + 1}</span>
                <span className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: NODE_COLORS[n.type] || NODE_COLORS.default }} />
                <span className="flex-1 text-left truncate" style={{ color: 'var(--t-text2)' }}>{n.name}</span>
                <div className="w-20 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--t-border)' }}>
                  <div className="h-full rounded-full" style={{
                    background: 'var(--t-primary)',
                    width: `${(n.score / maxScore) * 100}%`
                  }} />
                </div>
                <span className="w-12 text-right font-mono" style={{ color: 'var(--t-muted)' }}>
                  {n.score.toFixed(3)}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Communities */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <h4 className="text-xs font-bold" style={{ color: 'var(--t-text)' }}>Communities</h4>
          <button onClick={loadCommunities} className="t-btn px-2 py-0.5 text-[10px] rounded"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>Detect</button>
        </div>
        {communities.map(c => (
          <div key={c.id} className="p-2 rounded mb-1" style={{ background: 'var(--t-surface2)' }}>
            <p className="text-xs font-bold" style={{ color: 'var(--t-text)' }}>
              Community {c.id} ({c.size} members)
            </p>
            <div className="flex flex-wrap gap-1 mt-1">
              {c.members.slice(0, 10).map(m => (
                <span key={m.id} className="text-[10px] px-1 rounded"
                  style={{ background: NODE_COLORS[m.type] || NODE_COLORS.default, color: '#fff' }}>
                  {m.name}
                </span>
              ))}
              {c.size > 10 && <span className="text-[10px]" style={{ color: 'var(--t-muted)' }}>+{c.size - 10} more</span>}
            </div>
          </div>
        ))}
      </div>

      {/* Path finder */}
      <div>
        <h4 className="text-xs font-bold mb-2" style={{ color: 'var(--t-text)' }}>Shortest Path</h4>
        <div className="flex gap-2 mb-2">
          <input value={pathSource} onChange={e => setPathSource(e.target.value)}
            placeholder="Source node ID" className="flex-1 px-2 py-1 rounded text-xs focus:outline-none"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }} />
          <span className="text-xs self-center" style={{ color: 'var(--t-muted)' }}>\u2192</span>
          <input value={pathTarget} onChange={e => setPathTarget(e.target.value)}
            placeholder="Target node ID" className="flex-1 px-2 py-1 rounded text-xs focus:outline-none"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }} />
          <button onClick={findPath} className="t-btn px-2 py-1 text-xs rounded"
            style={{ background: 'var(--t-primary)', color: '#fff' }}>Find</button>
        </div>
        {pathResult && (
          <pre className="p-2 rounded text-[10px]" style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
            {JSON.stringify(pathResult, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};

export default KGAnalyticsPanel;
