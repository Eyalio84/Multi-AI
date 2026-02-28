/**
 * VoxOverlay — 3-state floating voice control.
 *
 * States:
 * 1. Dormant — Small "V" pill, bottom-right, tap to expand
 * 2. Listening — Pulsing ring animation, active mic, mini-transcript
 * 3. Speaking — Wave animation, VOX response playing
 *
 * Always-visible mini-transcript (last 3 exchanges) when expanded.
 * Text input field for typed queries.
 * Haptic feedback on state transitions.
 */
import React, { useState, useRef, useEffect } from 'react';
import { useVoxContext } from '../context/VoxContext';
import type { VoxVoice } from '../types/vox';

const VOICES: VoxVoice[] = [
  { id: 'Puck', name: 'Puck', gender: 'Male', style: 'Upbeat' },
  { id: 'Charon', name: 'Charon', gender: 'Male', style: 'Steady' },
  { id: 'Kore', name: 'Kore', gender: 'Female', style: 'Firm' },
  { id: 'Fenrir', name: 'Fenrir', gender: 'Male', style: 'Bold' },
  { id: 'Aoede', name: 'Aoede', gender: 'Female', style: 'Warm' },
  { id: 'Leda', name: 'Leda', gender: 'Female', style: 'Youthful' },
  { id: 'Orus', name: 'Orus', gender: 'Male', style: 'Decisive' },
  { id: 'Zephyr', name: 'Zephyr', gender: 'Male', style: 'Calm' },
  { id: 'Sage', name: 'Sage', gender: 'Non-binary', style: 'Wise' },
  { id: 'Vale', name: 'Vale', gender: 'Non-binary', style: 'Gentle' },
  { id: 'Solaria', name: 'Solaria', gender: 'Female', style: 'Bright' },
  { id: 'River', name: 'River', gender: 'Non-binary', style: 'Smooth' },
  { id: 'Ember', name: 'Ember', gender: 'Female', style: 'Passionate' },
  { id: 'Breeze', name: 'Breeze', gender: 'Female', style: 'Airy' },
  { id: 'Cove', name: 'Cove', gender: 'Male', style: 'Deep' },
  { id: 'Orbit', name: 'Orbit', gender: 'Male', style: 'Futuristic' },
];

function haptic(ms = 50) {
  try { navigator.vibrate?.(ms); } catch (_) {}
}

