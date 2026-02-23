/** StudioFilesPanel — File tree showing generated files */
import React, { useMemo, useState } from 'react';
import { useStudio } from '../../context/StudioContext';

interface TreeNode {
  name: string;
  path: string;
  isDir: boolean;
  children: TreeNode[];
}

const StudioFilesPanel: React.FC = () => {
  const { files, openFile, activeTab, deleteFile, mode } = useStudio();
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['/']));

  // Build tree from flat file map
  const tree = useMemo(() => {
    const root: TreeNode = { name: '/', path: '/', isDir: true, children: [] };
    const paths = Object.keys(files).sort();

    for (const filePath of paths) {
      const cleanPath = filePath.startsWith('/') ? filePath : `/${filePath}`;
      const parts = cleanPath.split('/').filter(Boolean);
      let current = root;

      for (let i = 0; i < parts.length; i++) {
        const isLast = i === parts.length - 1;
        const partPath = '/' + parts.slice(0, i + 1).join('/');
        let child = current.children.find(c => c.name === parts[i]);

        if (!child) {
          child = {
            name: parts[i],
            path: partPath,
            isDir: !isLast,
            children: [],
          };
          current.children.push(child);
        }
        current = child;
      }
    }

    // Sort: dirs first, then alphabetically
    const sortTree = (node: TreeNode) => {
      node.children.sort((a, b) => {
        if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
      node.children.forEach(sortTree);
    };
    sortTree(root);
    return root;
  }, [files]);

  const toggleDir = (path: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const fileCount = Object.keys(files).length;

  const getFileIcon = (name: string) => {
    const ext = name.split('.').pop()?.toLowerCase() || '';
    const iconMap: Record<string, string> = {
      tsx: '#3b82f6', ts: '#3b82f6', jsx: '#f59e0b', js: '#f59e0b',
      css: '#8b5cf6', html: '#ef4444', json: '#22c55e', md: '#6b7280',
      py: '#22d3ee', sql: '#f97316',
    };
    return iconMap[ext] || 'var(--t-muted)';
  };

  const renderNode = (node: TreeNode, depth: number) => {
    if (node.isDir) {
      const isExpanded = expanded.has(node.path);
      return (
        <div key={node.path}>
          <button
            onClick={() => toggleDir(node.path)}
            className="flex items-center gap-1 w-full text-left px-2 py-1 hover:opacity-80 transition-opacity text-xs"
            style={{ paddingLeft: depth * 12 + 8, color: 'var(--t-text2)' }}
          >
            <svg className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} style={{ color: 'var(--t-warning)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
            </svg>
            <span className="truncate">{node.name}</span>
          </button>
          {isExpanded && node.children.map(child => renderNode(child, depth + 1))}
        </div>
      );
    }

    const isActive = activeTab === node.path || activeTab === node.path.slice(1);
    const iconColor = getFileIcon(node.name);

    return (
      <button
        key={node.path}
        onClick={() => openFile(node.path.startsWith('/') ? node.path.slice(1) : node.path)}
        className="flex items-center gap-1.5 w-full text-left px-2 py-1 hover:opacity-80 transition-opacity text-xs group"
        style={{
          paddingLeft: depth * 12 + 8,
          color: isActive ? 'var(--t-primary)' : 'var(--t-text)',
          background: isActive ? 'var(--t-surface2)' : 'transparent',
        }}
      >
        <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: iconColor }} />
        <span className="truncate flex-1">{node.name}</span>
        {mode === 'code' && (
          <button
            onClick={(e) => { e.stopPropagation(); deleteFile(node.path.startsWith('/') ? node.path.slice(1) : node.path); }}
            className="opacity-0 group-hover:opacity-60 hover:opacity-100 p-0.5"
            style={{ color: 'var(--t-error)' }}
          >
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </button>
    );
  };

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 h-8 flex-shrink-0"
        style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
      >
        <span className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>
          Files
        </span>
        <span className="text-xs" style={{ color: 'var(--t-muted)' }}>
          {fileCount}
        </span>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto py-1">
        {fileCount === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-xs text-center px-4" style={{ color: 'var(--t-muted)' }}>
              No files yet. Use chat to generate your app.
            </p>
          </div>
        ) : (
          tree.children.map(child => renderNode(child, 0))
        )}
      </div>
    </div>
  );
};

export default StudioFilesPanel;
