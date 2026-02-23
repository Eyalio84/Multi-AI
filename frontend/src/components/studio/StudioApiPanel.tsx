/** StudioApiPanel — API contract viewer showing endpoints and schemas */
import React, { useState, useMemo } from 'react';
import { useStudio } from '../../context/StudioContext';
import StudioEndpointCard from './StudioEndpointCard';
import type { StudioApiEndpoint } from '../../types/studio';

type TabId = 'endpoints' | 'schemas' | 'types';

const StudioApiPanel: React.FC = () => {
  const { apiSpec, mockServerStatus, startMockServer, stopMockServer } = useStudio();
  const [activeTab, setActiveTab] = useState<TabId>('endpoints');
  const [filterMethod, setFilterMethod] = useState<string>('all');

  // Parse endpoints from spec.paths
  const endpoints = useMemo((): StudioApiEndpoint[] => {
    if (!apiSpec?.paths) return [];
    const result: StudioApiEndpoint[] = [];

    for (const [path, methods] of Object.entries(apiSpec.paths)) {
      for (const [method, details] of Object.entries(methods as Record<string, any>)) {
        if (['get', 'post', 'put', 'patch', 'delete'].includes(method.toLowerCase())) {
          result.push({
            method: method.toUpperCase(),
            path,
            summary: details.summary || details.description || '',
            parameters: details.parameters || [],
            requestBody: details.requestBody || null,
            responses: details.responses || {},
          });
        }
      }
    }

    return result;
  }, [apiSpec]);

  // Filter endpoints by method
  const filteredEndpoints = useMemo(() => {
    if (filterMethod === 'all') return endpoints;
    return endpoints.filter(e => e.method === filterMethod);
  }, [endpoints, filterMethod]);

  // Generate TypeScript interfaces from schemas
  const generatedTypes = useMemo((): string => {
    if (!apiSpec?.components?.schemas) return '// No schemas defined';
    const lines: string[] = [];

    for (const [name, schema] of Object.entries(apiSpec.components.schemas as Record<string, any>)) {
      lines.push(`export interface ${name} {`);

      if (schema.properties) {
        const required = new Set(schema.required || []);
        for (const [prop, propSchema] of Object.entries(schema.properties as Record<string, any>)) {
          const optional = required.has(prop) ? '' : '?';
          const tsType = jsonSchemaToTS(propSchema);
          lines.push(`  ${prop}${optional}: ${tsType};`);
        }
      }

      lines.push('}');
      lines.push('');
    }

    return lines.join('\n') || '// No schemas defined';
  }, [apiSpec]);

  // Unique methods for filter
  const availableMethods = useMemo(() => {
    const methods = new Set(endpoints.map(e => e.method));
    return ['all', ...Array.from(methods).sort()];
  }, [endpoints]);

  if (!apiSpec) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 p-4">
        <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1} style={{ color: 'var(--t-muted)' }}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
        </svg>
        <p className="text-sm text-center" style={{ color: 'var(--t-muted)' }}>
          No API spec available. Ask the AI to generate a backend for your app.
        </p>
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
        <span className="text-xs font-medium" style={{ color: 'var(--t-text2)' }}>
          {apiSpec.info.title} <span style={{ color: 'var(--t-muted)' }}>v{apiSpec.info.version}</span>
        </span>

        {/* Mock server toggle */}
        <button
          onClick={mockServerStatus.running ? stopMockServer : startMockServer}
          className="text-xs px-2 py-0.5 rounded transition-colors"
          style={{
            background: mockServerStatus.running ? 'var(--t-success)' : 'var(--t-surface2)',
            color: mockServerStatus.running ? '#fff' : 'var(--t-muted)',
          }}
        >
          {mockServerStatus.running ? `Mock :${mockServerStatus.port}` : 'Start Mock'}
        </button>
      </div>

      {/* Tab bar */}
      <div
        className="flex items-center gap-0.5 px-2 h-8 flex-shrink-0"
        style={{ borderBottom: '1px solid var(--t-border)' }}
      >
        {(['endpoints', 'schemas', 'types'] as TabId[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className="px-2.5 py-1 rounded text-xs capitalize transition-colors"
            style={{
              background: activeTab === tab ? 'var(--t-primary)' : 'transparent',
              color: activeTab === tab ? '#fff' : 'var(--t-muted)',
            }}
          >
            {tab}
          </button>
        ))}

        {/* Method filter (endpoints tab only) */}
        {activeTab === 'endpoints' && (
          <select
            value={filterMethod}
            onChange={e => setFilterMethod(e.target.value)}
            className="ml-auto text-xs px-1.5 py-0.5 rounded outline-none"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-text2)', border: '1px solid var(--t-border)' }}
          >
            {availableMethods.map(m => (
              <option key={m} value={m}>{m === 'all' ? 'All Methods' : m}</option>
            ))}
          </select>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {activeTab === 'endpoints' && (
          <>
            {filteredEndpoints.length === 0 ? (
              <p className="text-xs text-center p-4" style={{ color: 'var(--t-muted)' }}>No endpoints found</p>
            ) : (
              filteredEndpoints.map((ep, i) => (
                <StudioEndpointCard key={`${ep.method}-${ep.path}-${i}`} endpoint={ep} />
              ))
            )}
          </>
        )}

        {activeTab === 'schemas' && (
          <>
            {apiSpec.components?.schemas ? (
              Object.entries(apiSpec.components.schemas).map(([name, schema]: [string, any]) => (
                <div
                  key={name}
                  className="rounded p-3"
                  style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}
                >
                  <h4 className="text-xs font-medium mb-2" style={{ color: 'var(--t-primary)' }}>{name}</h4>
                  {schema.properties && (
                    <div className="space-y-1">
                      {Object.entries(schema.properties).map(([prop, propSchema]: [string, any]) => (
                        <div key={prop} className="flex items-center gap-2 text-xs">
                          <span style={{ color: 'var(--t-text)', fontFamily: 'var(--t-font-mono)' }}>{prop}</span>
                          <span style={{ color: 'var(--t-muted)' }}>{propSchema.type || 'object'}</span>
                          {schema.required?.includes(prop) && (
                            <span className="px-1 rounded" style={{ background: 'var(--t-error)', color: '#fff', fontSize: 10 }}>req</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p className="text-xs text-center p-4" style={{ color: 'var(--t-muted)' }}>No schemas defined</p>
            )}
          </>
        )}

        {activeTab === 'types' && (
          <pre
            className="text-xs p-3 rounded overflow-x-auto whitespace-pre-wrap"
            style={{
              background: 'var(--t-surface)',
              color: 'var(--t-text)',
              fontFamily: 'var(--t-font-mono)',
              border: '1px solid var(--t-border)',
            }}
          >
            {generatedTypes}
          </pre>
        )}
      </div>
    </div>
  );
};

/** Convert JSON Schema type to TypeScript type string */
function jsonSchemaToTS(schema: any): string {
  if (!schema) return 'any';
  if (schema.$ref) {
    const refName = schema.$ref.split('/').pop();
    return refName || 'any';
  }
  switch (schema.type) {
    case 'string': return schema.enum ? schema.enum.map((e: string) => `'${e}'`).join(' | ') : 'string';
    case 'integer':
    case 'number': return 'number';
    case 'boolean': return 'boolean';
    case 'array': return `${jsonSchemaToTS(schema.items)}[]`;
    case 'object': {
      if (!schema.properties) return 'Record<string, any>';
      const props = Object.entries(schema.properties)
        .map(([k, v]) => `${k}: ${jsonSchemaToTS(v as any)}`)
        .join('; ');
      return `{ ${props} }`;
    }
    default: return 'any';
  }
}

export default StudioApiPanel;
