import React, { useState, useEffect } from 'react';
import * as apiService from '../services/apiService';
import { ToolSummary, ToolDetail, ToolParam } from '../types/index';
import { showToast } from '../hooks/useToast';

const categoryColors: Record<string, string> = {
  'Code Quality': '#059669',
  'Cost Optimization': '#d97706',
  'Agent Intelligence': '#7c3aed',
  'Knowledge Graph': '#2563eb',
  'Generators': '#db2777',
  'Reasoning': '#dc2626',
  'Dev Tools': '#0891b2',
  'Frontend': '#f59e0b',
  'Backend': '#8b5cf6',
  'Full-Stack': '#ec4899',
  'Orchestration': '#14b8a6',
};

const ToolsPage: React.FC = () => {
  const [categories, setCategories] = useState<string[]>([]);
  const [toolsByCategory, setToolsByCategory] = useState<Record<string, ToolSummary[]>>({});
  const [activeCategory, setActiveCategory] = useState('ALL');
  const [search, setSearch] = useState('');
  const [selectedTool, setSelectedTool] = useState<ToolDetail | null>(null);
  const [paramValues, setParamValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<'run' | 'schema'>('run');
  const [total, setTotal] = useState(0);

  useEffect(() => {
    apiService.listTools().then((data: any) => {
      setCategories(data.categories || []);
      setToolsByCategory(data.tools || {});
      setTotal(data.total || 0);
    }).catch((e: any) => showToast(e.message || 'Failed to load tools'));
  }, []);

  const handleSelectTool = async (id: string) => {
    try {
      const detail = await apiService.getToolDetail(id);
      setSelectedTool(detail);
      setResult(null);
      setTab('run');
      // Initialize param defaults
      const defaults: Record<string, string> = {};
      (detail.params || []).forEach((p: ToolParam) => {
        if (p.default !== null && p.default !== undefined) {
          defaults[p.name] = typeof p.default === 'object' ? JSON.stringify(p.default, null, 2) : String(p.default);
        } else if (p.type === 'json') {
          defaults[p.name] = p.description || '{}';
        } else {
          defaults[p.name] = '';
        }
      });
      setParamValues(defaults);
    } catch (e: any) {
      showToast(e.message || 'Failed to load tool');
    }
  };

  const handleRun = async () => {
    if (!selectedTool) return;
    setLoading(true);
    setResult(null);
    try {
      // Build typed params
      const params: Record<string, any> = {};
      selectedTool.params.forEach((p: ToolParam) => {
        const raw = paramValues[p.name];
        if (raw === undefined || raw === '') {
          if (p.required) params[p.name] = p.default;
          return;
        }
        if (p.type === 'json') {
          try { params[p.name] = JSON.parse(raw); } catch { params[p.name] = raw; }
        } else if (p.type === 'integer') {
          params[p.name] = parseInt(raw, 10);
        } else if (p.type === 'float') {
          params[p.name] = parseFloat(raw);
        } else if (p.type === 'boolean') {
          params[p.name] = raw === 'true';
        } else {
          params[p.name] = raw;
        }
      });
      const data = await apiService.runTool(selectedTool.id, params);
      setResult(data);
    } catch (e: any) {
      setResult({ success: false, error: e.message });
    }
    setLoading(false);
  };

  // Filter tools
  const filteredTools: { category: string; tools: ToolSummary[] }[] = [];
  const cats = activeCategory === 'ALL' ? categories : [activeCategory];
  cats.forEach(cat => {
    const tools = toolsByCategory[cat] || [];
    const filtered = search
      ? tools.filter(t => t.name.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase()))
      : tools;
    if (filtered.length > 0) filteredTools.push({ category: cat, tools: filtered });
  });

  const renderParamInput = (p: ToolParam) => {
    const val = paramValues[p.name] || '';
    const baseStyle = {
      background: 'var(--t-bg)',
      color: 'var(--t-text2)',
      borderColor: 'var(--t-border)',
    };

    if (p.type === 'boolean') {
      return (
        <select
          value={val}
          onChange={e => setParamValues(prev => ({ ...prev, [p.name]: e.target.value }))}
          className="w-full px-2 py-1.5 rounded border text-sm"
          style={baseStyle}
        >
          <option value="true">true</option>
          <option value="false">false</option>
        </select>
      );
    }

    if (p.type === 'text' || p.type === 'json' || p.multiline) {
      return (
        <textarea
          value={val}
          onChange={e => setParamValues(prev => ({ ...prev, [p.name]: e.target.value }))}
          rows={p.type === 'json' ? 6 : 4}
          className={`w-full px-2 py-1.5 rounded border text-sm resize-y ${p.type === 'json' ? 'font-mono' : ''}`}
          style={baseStyle}
          placeholder={p.description}
          spellCheck={false}
        />
      );
    }

    return (
      <input
        type={p.type === 'integer' || p.type === 'float' ? 'number' : 'text'}
        step={p.type === 'float' ? '0.1' : undefined}
        value={val}
        onChange={e => setParamValues(prev => ({ ...prev, [p.name]: e.target.value }))}
        className="w-full px-2 py-1.5 rounded border text-sm"
        style={baseStyle}
        placeholder={p.description}
      />
    );
  };

  return (
    <div className="flex flex-col lg:flex-row h-full">
      {/* Sidebar */}
      <div className="w-full lg:w-72 border-b lg:border-b-0 lg:border-r flex flex-col" style={{ borderColor: 'var(--t-border)' }}>
        {/* Category filter */}
        <div className="p-2 border-b" style={{ borderColor: 'var(--t-border)' }}>
          <div className="flex flex-wrap gap-1 mb-2">
            <button
              onClick={() => setActiveCategory('ALL')}
              className="t-btn px-2 py-0.5 text-[10px] rounded"
              style={activeCategory === 'ALL'
                ? { background: 'var(--t-primary)', color: '#fff' }
                : { background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
            >
              ALL ({total})
            </button>
            {categories.map(c => (
              <button
                key={c}
                onClick={() => setActiveCategory(c)}
                className="t-btn px-2 py-0.5 text-[10px] rounded"
                style={activeCategory === c
                  ? { background: categoryColors[c] || 'var(--t-primary)', color: '#fff' }
                  : { background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
              >
                {c}
              </button>
            ))}
          </div>
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search tools..."
            className="w-full px-2 py-1 rounded border text-xs"
            style={{ background: 'var(--t-bg)', color: 'var(--t-text2)', borderColor: 'var(--t-border)' }}
          />
        </div>

        {/* Tool list */}
        <div className="flex-1 overflow-y-auto">
          {filteredTools.map(group => (
            <div key={group.category}>
              <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider" style={{ color: categoryColors[group.category] || 'var(--t-muted)' }}>
                {group.category}
              </div>
              {group.tools.map(tool => (
                <button
                  key={tool.id}
                  onClick={() => handleSelectTool(tool.id)}
                  className="t-btn w-full text-left px-3 py-2 border-b"
                  style={{
                    borderColor: 'var(--t-surface)',
                    background: selectedTool?.id === tool.id ? 'var(--t-surface2)' : undefined,
                  }}
                  onMouseEnter={e => { if (selectedTool?.id !== tool.id) e.currentTarget.style.background = 'var(--t-surface2)'; }}
                  onMouseLeave={e => { if (selectedTool?.id !== tool.id) e.currentTarget.style.background = ''; }}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm truncate" style={{ color: 'var(--t-text2)' }}>{tool.name}</span>
                    <span className="text-[9px] px-1 rounded" style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}>
                      {tool.param_count}p
                    </span>
                  </div>
                  <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--t-muted)' }}>{tool.description}</p>
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {selectedTool ? (
          <>
            {/* Header */}
            <div className="p-3 border-b" style={{ background: 'var(--t-surface)', borderColor: 'var(--t-border)' }}>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold" style={{ color: 'var(--t-text)' }}>{selectedTool.name}</h2>
                <span className="px-2 py-0.5 text-[10px] rounded" style={{ background: categoryColors[selectedTool.category] || 'var(--t-surface2)', color: '#fff' }}>
                  {selectedTool.category}
                </span>
              </div>
              <p className="text-sm mt-0.5" style={{ color: 'var(--t-muted)' }}>{selectedTool.description}</p>
              {/* Tabs */}
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => setTab('run')}
                  className="t-btn px-3 py-1 text-xs rounded"
                  style={tab === 'run'
                    ? { background: 'var(--t-primary)', color: '#fff' }
                    : { background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
                >
                  Run
                </button>
                <button
                  onClick={() => setTab('schema')}
                  className="t-btn px-3 py-1 text-xs rounded"
                  style={tab === 'schema'
                    ? { background: 'var(--t-primary)', color: '#fff' }
                    : { background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
                >
                  Schema
                </button>
              </div>
            </div>

            {tab === 'run' ? (
              <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
                {/* Param form */}
                <div className="flex-1 flex flex-col border-b lg:border-b-0 lg:border-r overflow-y-auto" style={{ borderColor: 'var(--t-border)' }}>
                  <div className="p-3 space-y-3">
                    {selectedTool.params.map((p: ToolParam) => (
                      <div key={p.name}>
                        <label className="block text-xs font-medium mb-1" style={{ color: 'var(--t-text2)' }}>
                          {p.label}
                          {p.required && <span style={{ color: 'var(--t-error, #ef4444)' }}> *</span>}
                          <span className="ml-1 font-normal" style={{ color: 'var(--t-muted)' }}>({p.type})</span>
                        </label>
                        {renderParamInput(p)}
                      </div>
                    ))}
                    <button
                      onClick={handleRun}
                      disabled={loading}
                      className="t-btn w-full px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
                      style={{ background: 'var(--t-primary)', color: '#fff' }}
                    >
                      {loading ? 'Running...' : 'Run Tool'}
                    </button>
                  </div>
                </div>

                {/* Output */}
                <div className="flex-1 flex flex-col">
                  <div className="p-2 border-b" style={{ background: 'var(--t-surface)', borderColor: 'var(--t-border)' }}>
                    <span className="text-xs" style={{ color: 'var(--t-muted)' }}>Output</span>
                  </div>
                  <div className="flex-1 overflow-y-auto p-3">
                    {loading && (
                      <div className="text-center py-10">
                        <div className="animate-spin h-8 w-8 border-2 border-t-transparent rounded-full mx-auto" style={{ borderColor: 'var(--t-primary)', borderTopColor: 'transparent' }} />
                        <p className="text-xs mt-2" style={{ color: 'var(--t-muted)' }}>Executing tool...</p>
                      </div>
                    )}
                    {result && (
                      <div>
                        {result.success === false && (
                          <div className="p-2 rounded mb-2 text-sm" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
                            <strong>Error:</strong> {result.error}
                          </div>
                        )}
                        <pre className="text-xs whitespace-pre-wrap font-mono" style={{ color: 'var(--t-text2)' }}>
                          {JSON.stringify(result.success !== false ? result.result : result, null, 2)}
                        </pre>
                      </div>
                    )}
                    {!result && !loading && (
                      <p className="text-sm text-center mt-10" style={{ color: 'var(--t-muted)' }}>
                        Fill in parameters and click "Run Tool" to see results
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              /* Schema tab */
              <div className="flex-1 overflow-y-auto p-4">
                <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--t-text)' }}>Parameters</h3>
                <table className="w-full text-xs" style={{ color: 'var(--t-text2)' }}>
                  <thead>
                    <tr className="border-b" style={{ borderColor: 'var(--t-border)' }}>
                      <th className="text-left py-2 px-2">Name</th>
                      <th className="text-left py-2 px-2">Type</th>
                      <th className="text-left py-2 px-2">Required</th>
                      <th className="text-left py-2 px-2">Default</th>
                      <th className="text-left py-2 px-2">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedTool.params.map((p: ToolParam) => (
                      <tr key={p.name} className="border-b" style={{ borderColor: 'var(--t-surface)' }}>
                        <td className="py-2 px-2 font-mono">{p.name}</td>
                        <td className="py-2 px-2"><span className="px-1 rounded" style={{ background: 'var(--t-surface2)' }}>{p.type}</span></td>
                        <td className="py-2 px-2">{p.required ? 'Yes' : 'No'}</td>
                        <td className="py-2 px-2 font-mono">{p.default !== null && p.default !== undefined ? String(p.default) : '—'}</td>
                        <td className="py-2 px-2" style={{ color: 'var(--t-muted)' }}>{p.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <h3 className="text-sm font-semibold mt-6 mb-3" style={{ color: 'var(--t-text)' }}>Raw Definition</h3>
                <pre className="text-xs font-mono p-3 rounded" style={{ background: 'var(--t-bg)', color: 'var(--t-text2)' }}>
                  {JSON.stringify(selectedTool, null, 2)}
                </pre>
              </div>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-full" style={{ color: 'var(--t-muted)' }}>
            <div className="text-center">
              <svg className="mx-auto h-12 w-12 mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17l-5.384 3.18.96-5.593L2.7 8.574l5.61-.814L11.42 2.5l2.507 5.26 5.61.814-4.296 4.183.96 5.593-5.384-3.18z" />
              </svg>
              <p className="text-lg font-semibold">{total} Python Tools</p>
              <p className="text-sm mt-1">Select a tool from the sidebar to get started</p>
              <p className="text-xs mt-3 max-w-sm mx-auto">Code review, cost analysis, reasoning engines, generators, KG tools, and more — all running locally with zero external dependencies.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ToolsPage;
