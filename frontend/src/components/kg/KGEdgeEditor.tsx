import React, { useState, useEffect } from 'react';
import { KGEdge } from '../../types/kg';
import * as api from '../../services/apiService';

interface Props {
  dbId: string;
  sourceId?: string;
  targetId?: string;
  edge?: KGEdge | null; // Pass existing edge for edit mode
  onSaved: () => void;
  onClose: () => void;
}

const KGEdgeEditor: React.FC<Props> = ({ dbId, sourceId = '', targetId = '', edge, onSaved, onClose }) => {
  const isEdit = !!edge;
  const [source, setSource] = useState(edge?.source || sourceId);
  const [target, setTarget] = useState(edge?.target || targetId);
  const [type, setType] = useState(edge?.type || 'relates_to');
  const [propsText, setPropsText] = useState(edge ? JSON.stringify(edge.properties || {}, null, 2) : '{}');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (edge) {
      setSource(edge.source);
      setTarget(edge.target);
      setType(edge.type);
      setPropsText(JSON.stringify(edge.properties || {}, null, 2));
    }
  }, [edge]);

  const handleSave = async () => {
    if (!source.trim() || !target.trim()) { setError('Source and target are required'); return; }
    let props: Record<string, any> = {};
    try { props = JSON.parse(propsText); } catch { setError('Invalid JSON'); return; }
    setSaving(true);
    setError('');
    try {
      if (isEdit && edge) {
        await api.updateKGEdge(dbId, edge.id, { type, properties: props });
      } else {
        await api.createKGEdge(dbId, source.trim(), target.trim(), type, props);
      }
      onSaved();
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
          {isEdit ? 'Edit Edge' : 'Create Edge'}
        </h3>

        <div className="space-y-3">
          <div>
            <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Source Node ID</label>
            <input value={source} onChange={e => setSource(e.target.value)}
              disabled={isEdit}
              className="w-full px-3 py-1.5 rounded text-sm focus:outline-none"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', opacity: isEdit ? 0.6 : 1 }} />
          </div>
          <div>
            <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Target Node ID</label>
            <input value={target} onChange={e => setTarget(e.target.value)}
              disabled={isEdit}
              className="w-full px-3 py-1.5 rounded text-sm focus:outline-none"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', opacity: isEdit ? 0.6 : 1 }} />
          </div>
          <div>
            <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Relationship Type</label>
            <input value={type} onChange={e => setType(e.target.value)}
              className="w-full px-3 py-1.5 rounded text-sm focus:outline-none"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }} placeholder="relates_to" />
          </div>
          <div>
            <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Properties (JSON)</label>
            <textarea value={propsText} onChange={e => setPropsText(e.target.value)} rows={3}
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

export default KGEdgeEditor;
