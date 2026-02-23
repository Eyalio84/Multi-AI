/** StudioExportDialog — Export modal for downloading project as ZIP or copying files */
import React, { useState, useCallback } from 'react';
import { useStudio } from '../../context/StudioContext';
import * as studioApi from '../../services/studioApiService';

interface Props {
  isOpen?: boolean;
  onClose?: () => void;
}

type ExportScope = 'frontend' | 'fullstack';

const StudioExportDialog: React.FC<Props> = ({ isOpen = true, onClose }) => {
  const { project, files } = useStudio();
  const [scope, setScope] = useState<ExportScope>('fullstack');
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedFile, setCopiedFile] = useState<string | null>(null);

  const handleDownloadZip = useCallback(async () => {
    if (!project) return;
    setExporting(true);
    setError(null);

    try {
      const blob = await studioApi.exportProject(project.id, scope);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${project.name.replace(/\s+/g, '-').toLowerCase()}-${scope}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || 'Export failed');
    } finally {
      setExporting(false);
    }
  }, [project, scope]);

  const handleCopyFile = useCallback(async (path: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedFile(path);
      setTimeout(() => setCopiedFile(null), 2000);
    } catch {
      // Fallback for environments without clipboard API
      const textarea = document.createElement('textarea');
      textarea.value = content;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopiedFile(path);
      setTimeout(() => setCopiedFile(null), 2000);
    }
  }, []);

  if (!isOpen) return null;

  const fileEntries = Object.entries(files);

  return (
    <div className="p-4 space-y-4">
          {/* Download ZIP section */}
          <div>
            <h4 className="text-xs font-medium mb-2" style={{ color: 'var(--t-text2)' }}>Download as ZIP</h4>

            {/* Scope selector */}
            <div className="flex gap-2 mb-3">
              {(['frontend', 'fullstack'] as ExportScope[]).map(s => (
                <button
                  key={s}
                  onClick={() => setScope(s)}
                  className="flex-1 py-2 rounded text-xs font-medium capitalize transition-colors"
                  style={{
                    background: scope === s ? 'var(--t-primary)' : 'var(--t-surface2)',
                    color: scope === s ? '#fff' : 'var(--t-muted)',
                    border: `1px solid ${scope === s ? 'var(--t-primary)' : 'var(--t-border)'}`,
                  }}
                >
                  {s === 'frontend' ? 'Frontend Only' : 'Full Stack'}
                </button>
              ))}
            </div>

            <button
              onClick={handleDownloadZip}
              disabled={exporting || !project}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded text-xs font-medium transition-colors disabled:opacity-40"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {exporting ? 'Exporting...' : 'Download ZIP'}
            </button>

            {error && (
              <p className="text-xs mt-1" style={{ color: 'var(--t-error)' }}>{error}</p>
            )}
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px" style={{ background: 'var(--t-border)' }} />
            <span className="text-xs" style={{ color: 'var(--t-muted)' }}>or copy individual files</span>
            <div className="flex-1 h-px" style={{ background: 'var(--t-border)' }} />
          </div>

          {/* Individual files */}
          <div className="space-y-1">
            {fileEntries.length === 0 ? (
              <p className="text-xs text-center p-4" style={{ color: 'var(--t-muted)' }}>No files to export</p>
            ) : (
              fileEntries.map(([path, file]) => (
                <div
                  key={path}
                  className="flex items-center justify-between px-2 py-1.5 rounded"
                  style={{ background: 'var(--t-bg)' }}
                >
                  <span
                    className="text-xs truncate flex-1 mr-2"
                    style={{ color: 'var(--t-text)', fontFamily: 'var(--t-font-mono)' }}
                  >
                    {path}
                  </span>
                  <button
                    onClick={() => handleCopyFile(path, file.content)}
                    className="flex items-center gap-1 px-2 py-0.5 rounded text-xs transition-colors flex-shrink-0"
                    style={{
                      background: copiedFile === path ? 'var(--t-success)' : 'var(--t-surface2)',
                      color: copiedFile === path ? '#fff' : 'var(--t-muted)',
                    }}
                  >
                    {copiedFile === path ? (
                      <>
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        Copied
                      </>
                    ) : (
                      <>
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        Copy
                      </>
                    )}
                  </button>
                </div>
              ))
            )}
          </div>
    </div>
  );
};

export default StudioExportDialog;
