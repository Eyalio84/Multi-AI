import React, { useState } from 'react';
import { KGDatabaseStats } from '../../types/kg';
import * as api from '../../services/apiService';

interface Props {
  dbId: string | null;
  stats: KGDatabaseStats | null;
  onRefresh: () => void;
}

const KGBatchPanel: React.FC<Props> = ({ dbId, stats, onRefresh }) => {
  const [deleteType, setDeleteType] = useState('');
  const [oldType, setOldType] = useState('');
  const [newType, setNewType] = useState('');
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleDeleteByType = async () => {
    if (!dbId || !deleteType) return;
    if (!confirm(`Delete ALL nodes of type "${deleteType}" and their edges?`)) return;
    setLoading(true);
    try {
      const data = await api.batchDeleteByType(dbId, deleteType);
      setResult(`Deleted ${data.deleted} nodes`);
      onRefresh();
    } catch (e: any) {
      setResult(`Error: ${e.message}`);
    }
    setLoading(false);
  };

  const handleRetype = async () => {
    if (!dbId || !oldType || !newType) return;
    setLoading(true);
    try {
      const data = await api.batchRetype(dbId, oldType, newType);
      setResult(`Retyped ${data.updated} nodes from "${oldType}" to "${newType}"`);
      onRefresh();
    } catch (e: any) {
      setResult(`Error: ${e.message}`);
    }
    setLoading(false);
  };

  if (!dbId) return (
    <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--t-muted)' }}>
      Select a database for batch operations
    </div>
  );

  const nodeTypes = stats?.node_types || [];

  return (
    <div className="flex-1 overflow-y-auto p-3 space-y-4">
      <h3 className="text-sm font-bold" style={{ color: 'var(--t-text)' }}>Batch Operations</h3>

      {/* Delete by type */}
      <div className="p-3 rounded" style={{ background: 'var(--t-surface2)' }}>
        <p className="text-xs font-bold mb-2" style={{ color: 'var(--t-text)' }}>Delete All Nodes by Type</p>
        <div className="flex gap-2 items-center">
          <select value={deleteType} onChange={e => setDeleteType(e.target.value)}
            className="flex-1 px-2 py-1.5 rounded text-xs"
            style={{ background: 'var(--t-surface)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}>
            <option value="">Select type...</option>
            {nodeTypes.map(t => (
              <option key={t.type} value={t.type}>{t.type} ({t.count})</option>
            ))}
          </select>
          <button onClick={handleDeleteByType} disabled={loading || !deleteType}
            className="t-btn px-3 py-1.5 text-xs rounded"
            style={{ background: '#dc2626', color: '#fff', opacity: !deleteType ? 0.5 : 1 }}>
            Delete All
          </button>
        </div>
      </div>

      {/* Retype */}
      <div className="p-3 rounded" style={{ background: 'var(--t-surface2)' }}>
        <p className="text-xs font-bold mb-2" style={{ color: 'var(--t-text)' }}>Rename Node Type</p>
        <div className="flex gap-2 items-center">
          <select value={oldType} onChange={e => setOldType(e.target.value)}
            className="flex-1 px-2 py-1.5 rounded text-xs"
            style={{ background: 'var(--t-surface)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}>
            <option value="">From type...</option>
            {nodeTypes.map(t => (
              <option key={t.type} value={t.type}>{t.type} ({t.count})</option>
            ))}
          </select>
          <span className="text-xs" style={{ color: 'var(--t-muted)' }}>\u2192</span>
          <input value={newType} onChange={e => setNewType(e.target.value)}
            placeholder="New type"
            className="flex-1 px-2 py-1.5 rounded text-xs focus:outline-none"
            style={{ background: 'var(--t-surface)', color: 'var(--t-text)' }} />
          <button onClick={handleRetype} disabled={loading || !oldType || !newType}
            className="t-btn px-3 py-1.5 text-xs rounded"
            style={{ background: 'var(--t-primary)', color: '#fff', opacity: !oldType || !newType ? 0.5 : 1 }}>
            Rename
          </button>
        </div>
      </div>

      {result && (
        <p className="text-xs p-2 rounded" style={{
          background: 'var(--t-surface2)',
          color: result.startsWith('Error') ? '#ef4444' : 'var(--t-primary)',
        }}>{result}</p>
      )}
    </div>
  );
};

export default KGBatchPanel;
