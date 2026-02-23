import React, { useState, useEffect } from 'react';
import { KGNode } from '../../types/kg';
import * as api from '../../services/apiService';

interface Props {
  dbId: string;
  node?: KGNode | null;
  onSaved: (node: KGNode) => void;
  onClose: () => void;
}

const KGNodeEditor: React.FC<Props> = ({ dbId, node, onSaved, onClose }) => {
  const isEdit = !!node;
  const [name, setName] = useState(node?.name || '');
  const [type, setType] = useState(node?.type || 'entity');
  const [propsText, setPropsText] = useState(
    node?.properties ? JSON.stringify(node.properties, null, 2) : '{}'
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSave = async () => {
    if (!name.trim()) { setError('Name is required'); return; }
    let props: Record<string, any> = {};
    try { props = JSON.parse(propsText); } catch { setError('Invalid JSON'); return; }
    setSaving(true);
    setError('');
    try {
      let result;
      if (isEdit && node) {
        result = await api.updateKGNode(dbId, node.id, { name: name.trim(), type, properties: props });
      } else {
        result = await api.createKGNode(dbId, name.trim(), type, props);
      }
      onSaved(result);
    } catch (e: any) {
      setError(e.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="rounded-lg p-4 w-96 max-w-[90vw]" style={{ background: 'var(--t-surface)' }}
        onClick={e => e.stopPropagation()}>
        <h3 className="text-sm font-bold mb-3" style={{ color: 'var(--t-text)' }}>
          {isEdit ? 'Edit Node' : 'Create Node'}
        </h3>

        <div className="space-y-3">
          <div>
            <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Name</label>
            <input value={name} onChange={e => setName(e.target.value)}
              className="w-full px-3 py-1.5 rounded text-sm focus:outline-none"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}
              placeholder="Node name" />
          </div>

          <div>
            <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Type</label>
            <input value={type} onChange={e => setType(e.target.value)}
              className="w-full px-3 py-1.5 rounded text-sm focus:outline-none"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}
              placeholder="entity" />
          </div>

          <div>
            <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Properties (JSON)</label>
            <textarea value={propsText} onChange={e => setPropsText(e.target.value)}
              rows={4}
              className="w-full px-3 py-1.5 rounded text-xs font-mono focus:outline-none"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }} />
          </div>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <div className="flex gap-2 justify-end">
            <button onClick={onClose} className="t-btn px-3 py-1.5 text-xs rounded"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>Cancel</button>
            <button onClick={handleSave} disabled={saving}
              className="t-btn px-3 py-1.5 text-xs rounded"
              style={{ background: 'var(--t-primary)', color: '#fff' }}>
              {saving ? 'Saving...' : isEdit ? 'Update' : 'Create'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KGNodeEditor;
