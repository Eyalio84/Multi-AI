import React from 'react';
import { KGNode, KGEdge } from '../../types/kg';
import { NODE_COLORS } from './KGSidebar';

interface Props {
  node: KGNode | null;
  edges: KGEdge[];
  allNodes: KGNode[];
  onNavigate: (nodeId: string) => void;
  onEdit?: (node: KGNode) => void;
  onDelete?: (nodeId: string) => void;
}

const KGInspector: React.FC<Props> = ({ node, edges, allNodes, onNavigate, onEdit, onDelete }) => {
  if (!node) return null;

  const connected = edges.filter(e => e.source === node.id || e.target === node.id);
  const nodeMap = Object.fromEntries(allNodes.map(n => [n.id, n]));

  return (
    <div className="w-full lg:w-72 border-t lg:border-t-0 lg:border-l p-3 overflow-y-auto"
      style={{ borderColor: 'var(--t-border)' }}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <span className="h-3 w-3 rounded-full flex-shrink-0"
          style={{ backgroundColor: NODE_COLORS[node.type] || NODE_COLORS.default }} />
        <h3 className="text-sm font-bold truncate" style={{ color: 'var(--t-text)' }}>{node.name}</h3>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <span className="text-[10px] px-1.5 py-0.5 rounded"
          style={{ background: NODE_COLORS[node.type] || NODE_COLORS.default, color: '#fff' }}>{node.type}</span>
        <span className="text-[10px]" style={{ color: 'var(--t-muted)' }}>ID: {node.id}</span>
      </div>

      {/* Actions */}
      {(onEdit || onDelete) && (
        <div className="flex gap-1 mb-3">
          {onEdit && (
            <button onClick={() => onEdit(node)}
              className="t-btn px-2 py-1 text-[10px] rounded"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
              Edit
            </button>
          )}
          {onDelete && (
            <button onClick={() => { if (confirm(`Delete "${node.name}"?`)) onDelete(node.id); }}
              className="t-btn px-2 py-1 text-[10px] rounded"
              style={{ background: '#7f1d1d', color: '#fca5a5' }}>
              Delete
            </button>
          )}
        </div>
      )}

      {/* Properties */}
      {Object.keys(node.properties).length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] font-bold mb-1" style={{ color: 'var(--t-muted)' }}>Properties</p>
          <div className="space-y-1">
            {Object.entries(node.properties).map(([k, v]) => (
              <div key={k} className="text-xs">
                <span style={{ color: 'var(--t-muted)' }}>{k}: </span>
                <span style={{ color: 'var(--t-text2)' }}>
                  {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connections */}
      <div>
        <p className="text-[10px] font-bold mb-1" style={{ color: 'var(--t-muted)' }}>
          Connections ({connected.length})
        </p>
        <div className="space-y-1">
          {connected.map(e => {
            const isOutgoing = e.source === node.id;
            const otherId = isOutgoing ? e.target : e.source;
            const other = nodeMap[otherId];
            return (
              <button
                key={e.id}
                onClick={() => onNavigate(otherId)}
                className="t-btn w-full text-left px-2 py-1 rounded text-xs flex items-center gap-1"
                style={{ background: 'var(--t-surface2)' }}
              >
                <span style={{ color: 'var(--t-muted)' }}>{isOutgoing ? '\u2192' : '\u2190'}</span>
                <span style={{ color: 'var(--t-primary)' }}>{e.type}</span>
                <span style={{ color: 'var(--t-muted)' }}>{isOutgoing ? '\u2192' : '\u2190'}</span>
                <span className="truncate" style={{ color: 'var(--t-text2)' }}>{other?.name || otherId}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default KGInspector;
