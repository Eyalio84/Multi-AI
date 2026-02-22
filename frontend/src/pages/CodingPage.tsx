import React, { useState } from 'react';
import ChatPanel from '../components/chat/ChatPanel';
import { useAppContext } from '../context/AppContext';

const FileExplorer: React.FC<{ projectId: string }> = ({ projectId }) => {
  const { filesByProject, handleSaveFileContent, handleDeleteFile } = useAppContext();
  const files = filesByProject.get(projectId) || [];
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  const selectedFile = files.find(f => f.id === selectedFileId);

  return (
    <div className="flex flex-col lg:flex-row h-full">
      {/* File list */}
      <div className="w-full lg:w-56 border-b lg:border-b-0 lg:border-r overflow-y-auto" style={{ borderColor: 'var(--t-border)' }}>
        <div className="p-2 text-xs font-semibold uppercase border-b" style={{ color: 'var(--t-muted)', borderColor: 'var(--t-border)' }}>Files</div>
        {files.length === 0 && <p className="p-3 text-xs" style={{ color: 'var(--t-muted)' }}>No files yet. Chat with AI to create files.</p>}
        {files.map(f => (
          <button
            key={f.id}
            onClick={() => { setSelectedFileId(f.id); setEditContent(f.content); }}
            className={`t-btn w-full text-left px-3 py-1.5 text-xs truncate`}
            style={selectedFileId === f.id ? { background: 'var(--t-surface2)', color: 'var(--t-primary)' } : { color: 'var(--t-text2)' }}
            onMouseEnter={e => { if (selectedFileId !== f.id) (e.currentTarget.style.background = 'var(--t-surface2)'); }}
            onMouseLeave={e => { if (selectedFileId !== f.id) (e.currentTarget.style.background = ''); }}
          >
            {f.path}
          </button>
        ))}
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col min-w-0">
        {selectedFile ? (
          <>
            <div className="flex items-center justify-between p-2 border-b" style={{ background: 'var(--t-surface)', borderColor: 'var(--t-border)' }}>
              <span className="text-xs truncate" style={{ color: 'var(--t-muted)' }}>{selectedFile.path}</span>
              <div className="flex gap-2">
                <button
                  onClick={() => handleSaveFileContent(projectId, selectedFile.id, editContent)}
                  className="t-btn px-2 py-1 text-xs rounded"
                  style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}
                >
                  Save
                </button>
                <button
                  onClick={() => { handleDeleteFile(selectedFile.id, projectId); setSelectedFileId(null); }}
                  className="t-btn px-2 py-1 text-xs rounded"
                  style={{ background: 'var(--t-error)', color: 'var(--t-text)' }}
                >
                  Delete
                </button>
              </div>
            </div>
            <textarea
              value={editContent}
              onChange={e => setEditContent(e.target.value)}
              className="flex-1 p-3 font-mono text-sm resize-none focus:outline-none"
              style={{ background: 'var(--t-bg)', color: 'var(--t-text2)' }}
              spellCheck={false}
            />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-sm" style={{ color: 'var(--t-muted)' }}>
            Select a file to edit
          </div>
        )}
      </div>
    </div>
  );
};

const CodingPage: React.FC = () => {
  const { projects, selectedProjectIds, handleCreateProject, handleToggleProjectSelection, handleViewProjectFiles } = useAppContext();
  const [newProjectName, setNewProjectName] = useState('');
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!newProjectName.trim()) return;
    const p = await handleCreateProject(newProjectName.trim());
    setNewProjectName('');
    handleToggleProjectSelection(p.id);
    handleViewProjectFiles(p.id);
    setActiveProjectId(p.id);
  };

  return (
    <div className="flex flex-col lg:flex-row h-full">
      {/* Project sidebar */}
      <div className="w-full lg:w-52 border-b lg:border-b-0 lg:border-r flex flex-col" style={{ borderColor: 'var(--t-border)', background: 'var(--t-surface)' }}>
        <div className="p-2 border-b" style={{ borderColor: 'var(--t-border)' }}>
          <div className="flex gap-1">
            <input
              value={newProjectName}
              onChange={e => setNewProjectName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
              placeholder="New project..."
              className="flex-1 px-2 py-1 rounded text-xs focus:outline-none focus:ring-1"
              style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', '--tw-ring-color': 'var(--t-primary)' } as React.CSSProperties}
            />
            <button onClick={handleCreate} className="t-btn px-2 py-1 text-xs rounded" style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}>+</button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {projects.map(p => (
            <button
              key={p.id}
              onClick={() => { setActiveProjectId(p.id); handleToggleProjectSelection(p.id); handleViewProjectFiles(p.id); }}
              className={`t-btn w-full text-left px-3 py-2 text-sm`}
              style={activeProjectId === p.id ? { background: 'var(--t-surface2)', color: 'var(--t-primary)' } : { color: 'var(--t-text2)' }}
              onMouseEnter={e => { if (activeProjectId !== p.id) (e.currentTarget.style.background = 'var(--t-surface2)'); }}
              onMouseLeave={e => { if (activeProjectId !== p.id) (e.currentTarget.style.background = ''); }}
            >
              {p.name}
            </button>
          ))}
        </div>
      </div>

      {/* IDE + Chat */}
      <div className="flex-1 flex flex-col lg:flex-row min-w-0">
        <div className="flex-1 lg:w-2/3 border-b lg:border-b-0 lg:border-r" style={{ borderColor: 'var(--t-border)' }}>
          {activeProjectId ? (
            <FileExplorer projectId={activeProjectId} />
          ) : (
            <div className="flex items-center justify-center h-full" style={{ color: 'var(--t-muted)' }}>
              <p>Select or create a project to start coding</p>
            </div>
          )}
        </div>
        <div className="flex-1 lg:w-1/3 min-w-0">
          <ChatPanel defaultMode="coding" />
        </div>
      </div>
    </div>
  );
};

export default CodingPage;
