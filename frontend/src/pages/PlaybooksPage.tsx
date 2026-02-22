import React, { useState, useEffect } from 'react';
import * as apiService from '../services/apiService';
import { PlaybookMeta } from '../types/index';

const difficultyColors: Record<string, string> = {
  beginner: 'bg-green-700',
  intermediate: 'bg-yellow-700',
  advanced: 'bg-orange-700',
  expert: 'bg-red-700',
};

const PlaybooksPage: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<PlaybookMeta[]>([]);
  const [categories, setCategories] = useState<{ name: string; count: number }[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPlaybook, setSelectedPlaybook] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiService.listPlaybooks().then(data => setPlaybooks(data.playbooks || [])).catch(() => {});
    apiService.listPlaybookCategories().then(data => setCategories(data.categories || [])).catch(() => {});
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      const data = await apiService.listPlaybooks();
      setPlaybooks(data.playbooks || []);
      return;
    }
    const data = await apiService.searchPlaybooks(searchQuery, selectedCategory || undefined);
    setPlaybooks(data.results || []);
  };

  const handleSelectPlaybook = async (filename: string) => {
    setLoading(true);
    try {
      const data = await apiService.getPlaybook(filename);
      setSelectedPlaybook(data);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { handleSearch(); }, [searchQuery, selectedCategory]);

  return (
    <div className="flex flex-col lg:flex-row h-full">
      {/* Playbook list */}
      <div className="w-full lg:w-80 border-b lg:border-b-0 lg:border-r flex flex-col" style={{ borderColor: 'var(--t-border)' }}>
        {/* Search */}
        <div className="p-2 border-b" style={{ borderColor: 'var(--t-border)' }}>
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search playbooks..."
            className="w-full px-3 py-2 rounded text-sm focus:outline-none focus:ring-1"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', '--tw-ring-color': 'var(--t-primary)' } as React.CSSProperties}
          />
        </div>

        {/* Category filters */}
        <div className="p-2 border-b flex flex-wrap gap-1" style={{ borderColor: 'var(--t-border)' }}>
          <button
            onClick={() => setSelectedCategory(null)}
            className={`t-btn px-2 py-0.5 text-[10px] rounded`}
            style={!selectedCategory ? { background: 'var(--t-primary)', color: 'var(--t-text)' } : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}
          >
            ALL
          </button>
          {categories.map(c => (
            <button
              key={c.name}
              onClick={() => setSelectedCategory(c.name)}
              className={`t-btn px-2 py-0.5 text-[10px] rounded`}
              style={selectedCategory === c.name ? { background: 'var(--t-primary)', color: 'var(--t-text)' } : { background: 'var(--t-surface2)', color: 'var(--t-text2)' }}
            >
              {c.name} ({c.count})
            </button>
          ))}
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {playbooks.map(pb => (
            <button
              key={pb.filename}
              onClick={() => handleSelectPlaybook(pb.filename)}
              className={`t-btn w-full text-left px-3 py-2 border-b`}
              style={{
                borderColor: 'var(--t-surface)',
                ...(selectedPlaybook?.filename === pb.filename ? { background: 'var(--t-surface2)' } : {}),
              }}
              onMouseEnter={e => { if (selectedPlaybook?.filename !== pb.filename) e.currentTarget.style.background = 'var(--t-surface2)'; }}
              onMouseLeave={e => { if (selectedPlaybook?.filename !== pb.filename) e.currentTarget.style.background = ''; }}
            >
              <div className="text-sm truncate" style={{ color: 'var(--t-text2)' }}>{pb.title}</div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'var(--t-surface2)' }}>{pb.category}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${difficultyColors[pb.difficulty] || 'bg-gray-600'}`}>{pb.difficulty}</span>
                <span className="text-[10px]" style={{ color: 'var(--t-muted)' }}>{pb.word_count} words</span>
                {pb.score && <span className="text-[10px]" style={{ color: 'var(--t-primary)' }}>score: {pb.score}</span>}
              </div>
            </button>
          ))}
          {playbooks.length === 0 && <p className="p-3 text-xs text-center" style={{ color: 'var(--t-muted)' }}>No playbooks found</p>}
        </div>
      </div>

      {/* Reader */}
      <div className="flex-1 overflow-y-auto">
        {loading && <div className="flex justify-center mt-20"><div className="animate-spin h-8 w-8 border-2 border-t-transparent rounded-full" style={{ borderColor: 'var(--t-primary)', borderTopColor: 'transparent' }} /></div>}
        {selectedPlaybook && !loading ? (
          <div className="p-4 lg:p-6 max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold mb-2" style={{ color: 'var(--t-text)' }}>{selectedPlaybook.title}</h1>
            <div className="flex gap-2 mb-4">
              <span className="px-2 py-0.5 text-xs rounded" style={{ background: 'var(--t-surface2)' }}>{selectedPlaybook.category}</span>
              <span className={`px-2 py-0.5 text-xs rounded ${difficultyColors[selectedPlaybook.difficulty] || 'bg-gray-600'}`}>{selectedPlaybook.difficulty}</span>
            </div>
            <div className="prose prose-invert prose-sm max-w-none">
              <pre className="whitespace-pre-wrap text-sm leading-relaxed" style={{ color: 'var(--t-text2)' }}>{selectedPlaybook.content}</pre>
            </div>
          </div>
        ) : !loading && (
          <div className="flex items-center justify-center h-full" style={{ color: 'var(--t-muted)' }}>
            <div className="text-center">
              <p className="text-lg">53 Playbooks</p>
              <p className="text-sm mt-1">Select a playbook to read its full content</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlaybooksPage;
