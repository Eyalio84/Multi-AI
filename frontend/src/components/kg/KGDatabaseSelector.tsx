import React from 'react';
import { KGDatabase, KGDatabaseStats } from '../../types/kg';

interface Props {
  databases: KGDatabase[];
  selected: string | null;
  stats: KGDatabaseStats | null;
  onSelect: (dbId: string) => void;
  loading: boolean;
}

const KGDatabaseSelector: React.FC<Props> = ({ databases, selected, stats, onSelect, loading }) => (
  <div className="p-2 border-b" style={{ borderColor: 'var(--t-border)' }}>
    <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Database</label>
    <select
      value={selected || ''}
      onChange={e => onSelect(e.target.value)}
      disabled={loading}
      className="w-full px-2 py-1.5 rounded text-sm focus:outline-none"
      style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
    >
      <option value="">Select a KG...</option>
      {databases.map(db => (
        <option key={db.id} value={db.id}>{db.filename} ({db.size_mb}MB)</option>
      ))}
    </select>
    {stats && (
      <div className="mt-1.5 flex gap-2 text-[10px]" style={{ color: 'var(--t-muted)' }}>
        <span>{stats.node_count} nodes</span>
        <span>{stats.edge_count} edges</span>
        <span className="px-1 rounded" style={{ background: 'var(--t-surface2)' }}>{stats.profile}</span>
      </div>
    )}
  </div>
);

export default KGDatabaseSelector;
