/**
 * VoxPage — Full dedicated page for VOX Control Center.
 * Controls + conversation transcript + function execution log + macros section.
 */
import React, { useState, useRef, useEffect } from 'react';
import { useVoxContext } from '../context/VoxContext';
import type { VoxVoice } from '../types/vox';

const VOICES: VoxVoice[] = [
  { id: 'Puck', name: 'Puck', gender: 'Male', style: 'Upbeat, lively' },
  { id: 'Charon', name: 'Charon', gender: 'Male', style: 'Informative, steady' },
  { id: 'Kore', name: 'Kore', gender: 'Female', style: 'Firm, authoritative' },
  { id: 'Fenrir', name: 'Fenrir', gender: 'Male', style: 'Excitable, bold' },
  { id: 'Aoede', name: 'Aoede', gender: 'Female', style: 'Breezy, warm' },
  { id: 'Leda', name: 'Leda', gender: 'Female', style: 'Youthful, approachable' },
  { id: 'Orus', name: 'Orus', gender: 'Male', style: 'Firm, decisive' },
  { id: 'Zephyr', name: 'Zephyr', gender: 'Male', style: 'Calm, breezy' },
  { id: 'Sage', name: 'Sage', gender: 'Non-binary', style: 'Wise, thoughtful' },
  { id: 'Vale', name: 'Vale', gender: 'Non-binary', style: 'Gentle, melodic' },
  { id: 'Solaria', name: 'Solaria', gender: 'Female', style: 'Bright, energetic' },
  { id: 'River', name: 'River', gender: 'Non-binary', style: 'Smooth, flowing' },
  { id: 'Ember', name: 'Ember', gender: 'Female', style: 'Warm, passionate' },
  { id: 'Breeze', name: 'Breeze', gender: 'Female', style: 'Light, airy' },
  { id: 'Cove', name: 'Cove', gender: 'Male', style: 'Deep, resonant' },
  { id: 'Orbit', name: 'Orbit', gender: 'Male', style: 'Futuristic, crisp' },
];

const GEMINI_MODELS = [
  'gemini-2.0-flash-live-001',
  'gemini-2.5-flash-preview-native-audio-dialog',
  'gemini-2.5-flash',
  'gemini-2.5-pro',
];

interface MacroSummary {
  id: string;
  name: string;
  trigger_phrase: string;
  step_count: number;
}

