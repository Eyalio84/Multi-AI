import React, { useState, useEffect, useCallback } from 'react';
import { KGDatabase, KGDatabaseStats, KGNode, KGEdge, KGEdgePage, KGSubgraph, KGTab } from '../types/kg';
import * as api from '../services/apiService';
import { showToast } from '../hooks/useToast';
import KGSidebar from '../components/kg/KGSidebar';
import KGCanvas from '../components/kg/KGCanvas';
import KGInspector from '../components/kg/KGInspector';
import KGSearchPanel from '../components/kg/KGSearchPanel';
import KGNodeEditor from '../components/kg/KGNodeEditor';
import KGEdgeEditor from '../components/kg/KGEdgeEditor';
import KGIngestPanel from '../components/kg/KGIngestPanel';
import KGCreateDialog from '../components/kg/KGCreateDialog';
import KGAnalyticsPanel from '../components/kg/KGAnalyticsPanel';
import KGRagChat from '../components/kg/KGRagChat';
import KGComparePanel from '../components/kg/KGComparePanel';
import KGMergePanel from '../components/kg/KGMergePanel';
import KGEmbeddingDashboard from '../components/kg/KGEmbeddingDashboard';
import KGBatchPanel from '../components/kg/KGBatchPanel';

const TABS: { id: KGTab; label: string }[] = [
  { id: 'explore', label: 'Explore' },
  { id: 'search', label: 'Search' },
  { id: 'edit', label: 'Edit' },
  { id: 'ingest', label: 'Ingest' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'chat', label: 'RAG Chat' },
  { id: 'compare', label: 'Compare' },
  { id: 'merge', label: 'Merge' },
  { id: 'embeddings', label: 'Embeddings' },
  { id: 'batch', label: 'Batch' },
];

