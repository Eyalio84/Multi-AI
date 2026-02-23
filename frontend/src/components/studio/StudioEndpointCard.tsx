/** StudioEndpointCard — Single API endpoint display */
import React, { useState } from 'react';
import type { StudioApiEndpoint } from '../../types/studio';

interface Props {
  endpoint: StudioApiEndpoint;
}

const METHOD_COLORS: Record<string, string> = {
  GET: '#22c55e',
  POST: '#3b82f6',
  PUT: '#f59e0b',
  PATCH: '#f97316',
  DELETE: '#ef4444',
};

const StudioEndpointCard: React.FC<Props> = ({ endpoint }) => {
  const [expanded, setExpanded] = useState(false);
  const methodColor = METHOD_COLORS[endpoint.method] || 'var(--t-muted)';

  const hasDetails = (endpoint.parameters && endpoint.parameters.length > 0) ||
    endpoint.requestBody ||
    (endpoint.responses && Object.keys(endpoint.responses).length > 0);

  return (
    <div
      className="rounded overflow-hidden"
      style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}
    >
      {/* Header */}
      <button
        onClick={() => hasDetails && setExpanded(!expanded)}
        className="flex items-center gap-2 w-full text-left px-3 py-2 hover:opacity-90 transition-opacity"
      >
        {/* Method badge */}
        <span
          className="text-xs font-bold px-2 py-0.5 rounded flex-shrink-0"
          style={{ background: methodColor, color: '#fff', minWidth: 52, textAlign: 'center' }}
        >
          {endpoint.method}
        </span>

        {/* Path */}
        <span
          className="text-xs flex-1 truncate"
          style={{ color: 'var(--t-text)', fontFamily: 'var(--t-font-mono)' }}
        >
          {endpoint.path}
        </span>

        {/* Summary */}
        {endpoint.summary && (
          <span className="text-xs truncate hidden sm:inline" style={{ color: 'var(--t-muted)', maxWidth: 200 }}>
            {endpoint.summary}
          </span>
        )}

        {/* Expand arrow */}
        {hasDetails && (
          <svg
            className={`w-3 h-3 flex-shrink-0 transition-transform ${expanded ? 'rotate-90' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
            style={{ color: 'var(--t-muted)' }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        )}
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="px-3 pb-3 space-y-2" style={{ borderTop: '1px solid var(--t-border)' }}>
          {/* Parameters */}
          {endpoint.parameters && endpoint.parameters.length > 0 && (
            <div className="mt-2">
              <h5 className="text-xs font-medium mb-1" style={{ color: 'var(--t-text2)' }}>Parameters</h5>
              <div className="space-y-1">
                {endpoint.parameters.map((param: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span style={{ color: 'var(--t-primary)', fontFamily: 'var(--t-font-mono)' }}>{param.name}</span>
                    <span className="px-1 rounded" style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)', fontSize: 10 }}>
                      {param.in}
                    </span>
                    <span style={{ color: 'var(--t-muted)' }}>{param.schema?.type || 'string'}</span>
                    {param.required && (
                      <span className="px-1 rounded" style={{ background: 'var(--t-error)', color: '#fff', fontSize: 10 }}>req</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Request body */}
          {endpoint.requestBody && (
            <div>
              <h5 className="text-xs font-medium mb-1" style={{ color: 'var(--t-text2)' }}>Request Body</h5>
              <pre
                className="text-xs p-2 rounded overflow-x-auto"
                style={{
                  background: 'var(--t-bg)',
                  color: 'var(--t-text)',
                  fontFamily: 'var(--t-font-mono)',
                  maxHeight: 120,
                }}
              >
                {JSON.stringify(
                  endpoint.requestBody?.content?.['application/json']?.schema || endpoint.requestBody,
                  null, 2
                )}
              </pre>
            </div>
          )}

          {/* Responses */}
          {endpoint.responses && Object.keys(endpoint.responses).length > 0 && (
            <div>
              <h5 className="text-xs font-medium mb-1" style={{ color: 'var(--t-text2)' }}>Responses</h5>
              <div className="space-y-1">
                {Object.entries(endpoint.responses).map(([code, resp]: [string, any]) => (
                  <div key={code} className="flex items-start gap-2 text-xs">
                    <span
                      className="px-1.5 py-0.5 rounded flex-shrink-0 font-medium"
                      style={{
                        background: code.startsWith('2') ? 'var(--t-success)' : code.startsWith('4') ? 'var(--t-warning)' : 'var(--t-error)',
                        color: '#fff',
                      }}
                    >
                      {code}
                    </span>
                    <span style={{ color: 'var(--t-muted)' }}>{resp.description || ''}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StudioEndpointCard;
