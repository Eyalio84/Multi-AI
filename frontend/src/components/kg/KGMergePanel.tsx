import React, { useState } from 'react';
import { KGDatabase } from '../../types/kg';
import * as api from '../../services/apiService';

interface Props {
  databases: KGDatabase[];
  onMerged: () => void;
}

const KGMergePanel: React.FC<Props> = ({ databases, onMerged }) => {
  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');
  const [strategy, setStrategy] = useState<'union' | 'intersection'>('union');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const doMerge = async () => {
    if (!source || !target) return;
    if (source === target) { setError('Source and target must be different'); return; }
    if (!confirm(`Merge "${source}" into "${target}" using ${strategy} strategy? This modifies the target database.`)) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.mergeKGs(source, target, strategy);
      setResult(data);
      onMerged();
    } catch (e: any) {
      setError(e.message || 'Merge failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-3 space-y-4">
      <h3 className="text-sm font-bold" style={{ color: 'var(--t-text)' }}>Merge Knowledge Graphs</h3>
      <p className="text-xs" style={{ color: 'var(--t-muted)' }}>
        Merge nodes and edges from a source KG into a target KG. The target database will be modified.
      </p>

      <div className="space-y-3">
        <div>
          <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Source (read-only)</label>
          <select value={source} onChange={e => setSource(e.target.value)}
            className="w-full px-2 py-1.5 rounded text-sm"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}>
            <option value="">Select source...</option>
            {databases.map(db => (
              <option key={db.id} value={db.id}>{db.filename}</option>
            ))}
          </select>
        </div>

        <div className="text-center text-xs" style={{ color: 'var(--t-muted)' }}>\u2193 merges into \u2193</div>

        <div>
          <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Target (will be modified)</label>
          <select value={target} onChange={e => setTarget(e.target.value)}
            className="w-full px-2 py-1.5 rounded text-sm"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}>
            <option value="">Select target...</option>
            {databases.map(db => (
              <option key={db.id} value={db.id}>{db.filename}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-[10px] block mb-1" style={{ color: 'var(--t-muted)' }}>Strategy</label>
          <div className="flex gap-2">
            {(['union', 'intersection'] as const).map(s => (
              <button key={s} onClick={() => setStrategy(s)}
                className="t-btn px-3 py-1.5 text-xs rounded flex-1"
                style={strategy === s
                  ? { background: 'var(--t-primary)', color: '#fff' }
                  : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
          <p className="text-[10px] mt-1" style={{ color: 'var(--t-muted)' }}>
            {strategy === 'union' ? 'Add all nodes/edges from source to target (skip duplicates)' :
              'Only keep nodes/edges that exist in both'}
          </p>
        </div>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <button onClick={doMerge} disabled={loading || !source || !target}
        className="t-btn w-full px-4 py-2 rounded text-sm"
        style={{ background: '#dc2626', color: '#fff', opacity: !source || !target ? 0.5 : 1 }}>
        {loading ? 'Merging...' : 'Merge'}
      </button>

      {result && (
        <div className="p-3 rounded" style={{ background: 'var(--t-surface2)' }}>
          <p className="text-xs font-bold mb-1" style={{ color: 'var(--t-primary)' }}>Merge Complete</p>
          <pre className="text-[10px]" style={{ color: 'var(--t-text2)' }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default KGMergePanel;