const VoxOverlay: React.FC = () => {
  const { state, connect, disconnect, toggleMic, sendText, setVoice, isAvailable } = useVoxContext();
  const [expanded, setExpanded] = useState(false);
  const [textInput, setTextInput] = useState('');
  const transcriptRef = useRef<HTMLDivElement>(null);
  const prevStateRef = useRef({ listening: false, speaking: false, connected: false });

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [state.transcript]);

  // Haptic feedback on state transitions
  useEffect(() => {
    const prev = prevStateRef.current;
    if (!prev.connected && state.connected) haptic(100);
    else if (!prev.listening && state.listening) haptic(50);
    else if (!prev.speaking && state.speaking) haptic(30);
    prevStateRef.current = {
      listening: state.listening,
      speaking: state.speaking,
      connected: state.connected,
    };
  }, [state.connected, state.listening, state.speaking]);

  if (!isAvailable) return null;

  const handleConnect = (mode: 'gemini' | 'claude') => {
    connect(mode, { voice: state.voice });
  };

  const handleSendText = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      sendText(textInput.trim());
      setTextInput('');
    }
  };

  // Determine visual state
  const voxState = state.speaking ? 'speaking' : state.listening ? 'listening' : 'dormant';

  // Styles for V button based on state
  const buttonStyles: Record<string, React.CSSProperties> = {
    dormant: {
      background: state.connected ? 'var(--t-primary)' : 'var(--t-surface)',
      color: state.connected ? '#fff' : 'var(--t-text)',
      border: `2px solid ${state.connected ? 'transparent' : 'var(--t-border)'}`,
    },
    listening: {
      background: 'var(--t-primary)',
      color: '#fff',
      border: '2px solid var(--t-primary)',
      boxShadow: '0 0 0 4px rgba(14, 165, 233, 0.3)',
    },
    speaking: {
      background: '#22c55e',
      color: '#fff',
      border: '2px solid #22c55e',
      boxShadow: '0 0 0 4px rgba(34, 197, 94, 0.3)',
    },
  };

  // ── Collapsed: "V" button ──────────────────────────────────────────
  if (!expanded) {
    return (
      <button
        onClick={() => { setExpanded(true); haptic(50); }}
        className="fixed bottom-4 right-4 z-50 flex items-center justify-center rounded-full shadow-lg transition-all hover:scale-110"
        style={{
          width: 48,
          height: 48,
          ...buttonStyles[voxState],
          animation: voxState === 'listening' ? 'vox-pulse 2s ease-in-out infinite' :
                     voxState === 'speaking' ? 'vox-wave 1s ease-in-out infinite' : undefined,
        }}
      >
        <span className="font-black text-lg">V</span>
        <style>{`
          @keyframes vox-pulse {
            0%, 100% { box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.3); }
            50% { box-shadow: 0 0 0 10px rgba(14, 165, 233, 0.1); }
          }
          @keyframes vox-wave {
            0%, 100% { box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.3); }
            50% { box-shadow: 0 0 0 10px rgba(34, 197, 94, 0.1); }
          }
        `}</style>
      </button>
    );
  }

  // ── Expanded panel ─────────────────────────────────────────────────
  return (
    <div
      className="fixed bottom-4 right-4 z-50 rounded-xl shadow-2xl overflow-hidden"
      style={{
        background: 'var(--t-surface)',
        border: '1px solid var(--t-border)',
        width: 320,
        maxHeight: '80vh',
      }}
    >
      {/* Header with state indicator */}
      <div className="flex items-center justify-between px-3 py-2 border-b" style={{ borderColor: 'var(--t-border)' }}>
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-black"
            style={{
              ...buttonStyles[voxState],
              animation: voxState === 'listening' ? 'vox-pulse 2s ease-in-out infinite' :
                         voxState === 'speaking' ? 'vox-wave 1s ease-in-out infinite' : undefined,
            }}
          >
            V
          </div>
          <span className="font-bold text-sm" style={{ color: 'var(--t-text)' }}>VOX</span>
          {state.connected && (
            <span className="text-xs px-1.5 py-0.5 rounded" style={{ background: 'var(--t-surface2)', color: 'var(--t-muted)' }}>
              {state.mode === 'gemini' ? 'Gemini' : 'Claude'}
            </span>
          )}
          {state.reconnecting && (
            <span className="text-xs text-yellow-400 animate-pulse">Reconnecting...</span>
          )}
        </div>
        <button onClick={() => setExpanded(false)} className="text-lg leading-none px-1" style={{ color: 'var(--t-muted)' }}>
          &times;
        </button>
      </div>

      {/* Not connected: mode selection */}
      {!state.connected && (
        <div className="p-3 space-y-3">
          <div className="flex gap-2">
            <button
              onClick={() => handleConnect('gemini')}
              className="flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all hover:scale-[1.02]"
              style={{ background: 'var(--t-primary)', color: '#fff' }}
            >
              Gemini Voice
            </button>
            <button
              onClick={() => handleConnect('claude')}
              className="flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all hover:scale-[1.02]"
              style={{ background: '#9a3412', color: '#fff' }}
            >
              Claude Voice
            </button>
          </div>

          <div>
            <label className="text-xs block mb-1" style={{ color: 'var(--t-muted)' }}>Voice</label>
            <select
              value={state.voice}
              onChange={e => setVoice(e.target.value)}
              className="w-full text-xs rounded px-2 py-1.5"
              style={{ background: 'var(--t-bg)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
            >
              {VOICES.map(v => (
                <option key={v.id} value={v.id}>{v.name} — {v.style}</option>
              ))}
            </select>
          </div>

          <p className="text-xs" style={{ color: 'var(--t-muted)' }}>
            Gemini: native audio streaming. Claude: browser STT/TTS.
          </p>
        </div>
      )}

      {/* Connected: transcript + controls */}
      {state.connected && (
        <>
          {/* Mini-transcript */}
          <div
            ref={transcriptRef}
            className="overflow-y-auto px-3 py-2 space-y-1.5"
            style={{ maxHeight: 240, minHeight: 100 }}
          >
            {state.transcript.length === 0 && (
              <p className="text-xs italic" style={{ color: 'var(--t-muted)' }}>
                {state.mode === 'gemini' ? 'Speak to VOX...' : 'Speak or type to VOX...'}
              </p>
            )}
            {state.transcript.map((t, i) => (
              <div key={i} className="text-xs">
                <span
                  className="font-semibold"
                  style={{
                    color: t.role === 'user' ? 'var(--t-primary)' :
                           t.role === 'model' ? '#22c55e' : 'var(--t-muted)',
                  }}
                >
                  {t.role === 'user' ? 'You' : t.role === 'model' ? 'VOX' : 'SYS'}:
                </span>{' '}
                <span style={{ color: 'var(--t-text)' }}>{t.text}</span>
              </div>
            ))}
          </div>

          {/* Text input */}
          <form onSubmit={handleSendText} className="px-3 pb-2">
            <div className="flex gap-1">
              <input
                type="text"
                value={textInput}
                onChange={e => setTextInput(e.target.value)}
                placeholder="Type to VOX..."
                className="flex-1 text-xs rounded px-2 py-1.5"
                style={{ background: 'var(--t-bg)', color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
              />
              <button type="submit" className="px-2 py-1.5 rounded text-xs" style={{ background: 'var(--t-primary)', color: '#fff' }}>
                Send
              </button>
            </div>
          </form>

          {/* State bar + controls */}
          <div className="px-3 pb-3 flex items-center justify-between border-t pt-2" style={{ borderColor: 'var(--t-border)' }}>
            <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--t-muted)' }}>
              <span>T:{state.turnCount}</span>
              <span>F:{state.functionCount}</span>
              {state.speaking && <span className="text-green-400 animate-pulse">Speaking</span>}
              {state.listening && !state.speaking && <span className="text-blue-400 animate-pulse">Listening</span>}
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => { toggleMic(); haptic(50); }}
                className="p-1.5 rounded transition-all"
                style={{
                  background: state.listening ? 'var(--t-primary)' : 'var(--t-surface2)',
                  color: state.listening ? '#fff' : 'var(--t-muted)',
                }}
                title={state.listening ? 'Mute' : 'Unmute'}
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  {state.listening ? (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                  )}
                </svg>
              </button>
              <button
                onClick={() => { disconnect(); haptic(100); }}
                className="p-1.5 rounded transition-all hover:scale-110"
                style={{ background: '#ef4444', color: '#fff' }}
                title="Disconnect"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </>
      )}

      {/* Error display */}
      {state.error && (
        <div className="px-3 pb-2">
          <p className="text-xs text-red-400">{state.error}</p>
        </div>
      )}
    </div>
  );
};

export default VoxOverlay;
