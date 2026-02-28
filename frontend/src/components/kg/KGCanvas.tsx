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
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  SimulationNodeDatum,
  SimulationLinkDatum,
} from 'd3-force';
import { KGNode, KGEdge, KGSubgraph } from '../../types/kg';
import { NODE_COLORS } from './KGSidebar';

interface SimNode extends SimulationNodeDatum {
  id: string;
}

interface SimLink extends SimulationLinkDatum<SimNode> {
  source: string;
  target: string;
}

// d3-force layout: physics-based node positioning
function forceLayout(nodes: KGNode[], edges: KGEdge[], width: number, height: number) {
  const nodeIdSet = new Set(nodes.map(n => n.id));
  const simNodes: SimNode[] = nodes.map(n => ({ id: n.id }));
  const simLinks: SimLink[] = edges
    .filter(e => nodeIdSet.has(e.source) && nodeIdSet.has(e.target))
    .map(e => ({ source: e.source, target: e.target }));

  const simulation = forceSimulation<SimNode>(simNodes)
    .force('link', forceLink<SimNode, SimLink>(simLinks).id(d => d.id).distance(120))
    .force('charge', forceManyBody<SimNode>().strength(-400))
    .force('center', forceCenter(width / 2, height / 2))
    .force('collide', forceCollide<SimNode>(40))
    .stop();

  // Run simulation synchronously (300 ticks to settle)
  for (let i = 0; i < 300; i++) {
    simulation.tick();
  }

  const positions: Record<string, { x: number; y: number }> = {};
  for (const node of simNodes) {
    positions[node.id] = {
      x: node.x ?? width / 2,
      y: node.y ?? height / 2,
    };
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
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

const KGCanvas: React.FC<Props> = ({ subgraph, selectedNodeId, onNodeClick, loading, isFullscreen, onToggleFullscreen }) => {
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState<Node>([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState<Edge>([]);
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

  const fullscreenBtn = onToggleFullscreen ? (
    <button
      onClick={onToggleFullscreen}
      className="absolute top-2 right-2 z-10 t-btn px-2 py-1 rounded text-xs"
      style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)', border: '1px solid var(--t-border)' }}
      title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
    >
      {isFullscreen ? '\u2716 Exit' : '\u26F6 Full'}
    </button>
  ) : null;

  if (!subgraph && !loading) {
    return (
      <div ref={containerRef} className="flex-1 flex items-center justify-center relative" style={{ background: 'var(--t-bg)', minHeight: '40vh' }}>
        {fullscreenBtn}
        <div className="text-center" style={{ color: 'var(--t-muted)' }}>
          <p className="text-lg">KG Studio</p>
          <p className="text-sm mt-1">Select a database and click a node to explore</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div ref={containerRef} className="flex-1 flex items-center justify-center relative" style={{ background: 'var(--t-bg)', minHeight: '40vh' }}>
        {fullscreenBtn}
        <div className="text-sm" style={{ color: 'var(--t-muted)' }}>Loading graph...</div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="flex-1 relative" style={{ background: 'var(--t-bg)', minHeight: '40vh' }}>
      {fullscreenBtn}
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
