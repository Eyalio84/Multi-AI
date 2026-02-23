import React, { useState, useEffect, useCallback } from 'react';
import { Expert } from '../types';
import * as api from '../services/apiService';
import ExpertList from '../components/experts/ExpertList';
import ExpertBuilder from '../components/experts/ExpertBuilder';
import ExpertChat from '../components/experts/ExpertChat';
import ExpertConfig from '../components/experts/ExpertConfig';
import ExpertAnalytics from '../components/experts/ExpertAnalytics';
import { showToast } from '../hooks/useToast';

type Tab = 'chat' | 'config' | 'analytics';

const ExpertsPage: React.FC = () => {
  const [experts, setExperts] = useState<Expert[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);
  const [editingExpert, setEditingExpert] = useState<Expert | null>(null);
  const [tab, setTab] = useState<Tab>('chat');

  const selectedExpert = experts.find(e => e.id === selectedId) || null;

  const loadExperts = useCallback(async () => {
    setLoading(true);
    try {
      const list = await api.listExperts();
      setExperts(list);
    } catch (e: any) {
      showToast(e.message || 'Failed to load experts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadExperts(); }, [loadExperts]);

  const handleCreate = () => {
    setEditingExpert(null);
    setBuilding(true);
  };

  const handleSelect = (id: string) => {
    setSelectedId(id);
    setBuilding(false);
    setTab('chat');
  };

  const handleSave = (expert: Expert) => {
    setBuilding(false);
    setEditingExpert(null);
    loadExperts().then(() => setSelectedId(expert.id));
    showToast('Expert saved');
  };

  const handleEdit = () => {
    if (selectedExpert) {
      setEditingExpert(selectedExpert);
      setBuilding(true);
    }
  };

  const handleDelete = async () => {
    if (!selectedExpert) return;
    if (!confirm(`Delete "${selectedExpert.name}"?`)) return;
    try {
      await api.deleteExpert(selectedExpert.id);
      setSelectedId(null);
      loadExperts();
      showToast('Expert deleted');
    } catch (e: any) {
      showToast(e.message || 'Failed to delete');
    }
  };

  const handleDuplicate = async () => {
    if (!selectedExpert) return;
    try {
      const dup = await api.duplicateExpert(selectedExpert.id);
      loadExperts().then(() => setSelectedId(dup.id));
      showToast('Expert duplicated');
    } catch (e: any) {
      showToast(e.message || 'Failed to duplicate');
    }
  };

  const TABS: { id: Tab; label: string }[] = [
    { id: 'chat', label: 'Chat' },
    { id: 'config', label: 'Config' },
    { id: 'analytics', label: 'Analytics' },
  ];

  return (
    <div className="flex h-full">
      {/* Left sidebar — expert list */}
      <div className="w-56 lg:w-64 flex-shrink-0">
        <ExpertList
          experts={experts}
          selectedId={selectedId}
          onSelect={handleSelect}
          onCreate={handleCreate}
          loading={loading}
        />
      </div>

      {/* Right content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {building ? (
          <ExpertBuilder
            expert={editingExpert}
            onSave={handleSave}
            onCancel={() => setBuilding(false)}
          />
        ) : selectedExpert ? (
          <>
            {/* Tab bar */}
            <div className="flex items-center gap-1 px-4 pt-3 pb-1">
              <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: selectedExpert.color }} />
              <span className="text-sm font-semibold mr-4 truncate" style={{ color: 'var(--t-text)' }}>
                {selectedExpert.name}
              </span>
              {TABS.map(t => (
                <button key={t.id} onClick={() => setTab(t.id)}
                  className="text-xs px-3 py-1.5 rounded transition-colors"
                  style={{
                    background: tab === t.id ? 'var(--t-primary)' : 'transparent',
                    color: tab === t.id ? '#fff' : 'var(--t-muted)',
                  }}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-hidden">
              {tab === 'chat' && <ExpertChat expert={selectedExpert} />}
              {tab === 'config' && (
                <ExpertConfig
                  expert={selectedExpert}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onDuplicate={handleDuplicate}
                />
              )}
              {tab === 'analytics' && <ExpertAnalytics expert={selectedExpert} />}
            </div>
          </>
        ) : (
          /* Empty state */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-3">
              <div className="text-4xl" style={{ color: 'var(--t-muted)' }}>
                <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div className="text-sm font-medium" style={{ color: 'var(--t-text)' }}>KG-OS Expert Builder</div>
              <div className="text-xs max-w-sm" style={{ color: 'var(--t-muted)' }}>
                Create AI experts backed by structured knowledge graphs with intent-driven retrieval,
                the 4-weight scoring formula, and 56 semantic dimensions.
              </div>
              <button onClick={handleCreate}
                className="text-xs px-4 py-2 rounded font-medium"
                style={{ background: 'var(--t-primary)', color: '#fff' }}>
                Create Your First Expert
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExpertsPage;
