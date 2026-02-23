/** StudioApiTester — Send test requests to the mock server */
import React, { useState, useMemo } from 'react';
import { useStudio } from '../../context/StudioContext';
import type { StudioApiEndpoint } from '../../types/studio';

const StudioApiTester: React.FC = () => {
  const { apiSpec, mockServerStatus } = useStudio();

  const [selectedIdx, setSelectedIdx] = useState(0);
  const [requestBody, setRequestBody] = useState('{}');
  const [response, setResponse] = useState<string | null>(null);
  const [responseStatus, setResponseStatus] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Parse endpoints
  const endpoints = useMemo((): StudioApiEndpoint[] => {
    if (!apiSpec?.paths) return [];
    const result: StudioApiEndpoint[] = [];
    for (const [path, methods] of Object.entries(apiSpec.paths)) {
      for (const [method, details] of Object.entries(methods as Record<string, any>)) {
        if (['get', 'post', 'put', 'patch', 'delete'].includes(method.toLowerCase())) {
          result.push({
            method: method.toUpperCase(),
            path,
            summary: details.summary || '',
            parameters: details.parameters || [],
            requestBody: details.requestBody || null,
            responses: details.responses || {},
          });
        }
      }
    }
    return result;
  }, [apiSpec]);

  const selectedEndpoint = endpoints[selectedIdx] || null;

  const handleSend = async () => {
    if (!selectedEndpoint || !mockServerStatus.running || !mockServerStatus.port) return;

    setLoading(true);
    setError(null);
    setResponse(null);
    setResponseStatus(null);

    try {
      const url = `http://localhost:${mockServerStatus.port}${selectedEndpoint.path}`;
      const hasBody = ['POST', 'PUT', 'PATCH'].includes(selectedEndpoint.method);

      const fetchOptions: RequestInit = {
        method: selectedEndpoint.method,
        headers: { 'Content-Type': 'application/json' },
      };

      if (hasBody) {
        try {
          JSON.parse(requestBody); // Validate JSON
          fetchOptions.body = requestBody;
        } catch {
          setError('Invalid JSON in request body');
          setLoading(false);
          return;
        }
      }

      const res = await fetch(url, fetchOptions);
      setResponseStatus(res.status);
      const text = await res.text();

      try {
        const json = JSON.parse(text);
        setResponse(JSON.stringify(json, null, 2));
      } catch {
        setResponse(text);
      }
    } catch (err: any) {
      setError(err.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  if (!apiSpec) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <p className="text-xs" style={{ color: 'var(--t-muted)' }}>No API spec available</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--t-bg)' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 h-8 flex-shrink-0"
        style={{ background: 'var(--t-surface)', borderBottom: '1px solid var(--t-border)' }}
      >
        <span className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>API Tester</span>
        <span className="text-xs" style={{ color: mockServerStatus.running ? 'var(--t-success)' : 'var(--t-error)' }}>
          {mockServerStatus.running ? `Mock :${mockServerStatus.port}` : 'Mock server offline'}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* Endpoint selector */}
        <div>
          <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--t-text2)' }}>Endpoint</label>
          <select
            value={selectedIdx}
            onChange={e => setSelectedIdx(Number(e.target.value))}
            className="w-full px-2 py-1.5 rounded text-xs outline-none"
            style={{
              background: 'var(--t-surface)',
              color: 'var(--t-text)',
              border: '1px solid var(--t-border)',
              fontFamily: 'var(--t-font-mono)',
            }}
          >
            {endpoints.map((ep, i) => (
              <option key={i} value={i}>{ep.method} {ep.path}</option>
            ))}
          </select>
        </div>

        {/* Request body (for POST/PUT/PATCH) */}
        {selectedEndpoint && ['POST', 'PUT', 'PATCH'].includes(selectedEndpoint.method) && (
          <div>
            <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--t-text2)' }}>Request Body (JSON)</label>
            <textarea
              value={requestBody}
              onChange={e => setRequestBody(e.target.value)}
              rows={6}
              spellCheck={false}
              className="w-full px-2 py-1.5 rounded text-xs outline-none resize-none"
              style={{
                background: 'var(--t-surface)',
                color: 'var(--t-text)',
                border: '1px solid var(--t-border)',
                fontFamily: 'var(--t-font-mono)',
              }}
            />
          </div>
        )}

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={loading || !mockServerStatus.running || !selectedEndpoint}
          className="w-full py-2 rounded text-xs font-medium transition-colors disabled:opacity-40"
          style={{ background: 'var(--t-primary)', color: '#fff' }}
        >
          {loading ? 'Sending...' : 'Send Request'}
        </button>

        {/* Error */}
        {error && (
          <div className="text-xs p-2 rounded" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--t-error)' }}>
            {error}
          </div>
        )}

        {/* Response */}
        {response !== null && (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <label className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>Response</label>
              {responseStatus !== null && (
                <span
                  className="text-xs px-1.5 py-0.5 rounded font-medium"
                  style={{
                    background: responseStatus < 300 ? 'var(--t-success)' : responseStatus < 500 ? 'var(--t-warning)' : 'var(--t-error)',
                    color: '#fff',
                  }}
                >
                  {responseStatus}
                </span>
              )}
            </div>
            <pre
              className="text-xs p-2 rounded overflow-auto max-h-64"
              style={{
                background: 'var(--t-surface)',
                color: 'var(--t-text)',
                fontFamily: 'var(--t-font-mono)',
                border: '1px solid var(--t-border)',
              }}
            >
              {response}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudioApiTester;
