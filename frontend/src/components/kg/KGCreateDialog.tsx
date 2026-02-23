import React, { useState } from 'react';
import * as api from '../../services/apiService';

interface Props {
  onCreated: (db: { id: string; filename: string }) => void;
  onClose: () => void;
}

const KGCreateDialog: React.FC<Props> = ({ onCreated, onClose }) => {
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  const handleCreate = async () => {
    if (!name.trim()) { setError('Name is required'); return; }
    setCreating(true);
    setError('');
    try {
      const db = await api.createKGDatabase(name.trim());
      onCreated(db);
    } catch (e: any) {
      setError(e.message || 'Failed to create database');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="rounded-lg p-4 w-80" style={{ background: 'var(--t-surface)' }}
        onClick={e => e.stopPropagation()}>
        <h3 className="text-sm font-bold mb-3" style={{ color: 'var(--t-text)' }}>Create New KG</h3>
        <div className="space-y-3">
          <div>
            <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Database Name</label>
            <input value={name} onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
              className="w-full px-3 py-1.5 rounded text-sm focus:outline-none"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}
              placeholder="my-knowledge-graph" autoFocus />
            <p className="text-[10px] mt-1" style={{ color: 'var(--t-muted)' }}>
              Letters, numbers, hyphens, underscores only
            </p>
          </div>
          {error && <p className="text-xs text-red-400">{error}</p>}
          <div className="flex gap-2 justify-end">
            <button onClick={onClose} className="t-btn px-3 py-1.5 text-xs rounded"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>Cancel</button>
            <button onClick={handleCreate} disabled={creating}
              className="t-btn px-3 py-1.5 text-xs rounded"
              style={{ background: 'var(--t-primary)', color: '#fff' }}>
              {creating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KGCreateDialog;
