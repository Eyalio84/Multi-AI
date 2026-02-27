import React, { useState, useEffect, useCallback } from 'react';
import { Expert } from '../types';
import * as api from '../services/apiService';
import ExpertBuilder from '../components/experts/ExpertBuilder';
import ExpertChat from '../components/experts/ExpertChat';
import ExpertConfig from '../components/experts/ExpertConfig';
import ExpertAnalytics from '../components/experts/ExpertAnalytics';
import { showToast } from '../hooks/useToast';

type Tab = 'chat' | 'config' | 'analytics';

const TABS: { id: Tab; label: string }[] = [
  { id: 'chat', label: 'Chat' },
  { id: 'config', label: 'Config' },
  { id: 'analytics', label: 'Analytics' },
];

const ExpertsPage: React.FC = () => {
  const [experts, setExperts] = useState<Expert[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);
  const [editingExpert, setEditingExpert] = useState<Expert | null>(null);
  const [tab, setTab] = useState<Tab>('chat');
  const [pickerOpen, setPickerOpen] = useState(false);

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
    setPickerOpen(false);
  };

  const handleSelect = (id: string) => {
    setSelectedId(id);
    setBuilding(false);
    setTab('chat');
    setPickerOpen(false);
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

  // ── Builder mode: full-screen overlay ──
  if (building) {
    return (
      <div className="flex flex-col h-full">
        <ExpertBuilder
          expert={editingExpert}
          onSave={handleSave}
          onCancel={() => setBuilding(false)}
        />
      </div>
    );
  }

  // ── No expert selected: landing screen ──
  if (!selectedExpert) {
    return (
      <div className="flex flex-col h-full">
        {/* Top bar */}
        <div className="border-b px-3 py-2" style={{ borderColor: 'var(--t-border)' }}>
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-bold" style={{ color: 'var(--t-text)' }}>KG-OS Experts</span>
            <div className="flex items-center gap-2">
              {experts.length > 0 && (
                <div className="relative">
                  <button
                    onClick={() => setPickerOpen(!pickerOpen)}
                    className="px-2 py-1 rounded text-xs"
                    style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
                  >
                    {experts.length} expert{experts.length !== 1 ? 's' : ''} ▾
                  </button>
                  {pickerOpen && (
                    <>
                      <div className="fixed inset-0 z-30" onClick={() => setPickerOpen(false)} />
                      <div
                        className="absolute right-0 top-full mt-1 w-64 rounded-lg shadow-lg z-40 overflow-hidden max-h-[70vh] overflow-y-auto"
                        style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}
                      >
                        {experts.map(ex => (
                          <button
                            key={ex.id}
                            onClick={() => handleSelect(ex.id)}
                            className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm"
                            style={{ color: 'var(--t-text)' }}
                          >
                            <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: ex.color }} />
                            <span className="truncate flex-1">{ex.name}</span>
                            <span className="text-[10px] truncate max-w-[80px]" style={{ color: 'var(--t-muted)' }}>
                              {ex.kg_db_id}
                            </span>
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
              <button
                onClick={handleCreate}
                className="px-3 py-1 rounded text-xs font-medium"
                style={{ background: 'var(--t-primary)', color: '#fff' }}
              >
                + New
              </button>
            </div>
          </div>
        </div>

        {/* Landing */}
        <div className="flex-1 flex items-center justify-center px-6">
          <div className="text-center space-y-4 max-w-xs">
            <div style={{ color: 'var(--t-muted)' }}>
              <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div className="text-base font-semibold" style={{ color: 'var(--t-text)' }}>
              KG-OS Expert Builder
            </div>
            <div className="text-xs leading-relaxed" style={{ color: 'var(--t-muted)' }}>
              Create AI experts backed by structured knowledge graphs with intent-driven retrieval,
              the 4-weight scoring formula, and 56 semantic dimensions.
            </div>
            <button
              onClick={handleCreate}
              className="w-full px-4 py-2.5 rounded-lg text-sm font-medium"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
            >
              Create Your First Expert
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Expert selected: full-width workspace ──
  return (
    <div className="flex flex-col h-full">
      {/* Top bar: expert picker + actions */}
      <div className="border-b" style={{ borderColor: 'var(--t-border)' }}>
        <div className="flex items-center justify-between px-3 py-2 gap-2">
          {/* Left: expert picker */}
          <div className="flex items-center gap-2 min-w-0">
            <div className="relative">
              <button
                onClick={() => setPickerOpen(!pickerOpen)}
                className="flex items-center gap-1.5 px-2 py-1 rounded text-sm font-medium min-w-0"
                style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}
              >
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: selectedExpert.color }} />
                <span className="truncate max-w-[140px]">{selectedExpert.name}</span>
                <span style={{ color: 'var(--t-muted)' }}>▾</span>
              </button>
              {pickerOpen && (
                <>
                  <div className="fixed inset-0 z-30" onClick={() => setPickerOpen(false)} />
                  <div
                    className="absolute left-0 top-full mt-1 w-64 rounded-lg shadow-lg z-40 overflow-hidden max-h-[70vh] overflow-y-auto"
                    style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}
                  >
                    {experts.map(ex => (
                      <button
                        key={ex.id}
                        onClick={() => handleSelect(ex.id)}
                        className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm"
                        style={{
                          background: ex.id === selectedId ? 'var(--t-primary)' : 'transparent',
                          color: ex.id === selectedId ? '#fff' : 'var(--t-text)',
                        }}
                      >
                        <span
                          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                          style={{ background: ex.id === selectedId ? '#fff' : ex.color }}
                        />
                        <span className="truncate flex-1">{ex.name}</span>
                        <span
                          className="text-[10px] truncate max-w-[80px]"
                          style={{ color: ex.id === selectedId ? 'rgba(255,255,255,0.7)' : 'var(--t-muted)' }}
                        >
                          {ex.kg_db_id}
                        </span>
                      </button>
                    ))}
                    <button
                      onClick={handleCreate}
                      className="w-full px-3 py-2 text-left text-sm border-t"
                      style={{ borderColor: 'var(--t-border)', color: 'var(--t-primary)' }}
                    >
                      + New Expert
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Right: action buttons */}
          <div className="flex items-center gap-1 flex-shrink-0">
            <button
              onClick={handleEdit}
              className="px-2 py-1 rounded text-xs"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
            >
              Edit
            </button>
            <button
              onClick={handleDuplicate}
              className="px-2 py-1 rounded text-xs"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
            >
              Dup
            </button>
            <button
              onClick={handleDelete}
              className="px-2 py-1 rounded text-xs"
              style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}
            >
              Del
            </button>
            <button
              onClick={handleCreate}
              className="px-2 py-1 rounded text-xs font-medium"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
            >
              + New
            </button>
          </div>
        </div>

        {/* Tabs — horizontally scrollable */}
        <div
          className="flex items-center gap-0.5 px-2 pb-1.5 overflow-x-auto"
          style={{ WebkitOverflowScrolling: 'touch', scrollbarWidth: 'none' } as React.CSSProperties}
        >
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className="flex-shrink-0 px-3 py-1 rounded text-xs font-medium transition-colors"
              style={{
                background: tab === t.id ? 'var(--t-primary)' : 'transparent',
                color: tab === t.id ? '#fff' : 'var(--t-muted)',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content — fills remaining space */}
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
    </div>
  );
};

export default ExpertsPage;
