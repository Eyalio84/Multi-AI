import React, { useState } from 'react';

interface KGNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
  x: number;
  y: number;
}

interface KGEdge {
  id: string;
  source: string;
  target: string;
  label: string;
}

const NODE_COLORS: Record<string, string> = {
  tool: '#3b82f6',
  capability: '#10b981',
  parameter: '#f59e0b',
  pattern: '#8b5cf6',
  use_case: '#ef4444',
  config: '#06b6d4',
  command: '#f97316',
  default: '#6b7280',
};

const KGStudioPage: React.FC = () => {
  const [nodes, setNodes] = useState<KGNode[]>([]);
  const [edges, setEdges] = useState<KGEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');

  // Demo nodes for preview
  const loadDemoGraph = () => {
    const demoNodes: KGNode[] = [
      { id: '1', label: 'Read Tool', type: 'tool', properties: { description: 'Read files from disk' }, x: 200, y: 150 },
      { id: '2', label: 'Write Tool', type: 'tool', properties: { description: 'Write files to disk' }, x: 400, y: 150 },
      { id: '3', label: 'Edit Tool', type: 'tool', properties: { description: 'Edit existing files' }, x: 300, y: 300 },
      { id: '4', label: 'File Operations', type: 'capability', properties: { category: 'filesystem' }, x: 300, y: 50 },
      { id: '5', label: 'Bash Tool', type: 'tool', properties: { description: 'Execute shell commands' }, x: 550, y: 200 },
      { id: '6', label: 'Glob Tool', type: 'tool', properties: { description: 'Find files by pattern' }, x: 100, y: 300 },
      { id: '7', label: 'Grep Tool', type: 'tool', properties: { description: 'Search file contents' }, x: 500, y: 350 },
      { id: '8', label: 'Code Search', type: 'use_case', properties: { goal: 'Find code patterns' }, x: 300, y: 450 },
    ];
    const demoEdges: KGEdge[] = [
      { id: 'e1', source: '4', target: '1', label: 'enables' },
      { id: 'e2', source: '4', target: '2', label: 'enables' },
      { id: 'e3', source: '4', target: '3', label: 'enables' },
      { id: 'e4', source: '1', target: '3', label: 'complements' },
      { id: 'e5', source: '6', target: '8', label: 'used_for' },
      { id: 'e6', source: '7', target: '8', label: 'used_for' },
      { id: 'e7', source: '5', target: '7', label: 'alternative_to' },
    ];
    setNodes(demoNodes);
    setEdges(demoEdges);
  };

  const filteredNodes = nodes.filter(n => {
    if (filterType !== 'all' && n.type !== filterType) return false;
    if (searchQuery && !n.label.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const nodeTypes = [...new Set(nodes.map(n => n.type))];

  return (
    <div className="flex flex-col lg:flex-row h-full">
      {/* Left panel — search + filters */}
      <div className="w-full lg:w-64 border-b lg:border-b-0 lg:border-r flex flex-col" style={{ borderColor: 'var(--t-border)' }}>
        <div className="p-2 border-b" style={{ borderColor: 'var(--t-border)' }}>
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search nodes..."
            className="w-full px-3 py-2 rounded text-sm focus:outline-none focus:ring-1"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', '--tw-ring-color': 'var(--t-primary)' } as React.CSSProperties}
          />
        </div>
        <div className="p-2 border-b flex flex-wrap gap-1" style={{ borderColor: 'var(--t-border)' }}>
          <button
            onClick={() => setFilterType('all')}
            className={`t-btn px-2 py-0.5 text-[10px] rounded`}
            style={filterType === 'all' ? { background: 'var(--t-primary)', color: 'var(--t-text)' } : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}
          >
            ALL
          </button>
          {nodeTypes.map(t => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`t-btn px-2 py-0.5 text-[10px] rounded`}
              style={filterType === t ? { background: 'var(--t-primary)', color: 'var(--t-text)' } : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="p-2 border-b" style={{ borderColor: 'var(--t-border)' }}>
          <button onClick={loadDemoGraph} className="t-btn w-full px-3 py-2 text-sm rounded" style={{ background: 'var(--t-accent1)', color: 'var(--t-text)' }}>
            Load Demo Graph
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {filteredNodes.map(n => (
            <button
              key={n.id}
              onClick={() => setSelectedNode(n)}
              className={`t-btn w-full text-left px-3 py-2 border-b`}
              style={{
                borderColor: 'var(--t-surface)',
                ...(selectedNode?.id === n.id ? { background: 'var(--t-surface2)' } : {}),
              }}
              onMouseEnter={e => { if (selectedNode?.id !== n.id) e.currentTarget.style.background = 'var(--t-surface2)'; }}
              onMouseLeave={e => { if (selectedNode?.id !== n.id) e.currentTarget.style.background = ''; }}
            >
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: NODE_COLORS[n.type] || NODE_COLORS.default }} />
                <span className="text-sm" style={{ color: 'var(--t-text2)' }}>{n.label}</span>
              </div>
              <span className="text-[10px]" style={{ color: 'var(--t-muted)' }}>{n.type}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative overflow-hidden" style={{ background: 'var(--t-bg)' }}>
        {nodes.length === 0 ? (
          <div className="flex items-center justify-center h-full" style={{ color: 'var(--t-muted)' }}>
            <div className="text-center">
              <p className="text-lg">KG Studio</p>
              <p className="text-sm mt-1">Load a demo graph or connect to a KG database</p>
            </div>
          </div>
        ) : (
          <svg className="w-full h-full" viewBox="0 0 700 500">
            {/* Edges */}
            {edges.map(e => {
              const source = nodes.find(n => n.id === e.source);
              const target = nodes.find(n => n.id === e.target);
              if (!source || !target) return null;
              return (
                <g key={e.id}>
                  <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="#4b5563" strokeWidth="1.5" markerEnd="url(#arrow)" />
                  <text x={(source.x + target.x) / 2} y={(source.y + target.y) / 2 - 5} fill="#6b7280" fontSize="9" textAnchor="middle">{e.label}</text>
                </g>
              );
            })}
            {/* Arrow marker */}
            <defs>
              <marker id="arrow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#4b5563" />
              </marker>
            </defs>
            {/* Nodes */}
            {filteredNodes.map(n => (
              <g key={n.id} onClick={() => setSelectedNode(n)} className="cursor-pointer">
                <circle cx={n.x} cy={n.y} r="20" fill={NODE_COLORS[n.type] || NODE_COLORS.default} opacity={selectedNode?.id === n.id ? 1 : 0.7} stroke={selectedNode?.id === n.id ? '#fff' : 'none'} strokeWidth="2" />
                <text x={n.x} y={n.y + 32} fill="#d1d5db" fontSize="10" textAnchor="middle">{n.label}</text>
              </g>
            ))}
          </svg>
        )}
      </div>

      {/* Right panel — node inspector */}
      {selectedNode && (
        <div className="t-card w-full lg:w-64 border-t lg:border-t-0 lg:border-l p-3" style={{ borderColor: 'var(--t-border)' }}>
          <h3 className="text-sm font-bold mb-2" style={{ color: 'var(--t-text)' }}>{selectedNode.label}</h3>
          <p className="text-xs mb-2" style={{ color: 'var(--t-muted)' }}>Type: <span style={{ color: 'var(--t-text2)' }}>{selectedNode.type}</span></p>
          <div className="space-y-1">
            {Object.entries(selectedNode.properties).map(([k, v]) => (
              <div key={k}>
                <span className="text-[10px]" style={{ color: 'var(--t-muted)' }}>{k}</span>
                <p className="text-xs" style={{ color: 'var(--t-text2)' }}>{String(v)}</p>
              </div>
            ))}
          </div>
          <div className="mt-3">
            <p className="text-[10px] mb-1" style={{ color: 'var(--t-muted)' }}>Connections</p>
            {edges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id).map(e => {
              const other = e.source === selectedNode.id ? nodes.find(n => n.id === e.target) : nodes.find(n => n.id === e.source);
              const direction = e.source === selectedNode.id ? '->' : '<-';
              return (
                <div key={e.id} className="text-xs" style={{ color: 'var(--t-muted)' }}>
                  {direction} {e.label} {direction} {other?.label}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default KGStudioPage;
