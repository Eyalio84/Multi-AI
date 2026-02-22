import React, { useState, useRef, useEffect } from 'react';
import { useAppContext } from '../context/AppContext';
import * as apiService from '../services/apiService';
import { THEME_LIST, ThemeId } from '../themes/index';

const SettingsPage: React.FC = () => {
  const {
    workspaceMode, setWorkspaceMode,
    projects, personas, filesByProject,
    setGlobalError, themeId, switchTheme,
  } = useAppContext();
  const [exportStatus, setExportStatus] = useState('');
  const [importStatus, setImportStatus] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // API key state
  const [geminiKey, setGeminiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [geminiConfigured, setGeminiConfigured] = useState(false);
  const [anthropicConfigured, setAnthropicConfigured] = useState(false);
  const [keySaveStatus, setKeySaveStatus] = useState('');
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [showAnthropicKey, setShowAnthropicKey] = useState(false);

  useEffect(() => {
    apiService.getKeysStatus().then(s => {
      setGeminiConfigured(s.gemini);
      setAnthropicConfigured(s.anthropic);
    }).catch(() => {});
  }, [workspaceMode]);

  const handleSaveKeys = async () => {
    if (!geminiKey && !anthropicKey) return;
    setKeySaveStatus('Saving...');
    try {
      const res = await apiService.setApiKeys(
        geminiKey || undefined,
        anthropicKey || undefined,
      );
      setGeminiConfigured(res.gemini_configured);
      setAnthropicConfigured(res.anthropic_configured);
      setGeminiKey('');
      setAnthropicKey('');
      setKeySaveStatus('Saved!');
      setTimeout(() => setKeySaveStatus(''), 3000);
    } catch (e: any) {
      setGlobalError(e.message);
      setKeySaveStatus('Failed');
    }
  };

  const handleExport = async () => {
    setExportStatus('Exporting...');
    try {
      const files: Record<string, any[]> = {};
      for (const [id, f] of filesByProject.entries()) files[id] = f;
      const data = await apiService.exportWorkspace({ projects, personas, files });

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `workspace-export-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setExportStatus('Exported!');
    } catch (e: any) {
      setGlobalError(e.message);
      setExportStatus('Failed');
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportStatus('Importing...');
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      const result = await apiService.importWorkspace(data);
      setImportStatus(`Imported: ${result.counts?.projects || 0} projects, ${result.counts?.chatMessages || 0} messages`);
    } catch (err: any) {
      setGlobalError(err.message);
      setImportStatus('Failed');
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-8 overflow-y-auto h-full">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--t-text)' }}>Settings</h1>

      {/* Theme */}
      <section className="t-card rounded-lg p-4" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
        <h2 className="text-lg font-semibold mb-3" style={{ color: 'var(--t-text)' }}>Theme</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {THEME_LIST.map(t => {
            const active = themeId === t.id;
            return (
              <button
                key={t.id}
                onClick={() => switchTheme(t.id as ThemeId)}
                className="t-card text-left p-3 rounded-lg border-2 transition-all"
                style={{
                  borderColor: active ? 'var(--t-primary)' : 'var(--t-border)',
                  background: active ? 'var(--t-surface2)' : 'var(--t-surface)',
                }}
              >
                {/* Mini mockup */}
                <div
                  className="rounded mb-2 p-2 flex flex-col gap-1"
                  style={{ background: t.vars['--t-bg'], minHeight: 56 }}
                >
                  {/* Mock nav bar */}
                  <div className="flex items-center gap-1 mb-1">
                    <div className="rounded-sm" style={{ width: 30, height: 4, background: t.vars['--t-primary'] }} />
                    <div className="rounded-sm" style={{ width: 16, height: 3, background: t.vars['--t-muted'] }} />
                    <div className="rounded-sm" style={{ width: 16, height: 3, background: t.vars['--t-muted'] }} />
                  </div>
                  {/* Mock content card */}
                  <div className="rounded-sm flex-1 p-1" style={{ background: t.vars['--t-surface'], border: `1px solid ${t.vars['--t-border']}` }}>
                    <div className="rounded-sm mb-0.5" style={{ width: '70%', height: 3, background: t.vars['--t-text'] }} />
                    <div className="rounded-sm" style={{ width: '50%', height: 2, background: t.vars['--t-muted'] }} />
                  </div>
                  {/* Swatch row */}
                  <div className="flex gap-1 mt-1">
                    {t.swatches.slice(2).map((c, i) => (
                      <div key={i} className="rounded-full" style={{ width: 8, height: 8, background: c }} />
                    ))}
                  </div>
                </div>
                {/* Label */}
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold" style={{ color: 'var(--t-text)' }}>{t.name}</div>
                    <div className="text-xs" style={{ color: 'var(--t-muted)' }}>{t.description}</div>
                  </div>
                  {active && (
                    <svg className="w-5 h-5 shrink-0" style={{ color: 'var(--t-primary)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Mode */}
      <section className="t-card rounded-lg p-4" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
        <h2 className="text-lg font-semibold mb-3" style={{ color: 'var(--t-text)' }}>Operating Mode</h2>
        <p className="text-sm mb-3" style={{ color: 'var(--t-muted)' }}>
          <strong>Standalone:</strong> Both Gemini and Claude APIs called directly.<br />
          <strong>Claude Code:</strong> Only Gemini API; Claude tasks export JSON for Claude Code sessions.
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => setWorkspaceMode('standalone')}
            className="t-btn flex-1 px-4 py-3 rounded-lg border-2 transition-colors"
            style={{
              borderColor: workspaceMode === 'standalone' ? 'var(--t-primary)' : 'var(--t-border)',
              background: workspaceMode === 'standalone' ? 'var(--t-surface2)' : 'var(--t-surface)',
              color: 'var(--t-text)',
            }}
          >
            <div className="font-semibold text-sm">Standalone</div>
            <div className="text-xs mt-1" style={{ color: 'var(--t-muted)' }}>Both API keys</div>
          </button>
          <button
            onClick={() => setWorkspaceMode('claude-code')}
            className="t-btn flex-1 px-4 py-3 rounded-lg border-2 transition-colors"
            style={{
              borderColor: workspaceMode === 'claude-code' ? 'var(--t-primary)' : 'var(--t-border)',
              background: workspaceMode === 'claude-code' ? 'var(--t-surface2)' : 'var(--t-surface)',
              color: 'var(--t-text)',
            }}
          >
            <div className="font-semibold text-sm">Claude Code</div>
            <div className="text-xs mt-1" style={{ color: 'var(--t-muted)' }}>Gemini API only</div>
          </button>
        </div>
      </section>

      {/* Export/Import */}
      <section className="t-card rounded-lg p-4" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
        <h2 className="text-lg font-semibold mb-3" style={{ color: 'var(--t-text)' }}>Workspace Transfer</h2>
        <p className="text-sm mb-3" style={{ color: 'var(--t-muted)' }}>
          Export your workspace (projects, files, personas) as JSON. Import from the other mode.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <button onClick={handleExport} className="t-btn px-4 py-2 rounded text-sm" style={{ background: 'var(--t-primary)', color: '#fff' }}>
            Export Workspace
          </button>
          <button onClick={() => fileInputRef.current?.click()} className="t-btn px-4 py-2 rounded text-sm" style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}>
            Import Workspace
          </button>
          <input ref={fileInputRef} type="file" accept=".json" onChange={handleImport} className="hidden" />
        </div>
        {exportStatus && <p className="mt-2 text-xs" style={{ color: 'var(--t-muted)' }}>{exportStatus}</p>}
        {importStatus && <p className="mt-2 text-xs" style={{ color: 'var(--t-muted)' }}>{importStatus}</p>}
      </section>

      {/* API Keys */}
      <section className="t-card rounded-lg p-4" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
        <h2 className="text-lg font-semibold mb-3" style={{ color: 'var(--t-text)' }}>API Keys</h2>

        {/* Status indicators */}
        <div className="space-y-2 text-sm mb-4">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full" style={{ background: geminiConfigured ? 'var(--t-success)' : 'var(--t-error)' }} />
            <span style={{ color: 'var(--t-text2)' }}>
              Gemini API: {geminiConfigured ? 'Configured' : 'Not configured'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full" style={{ background: anthropicConfigured ? 'var(--t-success)' : workspaceMode === 'claude-code' ? 'var(--t-muted)' : 'var(--t-error)' }} />
            <span style={{ color: 'var(--t-text2)' }}>
              Anthropic API: {workspaceMode === 'claude-code' ? 'Disabled (Claude Code mode)' : anthropicConfigured ? 'Configured' : 'Not configured'}
            </span>
          </div>
        </div>

        {/* Gemini key input */}
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: 'var(--t-muted)' }}>Gemini API Key</label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showGeminiKey ? 'text' : 'password'}
                  value={geminiKey}
                  onChange={e => setGeminiKey(e.target.value)}
                  placeholder={geminiConfigured ? 'Key set (enter new to replace)' : 'AIzaSy...'}
                  className="t-btn w-full px-3 py-2 rounded text-sm"
                  style={{ background: 'var(--t-bg)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
                />
                <button
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-xs"
                  style={{ color: 'var(--t-muted)' }}
                >
                  {showGeminiKey ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>
          </div>

          {/* Anthropic key input */}
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: 'var(--t-muted)' }}>Anthropic API Key</label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showAnthropicKey ? 'text' : 'password'}
                  value={anthropicKey}
                  onChange={e => setAnthropicKey(e.target.value)}
                  placeholder={anthropicConfigured ? 'Key set (enter new to replace)' : 'sk-ant-api03-...'}
                  className="t-btn w-full px-3 py-2 rounded text-sm"
                  style={{ background: 'var(--t-bg)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
                  disabled={workspaceMode === 'claude-code'}
                />
                <button
                  onClick={() => setShowAnthropicKey(!showAnthropicKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-xs"
                  style={{ color: 'var(--t-muted)' }}
                >
                  {showAnthropicKey ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSaveKeys}
              disabled={!geminiKey && !anthropicKey}
              className="t-btn px-4 py-2 rounded text-sm"
              style={{
                background: (geminiKey || anthropicKey) ? 'var(--t-primary)' : 'var(--t-surface2)',
                color: (geminiKey || anthropicKey) ? '#fff' : 'var(--t-muted)',
                cursor: (geminiKey || anthropicKey) ? 'pointer' : 'default',
              }}
            >
              Save Keys
            </button>
            {keySaveStatus && <span className="text-xs" style={{ color: 'var(--t-muted)' }}>{keySaveStatus}</span>}
          </div>
        </div>

        <p className="text-xs mt-3" style={{ color: 'var(--t-muted)' }}>
          Keys are stored in server memory only (not written to disk). They reset when the server restarts.
          You can also set keys via environment variables: GEMINI_API_KEY and ANTHROPIC_API_KEY.
        </p>
      </section>

      {/* About */}
      <section className="t-card rounded-lg p-4" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
        <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--t-text)' }}>About</h2>
        <p className="text-sm" style={{ color: 'var(--t-muted)' }}>
          Multi-AI Agentic Workspace v1.0<br />
          Professional workflow orchestrator combining Gemini + Claude intelligence<br />
          33 NLKE agents | 53 playbooks | 4 workflow templates
        </p>
      </section>
    </div>
  );
};

export default SettingsPage;
