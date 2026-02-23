/** StudioWelcome — Landing page shown when no project is open */
import React, { useState, useEffect } from 'react';
import { useStudio } from '../../context/StudioContext';

const TEMPLATES = [
  { name: 'Todo App', description: 'A task manager with categories, priorities, and due dates' },
  { name: 'Dashboard', description: 'Data visualization dashboard with charts and metrics' },
  { name: 'Chat App', description: 'Real-time messaging interface with threads' },
  { name: 'E-commerce', description: 'Product listing with cart and checkout flow' },
  { name: 'Blog', description: 'Markdown blog with search and categories' },
  { name: 'Portfolio', description: 'Personal portfolio with project showcase' },
];

const StudioWelcome: React.FC = () => {
  const { createProject, loadProject, loadProjectList, projectList, isLoading } = useStudio();
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadProjectList();
  }, [loadProjectList]);

  const handleCreate = async (name?: string, description?: string) => {
    const projectName = name || newName.trim();
    if (!projectName || creating) return;
    setCreating(true);
    try {
      await createProject(projectName, description);
    } finally {
      setCreating(false);
      setNewName('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleCreate();
  };

  return (
    <div className="flex flex-col items-center justify-center h-full overflow-y-auto p-6" style={{ background: 'var(--t-bg)' }}>
      <div className="w-full max-w-lg space-y-6">
        {/* Logo/Header */}
        <div className="text-center">
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ background: 'var(--t-surface2)' }}
          >
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} style={{ color: 'var(--t-primary)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold mb-1" style={{ color: 'var(--t-text)' }}>Studio</h1>
          <p className="text-sm" style={{ color: 'var(--t-muted)' }}>
            Describe your app and watch it come to life with AI-powered code generation
          </p>
        </div>

        {/* New project input */}
        <div>
          <div className="flex gap-2">
            <input
              type="text"
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Name your project..."
              className="flex-1 px-4 py-2.5 rounded-lg text-sm outline-none"
              style={{
                background: 'var(--t-surface)',
                color: 'var(--t-text)',
                border: '1px solid var(--t-border)',
                fontFamily: 'var(--t-font)',
              }}
              disabled={creating || isLoading}
            />
            <button
              onClick={() => handleCreate()}
              disabled={!newName.trim() || creating || isLoading}
              className="px-5 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-40"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>

        {/* Templates */}
        <div>
          <h3 className="text-xs font-medium mb-2" style={{ color: 'var(--t-text2)' }}>Start from a template</h3>
          <div className="grid grid-cols-2 gap-2">
            {TEMPLATES.map(tmpl => (
              <button
                key={tmpl.name}
                onClick={() => handleCreate(tmpl.name, tmpl.description)}
                disabled={creating || isLoading}
                className="text-left p-3 rounded-lg transition-colors hover:opacity-90 disabled:opacity-40"
                style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}
              >
                <span className="text-xs font-medium block mb-0.5" style={{ color: 'var(--t-text)' }}>{tmpl.name}</span>
                <span className="text-xs block" style={{ color: 'var(--t-muted)', lineHeight: '1.4' }}>{tmpl.description}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Recent projects */}
        {projectList.length > 0 && (
          <div>
            <h3 className="text-xs font-medium mb-2" style={{ color: 'var(--t-text2)' }}>Recent Projects</h3>
            <div className="space-y-1.5">
              {projectList.slice(0, 8).map(proj => (
                <button
                  key={proj.id}
                  onClick={() => loadProject(proj.id)}
                  disabled={isLoading}
                  className="flex items-center justify-between w-full px-3 py-2.5 rounded-lg text-left transition-colors hover:opacity-90 disabled:opacity-40"
                  style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}
                >
                  <div className="min-w-0 flex-1">
                    <span className="text-xs font-medium block truncate" style={{ color: 'var(--t-text)' }}>{proj.name}</span>
                    {proj.description && (
                      <span className="text-xs block truncate mt-0.5" style={{ color: 'var(--t-muted)' }}>{proj.description}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                    <span className="text-xs" style={{ color: 'var(--t-muted)' }}>{proj.fileCount} files</span>
                    <span className="text-xs" style={{ color: 'var(--t-muted)' }}>
                      {new Date(proj.updatedAt).toLocaleDateString()}
                    </span>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} style={{ color: 'var(--t-muted)' }}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudioWelcome;