const KGStudioPage: React.FC = () => {
  const [databases, setDatabases] = useState<KGDatabase[]>([]);
  const [selectedDb, setSelectedDb] = useState<string | null>(null);
  const [stats, setStats] = useState<KGDatabaseStats | null>(null);
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);
  const [subgraph, setSubgraph] = useState<KGSubgraph | null>(null);
  const [tab, setTab] = useState<KGTab>('explore');
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingNode, setEditingNode] = useState<KGNode | null | undefined>(undefined);
  const [showEdgeEditor, setShowEdgeEditor] = useState(false);
  const [editingEdge, setEditingEdge] = useState<KGEdge | null>(null);
  const [canvasFullscreen, setCanvasFullscreen] = useState(false);
  // Edge browser state
  const [edgeBrowserEdges, setEdgeBrowserEdges] = useState<KGEdge[]>([]);
  const [edgeBrowserTotal, setEdgeBrowserTotal] = useState(0);
  const [edgeBrowserOffset, setEdgeBrowserOffset] = useState(0);
  const [edgeBrowserFilter, setEdgeBrowserFilter] = useState('all');
  const edgeBrowserLimit = 50;

  // Load database list on mount
  useEffect(() => {
    loadDatabases();
  }, []);

  const loadDatabases = async () => {
    try {
      const dbs = await api.listKGDatabases();
      setDatabases(dbs);
    } catch (e: any) { showToast(e.message || 'Failed to load databases'); }
  };

  // Load stats when database changes
  useEffect(() => {
    if (!selectedDb) { setStats(null); setSubgraph(null); setSelectedNode(null); return; }
    loadStats();
  }, [selectedDb]);

  const loadStats = async () => {
    if (!selectedDb) return;
    setLoading(true);
    try {
      const s = await api.getKGStats(selectedDb);
      setStats(s);
    } catch (e: any) { showToast(e.message || 'Failed to load stats'); }
    setLoading(false);
  };

  const handleSelectDb = useCallback((dbId: string) => {
    setSelectedDb(dbId);
    setSelectedNode(null);
    setSubgraph(null);
  }, []);

  const handleSelectNode = useCallback(async (node: KGNode) => {
    setSelectedNode(node);
    if (!selectedDb) return;
    setLoading(true);
    try {
      const sg = await api.getKGNeighbors(selectedDb, node.id, 1, 50);
      setSubgraph(sg);
    } catch (e: any) { showToast(e.message || 'Failed to load neighbors'); }
    setLoading(false);
  }, [selectedDb]);

  const handleCanvasNodeClick = useCallback(async (nodeId: string) => {
    if (!selectedDb) return;
    try {
      const node = await api.getKGNode(selectedDb, nodeId);
      if (node) {
        setSelectedNode(node);
        const sg = await api.getKGNeighbors(selectedDb, nodeId, 1, 50);
        setSubgraph(sg);
      }
    } catch (e: any) { showToast(e.message || 'Failed to load node'); }
  }, [selectedDb]);

  const handleDeleteNode = useCallback(async (nodeId: string) => {
    if (!selectedDb) return;
    try {
      await api.deleteKGNode(selectedDb, nodeId);
      setSelectedNode(null);
      setSubgraph(null);
      loadStats();
    } catch (e: any) { showToast(e.message || 'Failed to delete node'); }
  }, [selectedDb]);

  const handleNodeSaved = useCallback(async (node: KGNode) => {
    setEditingNode(undefined);
    setSelectedNode(node);
    if (selectedDb) {
      const sg = await api.getKGNeighbors(selectedDb, node.id, 1, 50);
      setSubgraph(sg);
    }
    loadStats();
  }, [selectedDb]);

  const handleDbCreated = useCallback(() => {
    setShowCreateDialog(false);
    loadDatabases();
  }, []);

  // Edge handlers
  const handleEditEdge = useCallback((edge: KGEdge) => {
    setEditingEdge(edge);
    setShowEdgeEditor(true);
  }, []);

  const handleDeleteEdge = useCallback(async (edgeId: string) => {
    if (!selectedDb) return;
    try {
      await api.deleteKGEdge(selectedDb, edgeId);
      // Refresh subgraph if viewing a node
      if (selectedNode) {
        const sg = await api.getKGNeighbors(selectedDb, selectedNode.id, 1, 50);
        setSubgraph(sg);
      }
      loadStats();
      loadEdges(0);
    } catch (e: any) { showToast(e.message || 'Failed to delete edge'); }
  }, [selectedDb, selectedNode]);

  const handleEdgeSaved = useCallback(() => {
    setShowEdgeEditor(false);
    setEditingEdge(null);
    loadStats();
    loadEdges(edgeBrowserOffset);
    // Refresh subgraph if viewing a node
    if (selectedDb && selectedNode) {
      api.getKGNeighbors(selectedDb, selectedNode.id, 1, 50).then(sg => setSubgraph(sg)).catch(() => {});
    }
  }, [selectedDb, selectedNode, edgeBrowserOffset]);

  // Edge browser loader
  const loadEdges = useCallback(async (off: number) => {
    if (!selectedDb) { setEdgeBrowserEdges([]); return; }
    try {
      const page: KGEdgePage = await api.listKGEdges(
        selectedDb,
        edgeBrowserFilter === 'all' ? undefined : edgeBrowserFilter,
        edgeBrowserLimit,
        off,
      );
      setEdgeBrowserEdges(off === 0 ? page.edges : [...edgeBrowserEdges, ...page.edges]);
      setEdgeBrowserTotal(page.total);
      setEdgeBrowserOffset(off);
    } catch (e: any) { showToast(e.message || 'Failed to load edges'); }
  }, [selectedDb, edgeBrowserFilter, edgeBrowserEdges]);

  // Load edges when db or filter changes (only on edit tab)
  useEffect(() => {
    if (tab === 'edit' && selectedDb) {
      setEdgeBrowserOffset(0);
      loadEdges(0);
    }
  }, [selectedDb, edgeBrowserFilter, tab]);

  // Render the active tab content
  const renderTabContent = () => {
    switch (tab) {
      case 'explore':
        return (
          <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
            <KGCanvas
              subgraph={subgraph}
              selectedNodeId={selectedNode?.id || null}
              onNodeClick={handleCanvasNodeClick}
              loading={loading}
              isFullscreen={canvasFullscreen}
              onToggleFullscreen={() => setCanvasFullscreen(f => !f)}
            />
            {!canvasFullscreen && (
              <KGInspector
                node={selectedNode}
                edges={subgraph?.edges || []}
                allNodes={subgraph?.nodes || []}
                onNavigate={handleCanvasNodeClick}
                onEdit={(n) => setEditingNode(n)}
                onDelete={handleDeleteNode}
                onEditEdge={handleEditEdge}
                onDeleteEdge={handleDeleteEdge}
              />
            )}
          </div>
        );
      case 'search':
        return <KGSearchPanel dbId={selectedDb} databases={databases} onSelectNode={handleSelectNode} />;
      case 'edit':
        return (
          <div className="flex-1 flex flex-col p-3 gap-3 overflow-hidden">
            <div className="flex gap-2">
              <button onClick={() => setEditingNode(null)}
                className="t-btn px-3 py-1.5 text-xs rounded"
                style={{ background: 'var(--t-primary)', color: '#fff' }}>
                + New Node
              </button>
              <button onClick={() => { setEditingEdge(null); setShowEdgeEditor(true); }}
                className="t-btn px-3 py-1.5 text-xs rounded"
                style={{ background: 'var(--t-accent1, var(--t-primary))', color: '#fff' }}>
                + New Edge
              </button>
              <button onClick={() => setShowCreateDialog(true)}
                className="t-btn px-3 py-1.5 text-xs rounded"
                style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
                + New Database
              </button>
            </div>
            {selectedNode && (
              <div className="p-3 rounded" style={{ background: 'var(--t-surface2)' }}>
                <p className="text-xs" style={{ color: 'var(--t-muted)' }}>Selected: </p>
                <p className="text-sm font-bold" style={{ color: 'var(--t-text)' }}>{selectedNode.name}</p>
                <p className="text-xs" style={{ color: 'var(--t-muted)' }}>ID: {selectedNode.id} | Type: {selectedNode.type}</p>
                <div className="flex gap-2 mt-2">
                  <button onClick={() => setEditingNode(selectedNode)}
                    className="t-btn px-2 py-1 text-[10px] rounded"
                    style={{ background: 'var(--t-primary)', color: '#fff' }}>Edit</button>
                  <button onClick={() => handleDeleteNode(selectedNode.id)}
                    className="t-btn px-2 py-1 text-[10px] rounded"
                    style={{ background: '#7f1d1d', color: '#fca5a5' }}>Delete</button>
                  <button onClick={() => { setEditingEdge(null); setShowEdgeEditor(true); }}
                    className="t-btn px-2 py-1 text-[10px] rounded"
                    style={{ background: 'var(--t-surface)', color: 'var(--t-text2)' }}>Add Edge From</button>
                </div>
              </div>
            )}
            {/* Edge Browser */}
            {selectedDb && (
              <div className="flex-1 flex flex-col overflow-hidden">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-bold" style={{ color: 'var(--t-text)' }}>
                    Edges ({edgeBrowserTotal})
                  </p>
                  <div className="flex gap-1 flex-wrap">
                    <button onClick={() => setEdgeBrowserFilter('all')}
                      className="t-btn px-2 py-0.5 text-[10px] rounded"
                      style={edgeBrowserFilter === 'all'
                        ? { background: 'var(--t-primary)', color: '#fff' }
                        : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
                      ALL
                    </button>
                    {(stats?.edge_types || []).map(t => (
                      <button key={t.type} onClick={() => setEdgeBrowserFilter(t.type)}
                        className="t-btn px-2 py-0.5 text-[10px] rounded"
                        style={edgeBrowserFilter === t.type
                          ? { background: 'var(--t-primary)', color: '#fff' }
                          : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}>
                        {t.type} ({t.count})
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto space-y-1">
                  {edgeBrowserEdges.map(e => (
                    <div key={e.id} className="flex items-center gap-2 px-2 py-1.5 rounded text-xs"
                      style={{ background: 'var(--t-surface2)' }}>
                      <span className="truncate max-w-[80px]" style={{ color: 'var(--t-text2)' }}
                        title={e.source}>{e.source}</span>
                      <span className="flex-shrink-0 px-1.5 py-0.5 rounded text-[10px]"
                        style={{ background: 'var(--t-primary)', color: '#fff' }}>{e.type}</span>
                      <span className="truncate max-w-[80px]" style={{ color: 'var(--t-text2)' }}
                        title={e.target}>{e.target}</span>
                      <div className="ml-auto flex gap-1 flex-shrink-0">
                        <button onClick={() => handleEditEdge(e)} title="Edit"
                          className="t-btn text-[10px] px-1 rounded"
                          style={{ color: 'var(--t-muted)' }}>&#9998;</button>
                        <button onClick={() => { if (confirm(`Delete edge "${e.type}"?`)) handleDeleteEdge(e.id); }}
                          title="Delete" className="t-btn text-[10px] px-1 rounded"
                          style={{ color: '#fca5a5' }}>&times;</button>
                      </div>
                    </div>
                  ))}
                  {edgeBrowserEdges.length < edgeBrowserTotal && (
                    <button onClick={() => loadEdges(edgeBrowserOffset + edgeBrowserLimit)}
                      className="t-btn w-full py-2 text-xs"
                      style={{ color: 'var(--t-primary)' }}>
                      Load more ({edgeBrowserTotal - edgeBrowserEdges.length} remaining)
                    </button>
                  )}
                  {edgeBrowserEdges.length === 0 && (
                    <p className="text-xs text-center py-4" style={{ color: 'var(--t-muted)' }}>No edges found</p>
                  )}
                </div>
              </div>
            )}
            {!selectedDb && (
              <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--t-muted)' }}>
                Select a database to edit
              </div>
            )}
          </div>
        );
      case 'ingest':
        return <KGIngestPanel dbId={selectedDb} />;
      case 'analytics':
        return <KGAnalyticsPanel dbId={selectedDb} onSelectNode={handleSelectNode} />;
      case 'chat':
        return <KGRagChat dbId={selectedDb} />;
      case 'compare':
        return <KGComparePanel databases={databases} />;
      case 'merge':
        return <KGMergePanel databases={databases} onMerged={loadDatabases} />;
      case 'embeddings':
        return <KGEmbeddingDashboard dbId={selectedDb} />;
      case 'batch':
        return <KGBatchPanel dbId={selectedDb} stats={stats} onRefresh={loadStats} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="border-b flex overflow-x-auto" style={{ borderColor: 'var(--t-border)' }}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => { setTab(t.id); setCanvasFullscreen(false); }}
            className="t-btn px-3 py-2 text-xs whitespace-nowrap border-b-2"
            style={{
              borderColor: tab === t.id ? 'var(--t-primary)' : 'transparent',
              color: tab === t.id ? 'var(--t-primary)' : 'var(--t-text2)',
              background: tab === t.id ? 'var(--t-surface2)' : undefined,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Sidebar (hidden when canvas is fullscreen) */}
        {!canvasFullscreen && ['explore', 'search', 'edit', 'analytics', 'chat', 'ingest', 'embeddings', 'batch'].includes(tab) && (
          <KGSidebar
            databases={databases}
            selectedDb={selectedDb}
            stats={stats}
            onSelectDb={handleSelectDb}
            onSelectNode={handleSelectNode}
            selectedNodeId={selectedNode?.id || null}
            loading={loading}
          />
        )}

        {/* Tab content */}
        {renderTabContent()}
      </div>

      {/* Modals */}
      {editingNode !== undefined && selectedDb && (
        <KGNodeEditor
          dbId={selectedDb}
          node={editingNode}
          onSaved={handleNodeSaved}
          onClose={() => setEditingNode(undefined)}
        />
      )}
      {showEdgeEditor && selectedDb && (
        <KGEdgeEditor
          dbId={selectedDb}
          sourceId={selectedNode?.id}
          edge={editingEdge}
          onSaved={handleEdgeSaved}
          onClose={() => { setShowEdgeEditor(false); setEditingEdge(null); }}
        />
      )}
      {showCreateDialog && (
        <KGCreateDialog
          onCreated={handleDbCreated}
          onClose={() => setShowCreateDialog(false)}
        />
      )}
    </div>
  );
};

export default KGStudioPage;
