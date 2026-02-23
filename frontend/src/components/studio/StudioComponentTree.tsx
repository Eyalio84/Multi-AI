/** StudioComponentTree — React component hierarchy tree view */
import React, { useMemo, useState, useCallback } from 'react';
import { useStudio } from '../../context/StudioContext';
import type { StudioSelection } from '../../types/studio';

interface ComponentNode {
  name: string;
  tag: string;
  filePath: string;
  lineNumber: number;
  children: ComponentNode[];
  depth: number;
}

const StudioComponentTree: React.FC = () => {
  const { files, selectedElement, setSelectedElement } = useStudio();
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['root']));
  const [filter, setFilter] = useState('');

  // Parse files to extract component hierarchy
  const tree = useMemo((): ComponentNode[] => {
    const components: ComponentNode[] = [];
    const fileEntries = Object.entries(files);

    for (const [path, file] of fileEntries) {
      // Only parse JSX/TSX files
      if (!path.match(/\.(tsx|jsx|js)$/)) continue;

      const parsed = parseComponents(path, file.content);
      components.push(...parsed);
    }

    // Build tree by analyzing imports and JSX usage
    const rootComponents = buildHierarchy(components, files);
    return rootComponents;
  }, [files]);

  const toggleExpand = useCallback((key: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const handleSelect = useCallback((node: ComponentNode) => {
    const selection: StudioSelection = {
      componentName: node.name,
      elementTag: node.tag,
      filePath: node.filePath,
      lineNumber: node.lineNumber,
      props: {},
      styles: {},
    };
    setSelectedElement(selection);
  }, [setSelectedElement]);

  const renderNode = (node: ComponentNode, key: string): React.ReactNode => {
    const isExpanded = expanded.has(key);
    const isSelected = selectedElement?.componentName === node.name && selectedElement?.filePath === node.filePath;
    const hasChildren = node.children.length > 0;
    const matchesFilter = !filter || node.name.toLowerCase().includes(filter.toLowerCase());

    if (!matchesFilter && !node.children.some(c => matchesChild(c, filter))) {
      return null;
    }

    return (
      <div key={key}>
        <button
          onClick={() => handleSelect(node)}
          className="flex items-center gap-1 w-full text-left py-0.5 hover:opacity-80 transition-opacity"
          style={{
            paddingLeft: node.depth * 16 + 8,
            background: isSelected ? 'var(--t-surface2)' : 'transparent',
          }}
        >
          {/* Expand toggle */}
          {hasChildren ? (
            <svg
              className={`w-3 h-3 flex-shrink-0 transition-transform cursor-pointer ${isExpanded ? 'rotate-90' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
              style={{ color: 'var(--t-muted)' }}
              onClick={(e) => { e.stopPropagation(); toggleExpand(key); }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          ) : (
            <span className="w-3 flex-shrink-0" />
          )}

          {/* Component icon */}
          <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}
            style={{ color: isSelected ? 'var(--t-primary)' : node.name[0] === node.name[0].toUpperCase() ? 'var(--t-accent1)' : 'var(--t-muted)' }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
          </svg>

          {/* Name */}
          <span className="text-xs truncate" style={{ color: isSelected ? 'var(--t-primary)' : 'var(--t-text)' }}>
            {node.name}
          </span>

          {/* Tag */}
          <span className="text-xs flex-shrink-0" style={{ color: 'var(--t-muted)', fontSize: 10 }}>
            &lt;{node.tag}&gt;
          </span>
        </button>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div>
            {node.children.map((child, i) => renderNode(child, `${key}-${i}`))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Search */}
      <div className="flex-shrink-0 p-2" style={{ borderBottom: '1px solid var(--t-border)' }}>
        <input
          type="text"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Filter components..."
          className="w-full px-2 py-1 rounded text-xs outline-none"
          style={{
            background: 'var(--t-surface)',
            color: 'var(--t-text)',
            border: '1px solid var(--t-border)',
          }}
        />
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto py-1">
        {tree.length === 0 ? (
          <div className="flex items-center justify-center h-full p-4">
            <p className="text-xs text-center" style={{ color: 'var(--t-muted)' }}>
              No components found. Generate an app first.
            </p>
          </div>
        ) : (
          tree.map((node, i) => renderNode(node, `root-${i}`))
        )}
      </div>

      {/* Stats footer */}
      <div
        className="flex-shrink-0 px-3 py-1.5 text-xs"
        style={{ color: 'var(--t-muted)', borderTop: '1px solid var(--t-border)' }}
      >
        {countNodes(tree)} components
      </div>
    </div>
  );
};

/** Parse a file for component definitions */
function parseComponents(filePath: string, content: string): ComponentNode[] {
  const components: ComponentNode[] = [];
  const lines = content.split('\n');

  // Match function components: function Name() or const Name = () => or const Name: React.FC
  const funcRegex = /^(?:export\s+)?(?:default\s+)?(?:function\s+|const\s+)(\w+)\s*(?::\s*React\.FC[^=]*)?(?:\s*=\s*(?:\([^)]*\)|[^=])*=>|\s*\()/;

  for (let i = 0; i < lines.length; i++) {
    const match = lines[i].match(funcRegex);
    if (match) {
      const name = match[1];
      // Skip non-component names (lowercase first letter usually means helper)
      if (name[0] !== name[0].toUpperCase()) continue;

      // Find JSX children used in this component
      const children = findJSXChildren(content, i, lines);

      components.push({
        name,
        tag: name,
        filePath,
        lineNumber: i + 1,
        children,
        depth: 0,
      });
    }
  }

  return components;
}

/** Find JSX component references within a component body */
function findJSXChildren(content: string, startLine: number, lines: string[]): ComponentNode[] {
  const children: ComponentNode[] = [];
  const seen = new Set<string>();

  // Simple JSX tag detection: <ComponentName or <ComponentName>
  const jsxRegex = /<([A-Z][A-Za-z0-9]*)/g;

  // Scan from the component start to the next component or end of file
  let braceDepth = 0;
  let started = false;

  for (let i = startLine; i < lines.length; i++) {
    const line = lines[i];

    for (const ch of line) {
      if (ch === '{') braceDepth++;
      if (ch === '}') {
        braceDepth--;
        if (started && braceDepth === 0) return children;
      }
    }

    if (line.includes('{') && !started) started = true;

    let match;
    while ((match = jsxRegex.exec(line)) !== null) {
      const childName = match[1];
      if (!seen.has(childName) && childName !== 'React') {
        seen.add(childName);
        children.push({
          name: childName,
          tag: childName.toLowerCase(),
          filePath: '',
          lineNumber: i + 1,
          children: [],
          depth: 1,
        });
      }
    }
  }

  return children;
}

/** Build hierarchy from flat component list */
function buildHierarchy(components: ComponentNode[], files: Record<string, any>): ComponentNode[] {
  // Find the entry point (App component)
  const appComponent = components.find(c => c.name === 'App') || components[0];
  if (!appComponent) return [];

  // Set correct depths
  const setDepths = (node: ComponentNode, depth: number) => {
    node.depth = depth;
    // Resolve children file paths
    node.children.forEach(child => {
      const resolved = components.find(c => c.name === child.name);
      if (resolved) {
        child.filePath = resolved.filePath;
        child.lineNumber = resolved.lineNumber;
        child.children = resolved.children.map(gc => ({ ...gc }));
      }
      setDepths(child, depth + 1);
    });
  };

  const rootCopy = { ...appComponent, children: appComponent.children.map(c => ({ ...c })) };
  setDepths(rootCopy, 0);

  return [rootCopy];
}

/** Check if a node or its children match a filter */
function matchesChild(node: ComponentNode, filter: string): boolean {
  if (node.name.toLowerCase().includes(filter.toLowerCase())) return true;
  return node.children.some(c => matchesChild(c, filter));
}

/** Count total nodes in tree */
function countNodes(nodes: ComponentNode[]): number {
  let count = nodes.length;
  for (const node of nodes) {
    count += countNodes(node.children);
  }
  return count;
}

export default StudioComponentTree;
