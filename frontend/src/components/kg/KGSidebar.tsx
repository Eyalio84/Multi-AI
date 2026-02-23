import React, { useState, useEffect } from 'react';
import { KGDatabase, KGDatabaseStats, KGNode, KGNodePage, KGTypeCount } from '../../types/kg';
import KGDatabaseSelector from './KGDatabaseSelector';
import * as api from '../../services/apiService';

const NODE_COLORS: Record<string, string> = {
  tool: '#3b82f6', capability: '#10b981', parameter: '#f59e0b', pattern: '#8b5cf6',
  use_case: '#ef4444', config: '#06b6d4', command: '#f97316', entity: '#818cf8',
  concept: '#a78bfa', category: '#34d399', default: '#6b7280',
};

interface Props {
  databases: KGDatabase[];
  selectedDb: string | null;
  stats: KGDatabaseStats | null;
  onSelectDb: (dbId: string) => void;
  onSelectNode: (node: KGNode) => void;
  selectedNodeId: string | null;
  loading: boolean;
}

const KGSidebar: React.FC<Props> = ({
  databases, selectedDb, stats, onSelectDb, onSelectNode, selectedNodeId, loading,
}) => {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [nodes, setNodes] = useState<KGNode[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 50;

  useEffect(() => {
    if (!selectedDb) { setNodes([]); return; }
    setOffset(0);
    loadNodes(0);
  }, [selectedDb, filterType, search]);

  const loadNodes = async (off: number) => {
    if (!selectedDb) return;
    try {
      const page: KGNodePage = await api.listKGNodes(
        selectedDb,
        filterType === 'all' ? undefined : filterType,
        search || undefined,
        limit,
        off,
      );
      setNodes(off === 0 ? page.nodes : [...nodes, ...page.nodes]);
      setTotal(page.total);
      setOffset(off);
    } catch { /* ignore */ }
  };

  const nodeTypes: KGTypeCount[] = stats?.node_types || [];

  return (
    <div className="w-full lg:w-64 border-b lg:border-b-0 lg:border-r flex flex-col" style={{ borderColor: 'var(--t-border)' }}>
      <KGDatabaseSelector
        databases={databases}
        selected={selectedDb}
        stats={stats}
        onSelect={onSelectDb}
        loading={loading}
      />

      <div className="p-2 border-b" style={{ borderColor: 'var(--t-border)' }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search nodes..."
          className="w-full px-3 py-1.5 rounded text-sm focus:outline-none focus:ring-1"
          style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', '--tw-ring-color': 'var(--t-primary)' } as React.CSSProperties}
        />
      </div>

      <div className="p-2 border-b flex flex-wrap gap-1" style={{ borderColor: 'var(--t-border)' }}>
        <button
          onClick={() => setFilterType('all')}
          className="t-btn px-2 py-0.5 text-[10px] rounded"
          style={filterType === 'all'
            ? { background: 'var(--t-primary)', color: '#fff' }
            : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}
        >
          ALL ({stats?.node_count || 0})
        </button>
        {nodeTypes.map(t => (
          <button
            key={t.type}
            onClick={() => setFilterType(t.type)}
            className="t-btn px-2 py-0.5 text-[10px] rounded"
            style={filterType === t.type
              ? { background: NODE_COLORS[t.type] || NODE_COLORS.default, color: '#fff' }
              : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}
          >
            {t.type} ({t.count})
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto">
        {nodes.map(n => (
          <button
            key={n.id}
            onClick={() => onSelectNode(n)}
            className="t-btn w-full text-left px-3 py-1.5 border-b"
            style={{
              borderColor: 'var(--t-surface)',
              background: selectedNodeId === n.id ? 'var(--t-surface2)' : undefined,
            }}
          >
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: NODE_COLORS[n.type] || NODE_COLORS.default }} />
              <span className="text-xs truncate" style={{ color: 'var(--t-text2)' }}>{n.name}</span>
            </div>
            <span className="text-[10px] ml-4" style={{ color: 'var(--t-muted)' }}>{n.type}</span>
          </button>
        ))}
        {nodes.length < total && (
          <button
            onClick={() => loadNodes(offset + limit)}
            className="t-btn w-full py-2 text-xs"
            style={{ color: 'var(--t-primary)' }}
          >
            Load more ({total - nodes.length} remaining)
          </button>
        )}
        {selectedDb && nodes.length === 0 && !loading && (
          <p className="text-xs text-center p-4" style={{ color: 'var(--t-muted)' }}>No nodes found</p>
        )}
      </div>
    </div>
  );
};

export { NODE_COLORS };
export default KGSidebar;
