/** StudioPreviewPanel — SandpackProvider wrapper, dark theme, console, error overlay */
import React, { useMemo, useState } from 'react';
import {
  SandpackProvider,
  SandpackLayout,
  SandpackPreview,
  SandpackConsole,
} from '@codesandbox/sandpack-react';
import { useStudio } from '../../context/StudioContext';

const StudioPreviewPanel: React.FC = () => {
  const { files, mode } = useStudio();
  const [showConsole, setShowConsole] = useState(false);

  // Convert studio files to Sandpack file format
  const sandpackFiles = useMemo(() => {
    const result: Record<string, { code: string; active?: boolean }> = {};

    const fileEntries = Object.entries(files);
    if (fileEntries.length === 0) {
      // Default empty state
      result['/App.js'] = {
        code: `export default function App() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontFamily: 'system-ui', color: '#888', background: '#111827' }}>
      <div style={{ textAlign: 'center' }}>
        <h2 style={{ color: '#0ea5e9', marginBottom: 8 }}>Studio Preview</h2>
        <p>Describe your app in the chat to get started</p>
      </div>
    </div>
  );
}`,
        active: true,
      };
      return result;
    }

    for (const [path, file] of fileEntries) {
      // Sandpack expects paths starting with /
      const sandpackPath = path.startsWith('/') ? path : `/${path}`;
      result[sandpackPath] = { code: file.content };
    }

    // Ensure we have an entry point
    if (!result['/App.js'] && !result['/App.tsx'] && !result['/App.jsx']) {
      // Check for src/ prefixed entries
      if (result['/src/App.tsx']) {
        // Already has src structure - Sandpack will find it
      } else if (result['/src/App.js']) {
        // ok
      } else {
        // Create a simple App wrapper
        result['/App.js'] = {
          code: `export default function App() {
  return <div>Preview loading...</div>;
}`,
        };
      }
    }

    return result;
  }, [files]);

  // Compute dependencies from files
  const customDeps = useMemo(() => {
    const deps: Record<string, string> = {};
    // Check for package.json in files
    const pkgFile = files['package.json'] || files['/package.json'];
    if (pkgFile) {
      try {
        const pkg = JSON.parse(pkgFile.content);
        if (pkg.dependencies) {
          Object.assign(deps, pkg.dependencies);
        }
      } catch {}
    }
    return deps;
  }, [files]);

  const hasFiles = Object.keys(files).length > 0;

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 h-8 flex-shrink-0"
        style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
      >
        <span className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>
          Preview
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowConsole(!showConsole)}
            className="text-xs px-2 py-0.5 rounded transition-colors"
            style={{
              background: showConsole ? 'var(--t-primary)' : 'var(--t-surface2)',
              color: showConsole ? '#fff' : 'var(--t-muted)',
            }}
          >
            Console
          </button>
        </div>
      </div>

      {/* Sandpack — use absolute positioning to force full height */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <div className="studio-sandpack-wrapper" style={{ position: 'absolute', inset: 0 }}>
          <SandpackProvider
            template="react"
            files={sandpackFiles}
            customSetup={{
              dependencies: {
                ...customDeps,
              },
            }}
            theme={{
              colors: {
                surface1: '#111827',
                surface2: '#1f2937',
                surface3: '#374151',
                clickable: '#6b7280',
                base: '#f1f5f9',
                disabled: '#374151',
                hover: '#0ea5e9',
                accent: '#0ea5e9',
                error: '#ef4444',
                errorSurface: '#7f1d1d',
              },
              syntax: {
                plain: '#f1f5f9',
                comment: { color: '#6b7280', fontStyle: 'italic' },
                keyword: '#c084fc',
                tag: '#22c55e',
                punctuation: '#6b7280',
                definition: '#38bdf8',
                property: '#fbbf24',
                static: '#f472b6',
                string: '#a5f3fc',
              },
              font: {
                body: "system-ui, -apple-system, sans-serif",
                mono: "'Menlo', 'Monaco', 'Courier New', monospace",
                size: '13px',
                lineHeight: '1.5',
              },
            }}
            options={{
              recompileMode: 'delayed',
              recompileDelay: 500,
            }}
          >
            <SandpackLayout>
              <SandpackPreview
                showNavigator={false}
                showRefreshButton={hasFiles}
                showOpenInCodeSandbox={false}
              />
              {showConsole && (
                <SandpackConsole />
              )}
            </SandpackLayout>
          </SandpackProvider>
        </div>
        {/* Force the entire Sandpack tree to fill available height */}
        <style>{`
          .studio-sandpack-wrapper,
          .studio-sandpack-wrapper > .sp-wrapper,
          .studio-sandpack-wrapper > div {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
          }
          .studio-sandpack-wrapper .sp-layout {
            flex: 1 !important;
            height: 100% !important;
            max-height: none !important;
            border: none !important;
            border-radius: 0 !important;
            display: flex !important;
            flex-direction: column !important;
          }
          .studio-sandpack-wrapper .sp-stack {
            flex: 1 !important;
            height: 100% !important;
            max-height: none !important;
          }
          .studio-sandpack-wrapper .sp-preview-container {
            flex: 1 !important;
            height: 100% !important;
            max-height: none !important;
          }
          .studio-sandpack-wrapper .sp-preview-iframe {
            height: 100% !important;
            min-height: 0 !important;
          }
          .studio-sandpack-wrapper .sp-preview-actions {
            z-index: 10;
          }
        `}</style>
      </div>
    </div>
  );
};

export default StudioPreviewPanel;