const VoxPage: React.FC = () => {
  const { state, connect, disconnect, toggleMic, sendText, setVoice, isAvailable } = useVoxContext();
  const [selectedMode, setSelectedMode] = useState<'gemini' | 'claude'>('gemini');
  const [selectedModel, setSelectedModel] = useState(GEMINI_MODELS[0]);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [textInput, setTextInput] = useState('');
  const [macros, setMacros] = useState<MacroSummary[]>([]);
  const [showMacros, setShowMacros] = useState(false);
  const transcriptRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [state.transcript]);

  // Load macros
  useEffect(() => {
    fetch('/api/vox/macros')
      .then(r => r.json())
      .then(data => setMacros(data.macros || []))
      .catch(() => {});
  }, []);

  const handleConnect = () => {
    connect(selectedMode, {
      voice: state.voice,
      model: selectedModel,
      systemPrompt,
    });
  };

  const handleSendText = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      sendText(textInput.trim());
      setTextInput('');
    }
  };

  const handleRunMacro = async (macroId: string) => {
    try {
      const res = await fetch(`/api/vox/macros/${macroId}/run`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        // Results will appear in function log via WS
      }
    } catch (_) {}
  };

  const handleDeleteMacro = async (macroId: string) => {
    try {
      await fetch(`/api/vox/macros/${macroId}`, { method: 'DELETE' });
      setMacros(prev => prev.filter(m => m.id !== macroId));
    } catch (_) {}
  };

  return (
    <div className="h-full flex flex-col overflow-hidden" style={{ background: 'var(--t-bg)' }}>
      {/* Header */}
      <div className="px-4 py-3 border-b flex items-center justify-between" style={{ borderColor: 'var(--t-border)' }}>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} style={{ color: 'var(--t-primary)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            <h1 className="text-lg font-bold" style={{ color: 'var(--t-text)' }}>VOX Control Center</h1>
          </div>
          {state.connected && (
            <span className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full" style={{ background: 'rgba(34,197,94,0.15)', color: '#22c55e' }}>
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              Connected — {state.mode === 'gemini' ? 'Gemini Live' : 'Claude'}
            </span>
          )}
          {state.reconnecting && (
            <span className="text-xs px-2 py-1 rounded-full" style={{ background: 'rgba(251,191,36,0.15)', color: '#fbbf24' }}>
              Reconnecting...
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!isAvailable && (
            <span className="text-xs px-2 py-1 rounded" style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}>
              No API keys configured
            </span>
          )}
          <button
            onClick={() => setShowMacros(!showMacros)}
            className="text-xs px-2 py-1 rounded"
            style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}
          >
            Macros ({macros.length})
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Controls */}
        <div className="w-72 border-r overflow-y-auto p-4 space-y-4 shrink-0" style={{ borderColor: 'var(--t-border)' }}>

          {/* Mode selector */}
          <div>
            <label className="text-xs font-semibold block mb-2" style={{ color: 'var(--t-muted)' }}>MODE</label>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedMode('gemini')}
                className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${selectedMode === 'gemini' ? 'ring-2' : ''}`}
                style={{
                  background: selectedMode === 'gemini' ? 'var(--t-primary)' : 'var(--t-surface2)',
                  color: selectedMode === 'gemini' ? '#fff' : 'var(--t-muted)',
                  ringColor: 'var(--t-primary)',
                }}
                disabled={state.connected}
              >
                Gemini
              </button>
              <button
                onClick={() => setSelectedMode('claude')}
                className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${selectedMode === 'claude' ? 'ring-2' : ''}`}
                style={{
                  background: selectedMode === 'claude' ? '#9a3412' : 'var(--t-surface2)',
                  color: selectedMode === 'claude' ? '#fff' : 'var(--t-muted)',
                  ringColor: '#9a3412',
                }}
                disabled={state.connected}
              >
                Claude
              </button>
            </div>
            <p className="text-xs mt-1" style={{ color: 'var(--t-muted)' }}>
              {selectedMode === 'gemini' ? 'Native audio via Gemini Live API' : 'Browser STT/TTS via Claude text API'}
            </p>
          </div>

          {/* Voice selector (Gemini only) */}
          {selectedMode === 'gemini' && (
            <div>
              <label className="text-xs font-semibold block mb-2" style={{ color: 'var(--t-muted)' }}>VOICE ({VOICES.length})</label>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {VOICES.map(v => (
                  <button
                    key={v.id}
                    onClick={() => setVoice(v.id)}
                    className="w-full text-left px-3 py-1.5 rounded text-xs flex justify-between items-center"
                    style={{
                      background: state.voice === v.id ? 'var(--t-primary)' : 'transparent',
                      color: state.voice === v.id ? '#fff' : 'var(--t-text)',
                    }}
                    disabled={state.connected}
                  >
                    <span className="font-medium">{v.name}</span>
                    <span style={{ color: state.voice === v.id ? 'rgba(255,255,255,0.7)' : 'var(--t-muted)' }}>
                      {v.style}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Model selector */}
          <div>
            <label className="text-xs font-semibold block mb-2" style={{ color: 'var(--t-muted)' }}>MODEL</label>
            <select
              value={selectedModel}
              onChange={e => setSelectedModel(e.target.value)}
              className="w-full text-xs rounded px-2 py-1.5"
              style={{ background: 'var(--t-bg)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
              disabled={state.connected}
            >
              {selectedMode === 'gemini'
                ? GEMINI_MODELS.map(m => <option key={m} value={m}>{m}</option>)
                : ['claude-sonnet-4-6', 'claude-haiku-4-5-20251001', 'claude-opus-4-6'].map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))
              }
            </select>
          </div>

          {/* System prompt */}
          <div>
            <label className="text-xs font-semibold block mb-2" style={{ color: 'var(--t-muted)' }}>SYSTEM PROMPT (optional)</label>
            <textarea
              value={systemPrompt}
              onChange={e => setSystemPrompt(e.target.value)}
              rows={3}
              placeholder="Additional instructions for VOX..."
              className="w-full text-xs rounded px-2 py-1.5 resize-none"
              style={{ background: 'var(--t-bg)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
              disabled={state.connected}
            />
          </div>

          {/* Connect / Disconnect */}
          {!state.connected ? (
            <button
              onClick={handleConnect}
              className="w-full py-2.5 rounded-lg text-sm font-bold transition-all hover:opacity-90"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
              disabled={!isAvailable}
            >
              Connect to VOX
            </button>
          ) : (
            <div className="space-y-2">
              <button
                onClick={toggleMic}
                className="w-full py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-2"
                style={{
                  background: state.listening ? 'var(--t-primary)' : 'var(--t-surface2)',
                  color: state.listening ? '#fff' : 'var(--t-text)',
                }}
              >
                {state.listening ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                    Mic Active — Click to Mute
                  </>
                ) : (
                  'Mic Muted — Click to Unmute'
                )}
              </button>
              <button
                onClick={disconnect}
                className="w-full py-2 rounded-lg text-xs font-semibold"
                style={{ background: '#ef4444', color: '#fff' }}
              >
                Disconnect
              </button>
            </div>
          )}

          {/* Stats */}
          {state.connected && (
            <div className="rounded-lg p-3 space-y-2" style={{ background: 'var(--t-surface2)' }}>
              <h3 className="text-xs font-semibold" style={{ color: 'var(--t-muted)' }}>SESSION STATS</h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span style={{ color: 'var(--t-muted)' }}>Turns:</span>{' '}
                  <span className="font-semibold" style={{ color: 'var(--t-text)' }}>{state.turnCount}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--t-muted)' }}>Functions:</span>{' '}
                  <span className="font-semibold" style={{ color: 'var(--t-text)' }}>{state.functionCount}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--t-muted)' }}>Speaking:</span>{' '}
                  <span style={{ color: state.speaking ? '#22c55e' : 'var(--t-muted)' }}>{state.speaking ? 'Yes' : 'No'}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--t-muted)' }}>Listening:</span>{' '}
                  <span style={{ color: state.listening ? '#3b82f6' : 'var(--t-muted)' }}>{state.listening ? 'Yes' : 'No'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {state.error && (
            <div className="rounded-lg p-3 text-xs" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
              {state.error}
            </div>
          )}
        </div>

        {/* Right: Transcript + Function Log */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Macro panel (collapsible) */}
          {showMacros && (
            <div className="border-b p-3 space-y-2" style={{ borderColor: 'var(--t-border)', background: 'var(--t-surface2)' }}>
              <h3 className="text-xs font-semibold" style={{ color: 'var(--t-muted)' }}>VOICE MACROS</h3>
              {macros.length === 0 ? (
                <p className="text-xs" style={{ color: 'var(--t-muted)' }}>No macros saved. Ask VOX to "create a macro" by voice.</p>
              ) : (
                <div className="space-y-1">
                  {macros.map(m => (
                    <div key={m.id} className="flex items-center justify-between px-2 py-1.5 rounded text-xs" style={{ background: 'var(--t-bg)' }}>
                      <div>
                        <span className="font-semibold" style={{ color: 'var(--t-text)' }}>{m.name}</span>
                        <span className="ml-2" style={{ color: 'var(--t-muted)' }}>"{m.trigger_phrase}" ({m.step_count} steps)</span>
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleRunMacro(m.id)}
                          className="px-2 py-0.5 rounded text-xs"
                          style={{ background: 'var(--t-primary)', color: '#fff' }}
                        >
                          Run
                        </button>
                        <button
                          onClick={() => handleDeleteMacro(m.id)}
                          className="px-2 py-0.5 rounded text-xs"
                          style={{ background: '#ef4444', color: '#fff' }}
                        >
                          Del
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Conversation transcript */}
          <div className="flex-1 overflow-y-auto" ref={transcriptRef}>
            <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--t-border)' }}>
              <h2 className="text-sm font-semibold" style={{ color: 'var(--t-text)' }}>Conversation</h2>
            </div>
            <div className="px-4 py-3 space-y-3">
              {state.transcript.length === 0 && (
                <div className="text-center py-12">
                  <svg className="h-12 w-12 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1} style={{ color: 'var(--t-muted)' }}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                  <p className="text-sm" style={{ color: 'var(--t-muted)' }}>
                    {state.connected
                      ? 'Start speaking to VOX...'
                      : 'Connect to VOX to start a voice conversation'}
                  </p>
                  <p className="text-xs mt-2" style={{ color: 'var(--t-muted)' }}>
                    VOX has 34 functions: navigate pages, run tools, query KGs, guided tours, voice macros, and more — all by voice.
                  </p>
                </div>
              )}
              {state.transcript.map((t, i) => (
                <div
                  key={i}
                  className={`flex ${t.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className="max-w-[80%] rounded-xl px-3 py-2 text-sm"
                    style={{
                      background: t.role === 'user'
                        ? 'var(--t-primary)'
                        : t.role === 'model'
                        ? 'var(--t-surface2)'
                        : 'transparent',
                      color: t.role === 'user' ? '#fff' : 'var(--t-text)',
                      border: t.role === 'system' ? '1px dashed var(--t-border)' : 'none',
                      fontStyle: t.role === 'system' ? 'italic' : 'normal',
                    }}
                  >
                    {t.role !== 'user' && (
                      <span className="text-xs font-semibold block mb-0.5" style={{
                        color: t.role === 'model' ? '#22c55e' : 'var(--t-muted)',
                      }}>
                        {t.role === 'model' ? 'VOX' : 'System'}
                      </span>
                    )}
                    {t.text}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Text input bar */}
          {state.connected && (
            <form onSubmit={handleSendText} className="px-4 py-3 border-t" style={{ borderColor: 'var(--t-border)' }}>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={textInput}
                  onChange={e => setTextInput(e.target.value)}
                  placeholder="Type a message to VOX..."
                  className="flex-1 rounded-lg px-3 py-2 text-sm"
                  style={{ background: 'var(--t-surface2)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
                />
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg text-sm font-semibold"
                  style={{ background: 'var(--t-primary)', color: '#fff' }}
                >
                  Send
                </button>
              </div>
            </form>
          )}

          {/* Function log */}
          {state.functionLog.length > 0 && (
            <div className="border-t overflow-y-auto" style={{ borderColor: 'var(--t-border)', maxHeight: 160 }}>
              <div className="px-4 py-2">
                <h3 className="text-xs font-semibold" style={{ color: 'var(--t-muted)' }}>Function Log</h3>
              </div>
              <div className="px-4 pb-3 space-y-1">
                {state.functionLog.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs" style={{ color: 'var(--t-text)' }}>
                    <span style={{
                      color: f.status === 'success' ? '#22c55e' : f.status === 'error' ? '#ef4444' : '#f59e0b',
                    }}>
                      {f.status === 'success' ? 'OK' : f.status === 'error' ? 'ERR' : '...'}
                    </span>
                    <span className="font-mono">{f.name}</span>
                    <span style={{ color: 'var(--t-muted)' }}>
                      ({JSON.stringify(f.args).slice(0, 60)})
                    </span>
                    {f.serverHandled && (
                      <span className="text-xs px-1 rounded" style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}>
                        server
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoxPage;
