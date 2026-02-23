/** StudioProjectSettings — Project name, description, tech stack, dependencies */
import React, { useState, useEffect, useCallback } from 'react';
import { useStudio } from '../../context/StudioContext';
import type { StudioProjectSettings as SettingsType } from '../../types/studio';
import * as studioApi from '../../services/studioApiService';

const TECH_STACKS: { value: SettingsType['techStack']; label: string }[] = [
  { value: 'react', label: 'React (JavaScript)' },
  { value: 'react-ts', label: 'React (TypeScript)' },
];

const CSS_FRAMEWORKS: { value: SettingsType['cssFramework']; label: string }[] = [
  { value: 'tailwind', label: 'Tailwind CSS' },
  { value: 'css', label: 'Plain CSS' },
  { value: 'none', label: 'None' },
];

const BACKEND_FRAMEWORKS: { value: NonNullable<SettingsType['backendFramework']>; label: string }[] = [
  { value: 'fastapi', label: 'FastAPI (Python)' },
  { value: 'express', label: 'Express (Node.js)' },
];

const StudioProjectSettings: React.FC = () => {
  const { project, saveProject, isLoading } = useStudio();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [techStack, setTechStack] = useState<SettingsType['techStack']>('react-ts');
  const [cssFramework, setCssFramework] = useState<SettingsType['cssFramework']>('tailwind');
  const [hasBackend, setHasBackend] = useState(false);
  const [backendFramework, setBackendFramework] = useState<SettingsType['backendFramework']>('fastapi');
  const [newDep, setNewDep] = useState('');
  const [dependencies, setDependencies] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Populate from project
  useEffect(() => {
    if (project) {
      setName(project.name);
      setDescription(project.description);
      if (project.settings) {
        setTechStack(project.settings.techStack || 'react-ts');
        setCssFramework(project.settings.cssFramework || 'tailwind');
        setHasBackend(project.settings.hasBackend || false);
        setBackendFramework(project.settings.backendFramework || 'fastapi');
        setDependencies(project.settings.dependencies || {});
      }
    }
  }, [project]);

  const handleAddDep = useCallback(() => {
    const trimmed = newDep.trim();
    if (!trimmed) return;
    const [pkg, version] = trimmed.includes('@') ? trimmed.split('@') : [trimmed, 'latest'];
    setDependencies(prev => ({ ...prev, [pkg]: version || 'latest' }));
    setNewDep('');
  }, [newDep]);

  const handleRemoveDep = useCallback((pkg: string) => {
    setDependencies(prev => {
      const next = { ...prev };
      delete next[pkg];
      return next;
    });
  }, []);

  const handleSave = useCallback(async () => {
    if (!project || saving) return;
    setSaving(true);
    setSaved(false);

    try {
      await studioApi.updateProject(project.id, {
        name,
        description,
        settings: {
          techStack,
          cssFramework,
          hasBackend,
          backendFramework: hasBackend ? backendFramework : undefined,
          dependencies,
        },
      } as any);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Failed to save settings:', err);
    } finally {
      setSaving(false);
    }
  }, [project, name, description, techStack, cssFramework, hasBackend, backendFramework, dependencies, saving]);

  if (!project) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-xs" style={{ color: 'var(--t-muted)' }}>No project open</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Header */}
      <div
        className="flex items-center px-3 h-8 flex-shrink-0"
        style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
      >
        <span className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>Project Settings</span>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Name */}
        <div>
          <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--t-text2)' }}>Project Name</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            className="w-full px-3 py-2 rounded text-sm outline-none"
            style={{ background: 'var(--t-surface)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
          />
        </div>

        {/* Description */}
        <div>
          <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--t-text2)' }}>Description</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 rounded text-sm outline-none resize-none"
            style={{ background: 'var(--t-surface)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
          />
        </div>

        {/* Tech Stack */}
        <div>
          <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--t-text2)' }}>Tech Stack</label>
          <select
            value={techStack}
            onChange={e => setTechStack(e.target.value as SettingsType['techStack'])}
            className="w-full px-3 py-2 rounded text-sm outline-none"
            style={{ background: 'var(--t-surface)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
          >
            {TECH_STACKS.map(ts => (
              <option key={ts.value} value={ts.value}>{ts.label}</option>
            ))}
          </select>
        </div>

        {/* CSS Framework */}
        <div>
          <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--t-text2)' }}>CSS Framework</label>
          <div className="flex gap-2">
            {CSS_FRAMEWORKS.map(cf => (
              <button
                key={cf.value}
                onClick={() => setCssFramework(cf.value)}
                className="flex-1 py-1.5 rounded text-xs transition-colors"
                style={{
                  background: cssFramework === cf.value ? 'var(--t-primary)' : 'var(--t-surface)',
                  color: cssFramework === cf.value ? '#fff' : 'var(--t-muted)',
                  border: `1px solid ${cssFramework === cf.value ? 'var(--t-primary)' : 'var(--t-border)'}`,
                }}
              >
                {cf.label}
              </button>
            ))}
          </div>
        </div>

        {/* Backend toggle */}
        <div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={hasBackend}
              onChange={e => setHasBackend(e.target.checked)}
              className="rounded"
              style={{ accentColor: 'var(--t-primary)' }}
            />
            <span className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>Include Backend</span>
          </label>

          {hasBackend && (
            <select
              value={backendFramework}
              onChange={e => setBackendFramework(e.target.value as SettingsType['backendFramework'])}
              className="w-full mt-2 px-3 py-2 rounded text-sm outline-none"
              style={{ background: 'var(--t-surface)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
            >
              {BACKEND_FRAMEWORKS.map(bf => (
                <option key={bf.value} value={bf.value}>{bf.label}</option>
              ))}
            </select>
          )}
        </div>

        {/* Dependencies */}
        <div>
          <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--t-text2)' }}>
            Dependencies ({Object.keys(dependencies).length})
          </label>

          <div className="flex gap-1 mb-2">
            <input
              type="text"
              value={newDep}
              onChange={e => setNewDep(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAddDep()}
              placeholder="e.g. axios or lodash@4.17.21"
              className="flex-1 px-2 py-1 rounded text-xs outline-none"
              style={{ background: 'var(--t-surface)', color: 'var(--t-text)', border: '1px solid var(--t-border)', fontFamily: 'var(--t-font-mono)' }}
            />
            <button
              onClick={handleAddDep}
              className="px-2 py-1 rounded text-xs"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
            >
              Add
            </button>
          </div>

          <div className="space-y-1">
            {Object.entries(dependencies).map(([pkg, ver]) => (
              <div key={pkg} className="flex items-center justify-between px-2 py-1 rounded" style={{ background: 'var(--t-surface)' }}>
                <span className="text-xs" style={{ color: 'var(--t-text)', fontFamily: 'var(--t-font-mono)' }}>
                  {pkg}<span style={{ color: 'var(--t-muted)' }}>@{ver}</span>
                </span>
                <button
                  onClick={() => handleRemoveDep(pkg)}
                  className="p-0.5 rounded hover:opacity-80"
                  style={{ color: 'var(--t-error)' }}
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Save */}
      <div className="flex-shrink-0 p-3" style={{ borderTop: '1px solid var(--t-border)' }}>
        <button
          onClick={handleSave}
          disabled={saving || isLoading}
          className="w-full py-2 rounded text-xs font-medium transition-colors disabled:opacity-40"
          style={{ background: saved ? 'var(--t-success)' : 'var(--t-primary)', color: '#fff' }}
        >
          {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
};

export default StudioProjectSettings;
