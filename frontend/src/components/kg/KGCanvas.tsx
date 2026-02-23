import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
  NodeMouseHandler,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { KGNode, KGEdge, KGSubgraph } from '../../types/kg';
import { NODE_COLORS } from './KGSidebar';

// Force simulation (inline d3-force-like algorithm)
function forceLayout(nodes: KGNode[], edges: KGEdge[], width: number, height: number) {
  const positions: Record<string, { x: number; y: number; vx: number; vy: number }> = {};
  const idSet = new Set(nodes.map(n => n.id));

  // Initialize random positions
  nodes.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / nodes.length;
    const radius = Math.min(width, height) * 0.35;
    positions[n.id] = {
      x: width / 2 + radius * Math.cos(angle) + (Math.random() - 0.5) * 40,
      y: height / 2 + radius * Math.sin(angle) + (Math.random() - 0.5) * 40,
      vx: 0, vy: 0,
    };
  });

  // Simple force simulation: repulsion + attraction + centering
  const iterations = 80;
  const repulsionK = 3000;
  const attractionK = 0.008;
  const damping = 0.85;

  for (let iter = 0; iter < iterations; iter++) {
    const temp = 1 - iter / iterations;
    // Repulsion between all nodes
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = positions[nodes[i].id];
        const b = positions[nodes[j].id];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (repulsionK * temp) / (dist * dist);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx; a.vy += fy;
        b.vx -= fx; b.vy -= fy;
      }
    }
    // Attraction along edges
    edges.forEach(e => {
      if (!positions[e.source] || !positions[e.target]) return;
      const a = positions[e.source];
      const b = positions[e.target];
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = dist * attractionK;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    });
    // Center gravity
    nodes.forEach(n => {
      const p = positions[n.id];
      p.vx += (width / 2 - p.x) * 0.001;
      p.vy += (height / 2 - p.y) * 0.001;
    });
    // Update positions
    nodes.forEach(n => {
      const p = positions[n.id];
      p.vx *= damping;
      p.vy *= damping;
      p.x += p.vx;
      p.y += p.vy;
      p.x = Math.max(40, Math.min(width - 40, p.x));
      p.y = Math.max(40, Math.min(height - 40, p.y));
    });
  }

  return positions;
}

// Custom node component
function KGGraphNode({ data }: { data: { label: string; nodeType: string; selected: boolean } }) {
  const color = NODE_COLORS[data.nodeType] || NODE_COLORS.default;
  return (
    <div
      style={{
        background: color,
        border: data.selected ? '2px solid #fff' : '2px solid transparent',
        borderRadius: 8,
        padding: '4px 10px',
        fontSize: 11,
        color: '#fff',
        maxWidth: 160,
        textAlign: 'center',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        boxShadow: data.selected ? `0 0 8px ${color}` : 'none',
        opacity: 0.9,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ visibility: 'hidden' }} />
      {data.label}
      <Handle type="source" position={Position.Bottom} style={{ visibility: 'hidden' }} />
    </div>
  );
}

const nodeTypes = { kgNode: KGGraphNode };

interface Props {
  subgraph: KGSubgraph | null;
  selectedNodeId: string | null;
  onNodeClick: (nodeId: string) => void;
  loading: boolean;
}

const KGCanvas: React.FC<Props> = ({ subgraph, selectedNodeId, onNodeClick, loading }) => {
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!subgraph || subgraph.nodes.length === 0) {
      setRfNodes([]);
      setRfEdges([]);
      return;
    }

    const w = containerRef.current?.clientWidth || 800;
    const h = containerRef.current?.clientHeight || 600;
    const positions = forceLayout(subgraph.nodes, subgraph.edges, w, h);

    const newNodes: Node[] = subgraph.nodes.map(n => ({
      id: n.id,
      type: 'kgNode',
      position: { x: positions[n.id]?.x || 0, y: positions[n.id]?.y || 0 },
      data: { label: n.name, nodeType: n.type, selected: n.id === selectedNodeId },
    }));

    const nodeIdSet = new Set(subgraph.nodes.map(n => n.id));
    const newEdges: Edge[] = subgraph.edges
      .filter(e => nodeIdSet.has(e.source) && nodeIdSet.has(e.target))
      .map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.type,
        type: 'default',
        animated: false,
        style: { stroke: '#4b5563', strokeWidth: 1.5 },
        labelStyle: { fontSize: 9, fill: '#9ca3af' },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#4b5563', width: 12, height: 12 },
      }));

    setRfNodes(newNodes);
    setRfEdges(newEdges);
  }, [subgraph, selectedNodeId]);

  const handleNodeClick: NodeMouseHandler = useCallback((_event, node) => {
    onNodeClick(node.id);
  }, [onNodeClick]);

  if (!subgraph && !loading) {
    return (
      <div ref={containerRef} className="flex-1 flex items-center justify-center" style={{ background: 'var(--t-bg)' }}>
        <div className="text-center" style={{ color: 'var(--t-muted)' }}>
          <p className="text-lg">KG Studio</p>
          <p className="text-sm mt-1">Select a database and click a node to explore</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div ref={containerRef} className="flex-1 flex items-center justify-center" style={{ background: 'var(--t-bg)' }}>
        <div className="text-sm" style={{ color: 'var(--t-muted)' }}>Loading graph...</div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="flex-1" style={{ background: 'var(--t-bg)' }}>
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        maxZoom={3}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1f2937" gap={20} />
        <Controls position="bottom-right" />
        <MiniMap
          nodeColor={n => NODE_COLORS[(n.data as any)?.nodeType] || '#6b7280'}
          maskColor="rgba(0,0,0,0.6)"
          style={{ background: '#111827' }}
        />
      </ReactFlow>
    </div>
  );
};

export default KGCanvas;
