/** StudioVersionHistory — Version browser with preview and restore */
import React, { useEffect, useState, useMemo } from 'react';
import { useStudio } from '../../context/StudioContext';
import * as studioApi from '../../services/studioApiService';
import type { StudioVersion, StudioFile } from '../../types/studio';

const StudioVersionHistory: React.FC = () => {
  const { versions, loadVersions, restoreVersion, project, isLoading, files } = useStudio();
  const [previewVersion, setPreviewVersion] = useState<StudioVersion | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [restoring, setRestoring] = useState(false);

  // Load versions on mount
  useEffect(() => {
    if (project) {
      loadVersions();
    }
  }, [project, loadVersions]);

  // Sort versions newest first
  const sortedVersions = useMemo(() => {
    return [...versions].sort((a, b) => b.versionNumber - a.versionNumber);
  }, [versions]);

  const handlePreview = async (version: StudioVersion) => {
    if (!project) return;
    setLoadingPreview(true);
    try {
      // If full files are already in the version object, use them
      if (version.files && Object.keys(version.files).length > 0) {
        setPreviewVersion(version);
      } else {
        // Otherwise fetch full version data
        const fullVersion = await studioApi.getVersion(project.id, version.versionNumber);
        setPreviewVersion(fullVersion);
      }
    } catch (err) {
      console.error('Failed to load version preview:', err);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleRestore = async (versionNumber: number) => {
    if (!project || restoring) return;
    setRestoring(true);
    try {
      await restoreVersion(versionNumber);
      setPreviewVersion(null);
    } catch (err) {
      console.error('Failed to restore version:', err);
    } finally {
      setRestoring(false);
    }
  };

  const formatTimestamp = (ts: string): string => {
    const date = new Date(ts);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 h-8 flex-shrink-0"
        style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
      >
        <span className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>Version History</span>
        <span className="text-xs" style={{ color: 'var(--t-muted)' }}>{versions.length} versions</span>
      </div>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Version list */}
        <div className="flex-1 overflow-y-auto">
          {sortedVersions.length === 0 ? (
            <div className="flex items-center justify-center h-full p-4">
              <p className="text-xs text-center" style={{ color: 'var(--t-muted)' }}>
                No versions yet. Save your project to create the first version.
              </p>
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {sortedVersions.map(version => {
                const isActive = previewVersion?.versionNumber === version.versionNumber;
                const isCurrent = project && version.versionNumber === project.currentVersion;

                return (
                  <div
                    key={version.id}
                    className="rounded p-2.5 cursor-pointer transition-colors"
                    style={{
                      background: isActive ? 'var(--t-surface2)' : 'var(--t-surface)',
                      border: `1px solid ${isActive ? 'var(--t-primary)' : 'var(--t-border)'}`,
                    }}
                    onClick={() => handlePreview(version)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-medium" style={{ color: 'var(--t-text)' }}>
                          v{version.versionNumber}
                        </span>
                        {isCurrent && (
                          <span
                            className="text-xs px-1 rounded"
                            style={{ background: 'var(--t-primary)', color: '#fff', fontSize: 10 }}
                          >
                            current
                          </span>
                        )}
                      </div>
                      <span className="text-xs" style={{ color: 'var(--t-muted)' }}>
                        {formatTimestamp(version.timestamp)}
                      </span>
                    </div>

                    <p className="text-xs truncate" style={{ color: 'var(--t-muted)' }}>
                      {version.message || 'No description'}
                    </p>

                    {/* Action buttons when previewing */}
                    {isActive && !isCurrent && (
                      <button
                        onClick={(e) => { e.stopPropagation(); handleRestore(version.versionNumber); }}
                        disabled={restoring || isLoading}
                        className="mt-2 w-full py-1.5 rounded text-xs font-medium transition-colors disabled:opacity-40"
                        style={{ background: 'var(--t-warning)', color: '#000' }}
                      >
                        {restoring ? 'Restoring...' : 'Restore This Version'}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Preview panel */}
        {previewVersion && (
          <div
            className="flex-1 overflow-y-auto flex flex-col"
            style={{ borderLeft: '1px solid var(--t-border)' }}
          >
            <div
              className="flex items-center px-3 h-8 flex-shrink-0"
              style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
            >
              <span className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>
                Files in v{previewVersion.versionNumber}
              </span>
              <button
                onClick={() => setPreviewVersion(null)}
                className="ml-auto p-1 rounded hover:opacity-80"
                style={{ color: 'var(--t-muted)' }}
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {loadingPreview ? (
              <div className="flex items-center justify-center h-full">
                <span className="text-xs" style={{ color: 'var(--t-muted)' }}>Loading...</span>
              </div>
            ) : (
              <div className="p-2 space-y-1">
                {previewVersion.files && Object.entries(previewVersion.files).map(([path, file]) => {
                  const currentFile = files[path];
                  const isDifferent = currentFile && currentFile.content !== file.content;
                  const isNew = !currentFile;

                  return (
                    <div
                      key={path}
                      className="flex items-center gap-2 px-2 py-1.5 rounded text-xs"
                      style={{ background: 'var(--t-bg)' }}
                    >
                      <span className="truncate flex-1" style={{ color: 'var(--t-text)', fontFamily: 'var(--t-font-mono)' }}>
                        {path}
                      </span>
                      {isDifferent && (
                        <span className="px-1 rounded flex-shrink-0" style={{ background: 'var(--t-warning)', color: '#000', fontSize: 10 }}>
                          modified
                        </span>
                      )}
                      {isNew && (
                        <span className="px-1 rounded flex-shrink-0" style={{ background: 'var(--t-success)', color: '#fff', fontSize: 10 }}>
                          added
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default StudioVersionHistory;
