/** StudioPage — Top-level: mode tabs, panel layout, StudioContext provider */
import React, { useEffect, useState } from 'react';
import { useAppContext } from '../context/AppContext';
import { StudioProvider, useStudio } from '../context/StudioContext';
import StudioToolbar from '../components/studio/StudioToolbar';
import StudioLayout from '../components/studio/StudioLayout';
import StudioChatPanel from '../components/studio/StudioChatPanel';
import StudioPreviewPanel from '../components/studio/StudioPreviewPanel';
import StudioFilesPanel from '../components/studio/StudioFilesPanel';
import StudioCodeEditor from '../components/studio/StudioCodeEditor';
import StudioVisualMode from '../components/studio/StudioVisualMode';
import StudioWelcome from '../components/studio/StudioWelcome';
import StudioErrorBoundary from '../components/studio/StudioErrorBoundary';
import StudioMobileLayout from '../components/studio/StudioMobileLayout';
import StudioExportDialog from '../components/studio/StudioExportDialog';
import StudioVersionHistory from '../components/studio/StudioVersionHistory';
import StudioProjectSettings from '../components/studio/StudioProjectSettings';
import StudioApiPanel from '../components/studio/StudioApiPanel';
import StudioPipelineConfig from '../components/studio/StudioPipelineConfig';

type OverlayPanel = null | 'export' | 'versions' | 'settings' | 'api' | 'pipeline';

const StudioContent: React.FC = () => {
  const { mode, project, loadProjectList, apiSpec } = useStudio();
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [overlay, setOverlay] = useState<OverlayPanel>(null);

  useEffect(() => {
    loadProjectList();
  }, [loadProjectList]);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Show welcome screen if no project
  if (!project) {
    return (
      <div className="flex flex-col h-full">
        <StudioToolbar />
        <div className="flex-1 overflow-hidden">
          <StudioWelcome />
        </div>
      </div>
    );
  }

  // Mobile layout — bottom tab bar handles mode switching, hide top secondary bar
  if (isMobile) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex-1 overflow-hidden">
          <StudioMobileLayout />
        </div>
      </div>
    );
  }

  // Desktop layouts by mode
  const renderByMode = () => {
    switch (mode) {
      case 'chat':
        return (
          <StudioLayout
            left={<StudioChatPanel />}
            center={<StudioPreviewPanel />}
            right={<StudioFilesPanel />}
          />
        );

      case 'code':
        return (
          <StudioLayout
            left={<StudioFilesPanel />}
            center={<StudioCodeEditor />}
            right={<StudioPreviewPanel />}
          />
        );

      case 'visual':
        return (
          <StudioLayout
            left={<StudioChatPanel />}
            center={<StudioVisualMode />}
            right={<StudioFilesPanel />}
          />
        );

      default:
        return (
          <StudioLayout
            left={<StudioChatPanel />}
            center={<StudioPreviewPanel />}
            right={<StudioFilesPanel />}
          />
        );
    }
  };

  // Overlay panel renderer
  const renderOverlay = () => {
    if (!overlay) return null;

    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{ background: 'rgba(0,0,0,0.5)' }}
        onClick={() => setOverlay(null)}
      >
        <div
          className="rounded-lg shadow-2xl overflow-hidden"
          style={{
            background: 'var(--t-surface)',
            border: '1px solid var(--t-border)',
            width: overlay === 'api' ? '90vw' : '600px',
            maxWidth: '90vw',
            maxHeight: '85vh',
          }}
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between px-4 py-2"
            style={{ borderBottom: '1px solid var(--t-border)' }}
          >
            <span className="text-sm font-medium" style={{ color: 'var(--t-text)' }}>
              {overlay === 'export' && 'Export Project'}
              {overlay === 'versions' && 'Version History'}
              {overlay === 'settings' && 'Project Settings'}
              {overlay === 'api' && 'API Contracts'}
              {overlay === 'pipeline' && 'Pipeline Config'}
            </span>
            <button
              onClick={() => setOverlay(null)}
              className="p-1 rounded hover:opacity-80"
              style={{ color: 'var(--t-muted)' }}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="overflow-y-auto" style={{ maxHeight: 'calc(85vh - 48px)' }}>
            {overlay === 'export' && <StudioExportDialog onClose={() => setOverlay(null)} />}
            {overlay === 'versions' && <StudioVersionHistory />}
            {overlay === 'settings' && <StudioProjectSettings />}
            {overlay === 'api' && <StudioApiPanel />}
            {overlay === 'pipeline' && <StudioPipelineConfig />}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      <StudioToolbar />

      {/* Secondary action bar */}
      <div
        className="flex items-center gap-1 px-3 h-8 flex-shrink-0"
        style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
      >
        <button
          onClick={() => setOverlay('versions')}
          className="text-xs px-2 py-0.5 rounded transition-colors hover:opacity-80"
          style={{ color: 'var(--t-muted)' }}
        >
          History
        </button>
        <button
          onClick={() => setOverlay('settings')}
          className="text-xs px-2 py-0.5 rounded transition-colors hover:opacity-80"
          style={{ color: 'var(--t-muted)' }}
        >
          Settings
        </button>
        <button
          onClick={() => setOverlay('pipeline')}
          className="text-xs px-2 py-0.5 rounded transition-colors hover:opacity-80"
          style={{ color: 'var(--t-accent1)' }}
        >
          Pipeline
        </button>
        {apiSpec && (
          <button
            onClick={() => setOverlay('api')}
            className="text-xs px-2 py-0.5 rounded transition-colors hover:opacity-80"
            style={{ color: 'var(--t-accent1)' }}
          >
            API
          </button>
        )}
        <div className="flex-1" />
        <button
          onClick={() => setOverlay('export')}
          className="text-xs px-2 py-0.5 rounded transition-colors"
          style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)' }}
        >
          Export
        </button>
      </div>

      <div className="flex-1 overflow-hidden">
        {renderByMode()}
      </div>

      {renderOverlay()}
    </div>
  );
};

const StudioPage: React.FC = () => {
  const { activeProvider, activeModel } = useAppContext();

  return (
    <StudioErrorBoundary>
      <StudioProvider initialProvider={activeProvider} initialModel={activeModel}>
        <StudioContent />
      </StudioProvider>
    </StudioErrorBoundary>
  );
};

export default StudioPage;
