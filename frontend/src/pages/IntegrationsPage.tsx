import React, { useState, useEffect } from 'react';
import * as apiService from '../services/apiService';
import { Integration, IntegrationSetup } from '../types/memory';

const PLATFORM_INFO: Record<string, { label: string; icon: string; color: string }> = {
  telegram: { label: 'Telegram', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z', color: '#0088cc' },
  whatsapp: { label: 'WhatsApp', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z', color: '#25D366' },
  discord: { label: 'Discord', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z', color: '#5865F2' },
  slack: { label: 'Slack', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z', color: '#4A154B' },
  gmail: { label: 'Gmail', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z', color: '#EA4335' },
  spotify: { label: 'Spotify', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z', color: '#1DB954' },
  calendar: { label: 'Calendar', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z', color: '#4285F4' },
};

const IntegrationsPage: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [configuring, setConfiguring] = useState<string | null>(null);
  const [configFields, setConfigFields] = useState<Record<string, string>>({});
  const [testResult, setTestResult] = useState<{ ok?: boolean; error?: string } | null>(null);
  const [setupInfo, setSetupInfo] = useState<IntegrationSetup | null>(null);

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    try {
      const data = await apiService.listIntegrations();
      setIntegrations(Array.isArray(data) ? data : []);
    } catch { }
    setLoading(false);
  };

  const handleConfigure = async (platform: string) => {
    setConfiguring(platform);
    setTestResult(null);
    setConfigFields({});
    try {
      const setup = await apiService.getIntegrationSetup(platform);
      setSetupInfo(setup);
    } catch { }
  };

  const handleSave = async () => {
    if (!configuring) return;
    try {
      await apiService.configureIntegration(configuring, configFields);
      setConfiguring(null);
      loadIntegrations();
    } catch { }
  };

  const handleTest = async (platform: string) => {
    setTestResult(null);
    try {
      const result = await apiService.testIntegration(platform);
      setTestResult(result);
    } catch (e: any) {
      setTestResult({ ok: false, error: e.message });
    }
  };

  const handleToggle = async (platform: string, currentlyEnabled: boolean) => {
    try {
      if (currentlyEnabled) {
        await apiService.disableIntegration(platform);
      } else {
        await apiService.enableIntegration(platform);
      }
      loadIntegrations();
    } catch { }
  };

  const handleDelete = async (platform: string) => {
    try {
      await apiService.deleteIntegration(platform);
      loadIntegrations();
    } catch { }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full" style={{ color: 'var(--t-muted)' }}>
        Loading integrations...
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4" style={{ background: 'var(--t-bg)' }}>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-xl font-bold mb-1" style={{ color: 'var(--t-text)' }}>Integrations</h1>
        <p className="text-sm mb-6" style={{ color: 'var(--t-muted)' }}>
          Connect external platforms to your AI workspace. Messages from connected platforms flow through the unified agentic loop with memory and skill injection.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {integrations.map(intg => {
            const info = PLATFORM_INFO[intg.platform] || { label: intg.platform, icon: '', color: '#666' };
            const isConfigured = intg.id !== null;

            return (
              <div
                key={intg.platform}
                className="rounded-lg p-4 border"
                style={{ background: 'var(--t-surface)', borderColor: 'var(--t-border)' }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
                      style={{ background: info.color }}
                    >
                      {info.label[0]}
                    </div>
                    <div>
                      <span className="font-medium text-sm" style={{ color: 'var(--t-text)' }}>{info.label}</span>
                      {intg.user_label && (
                        <span className="text-xs ml-2" style={{ color: 'var(--t-muted)' }}>({intg.user_label})</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ background: isConfigured && intg.enabled ? '#22c55e' : '#6b7280' }}
                    />
                    <span className="text-xs" style={{ color: 'var(--t-muted)' }}>
                      {isConfigured ? (intg.enabled ? 'Active' : 'Disabled') : 'Not configured'}
                    </span>
                  </div>
                </div>

                {isConfigured && (
                  <div className="text-xs mb-3" style={{ color: 'var(--t-muted)' }}>
                    {intg.message_count} messages | Keys: {intg.config_keys.join(', ') || 'none'}
                  </div>
                )}

                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => handleConfigure(intg.platform)}
                    className="px-3 py-1.5 rounded text-xs font-medium"
                    style={{ background: 'var(--t-primary)', color: '#fff' }}
                  >
                    {isConfigured ? 'Edit' : 'Configure'}
                  </button>

                  {isConfigured && (
                    <>
                      <button
                        onClick={() => handleTest(intg.platform)}
                        className="px-3 py-1.5 rounded text-xs border"
                        style={{ borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
                      >
                        Test
                      </button>
                      <button
                        onClick={() => handleToggle(intg.platform, intg.enabled)}
                        className="px-3 py-1.5 rounded text-xs border"
                        style={{ borderColor: 'var(--t-border)', color: intg.enabled ? 'var(--t-error)' : '#22c55e' }}
                      >
                        {intg.enabled ? 'Disable' : 'Enable'}
                      </button>
                      <button
                        onClick={() => handleDelete(intg.platform)}
                        className="px-3 py-1.5 rounded text-xs"
                        style={{ color: 'var(--t-error)' }}
                      >
                        Remove
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Configuration Modal */}
      {configuring && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: 'rgba(0,0,0,0.5)' }}
          onClick={() => setConfiguring(null)}
        >
          <div
            className="rounded-lg p-6 max-w-md w-full mx-4"
            style={{ background: 'var(--t-surface)', color: 'var(--t-text)' }}
            onClick={e => e.stopPropagation()}
          >
            <h2 className="text-lg font-bold mb-4">
              Configure {PLATFORM_INFO[configuring]?.label || configuring}
            </h2>

            {setupInfo && (
              <div className="mb-4 p-3 rounded text-xs" style={{ background: 'var(--t-surface2)' }}>
                <p className="font-medium mb-2" style={{ color: 'var(--t-muted)' }}>Setup steps:</p>
                {setupInfo.steps.map((step, i) => (
                  <p key={i} className="mb-1" style={{ color: 'var(--t-muted)' }}>{step}</p>
                ))}
              </div>
            )}

            <div className="space-y-3">
              {(setupInfo?.required_fields || []).map(field => (
                <div key={field}>
                  <label className="block text-xs font-medium mb-1" style={{ color: 'var(--t-muted)' }}>
                    {field}
                  </label>
                  <input
                    type={field.includes('secret') || field.includes('token') ? 'password' : 'text'}
                    value={configFields[field] || ''}
                    onChange={e => setConfigFields(prev => ({ ...prev, [field]: e.target.value }))}
                    className="w-full p-2 rounded text-sm"
                    style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
                    placeholder={field}
                  />
                </div>
              ))}
            </div>

            {testResult && (
              <div
                className="mt-3 p-2 rounded text-xs"
                style={{ background: testResult.ok ? '#22c55e20' : '#ef444420', color: testResult.ok ? '#22c55e' : '#ef4444' }}
              >
                {testResult.ok ? 'Connection successful!' : `Error: ${testResult.error}`}
              </div>
            )}

            <div className="flex gap-2 mt-4">
              <button
                onClick={handleSave}
                className="px-4 py-2 rounded text-sm font-medium"
                style={{ background: 'var(--t-primary)', color: '#fff' }}
              >
                Save
              </button>
              <button
                onClick={() => handleTest(configuring)}
                className="px-4 py-2 rounded text-sm border"
                style={{ borderColor: 'var(--t-border)', color: 'var(--t-text)' }}
              >
                Test
              </button>
              <button
                onClick={() => setConfiguring(null)}
                className="px-4 py-2 rounded text-sm"
                style={{ color: 'var(--t-muted)' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationsPage;
