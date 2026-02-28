/**
 * voxCore — Module-level VOX singleton state manager.
 *
 * All VOX state lives at JS module scope, not React.
 * Survives React Router navigation and component unmounts.
 * React components subscribe via on()/off() and re-render via setState.
 *
 * Architecture: INSIGHT-004 (navigation callback injection),
 * INSIGHT-006 (plain JS state + event emitter → React bridge),
 * INSIGHT-001 (relative URLs, no hardcoded port).
 */
import type { VoxState, VoxConfig, VoxTranscriptEntry, VoxFunctionEntry, VoxMode } from '../types/vox';

// ── URL derivation (INSIGHT-001: use relative, no hardcoded port) ────
const API_BASE = '/api';
const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;

// ── Constants ─────────────────────────────────────────────────────────
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_BASE_DELAY = 500;
const MAX_TRANSCRIPT = 50;
const MAX_FUNCTION_LOG = 30;

// ── Module-level state (survives router navigation) ──────────────────
let _state: VoxState = {
  connected: false,
  mode: null,
  voice: localStorage.getItem('voxVoice') || 'Puck',
  speaking: false,
  listening: false,
  turnCount: 0,
  functionCount: 0,
  sessionId: null,
  transcript: [],
  functionLog: [],
  error: null,
  reconnecting: false,
  persona: 'default',
  conversationId: null,
};

// ── Internal refs (non-reactive) ─────────────────────────────────────
let _ws: WebSocket | null = null;
let _captureCtx: AudioContext | null = null;
let _micStream: MediaStream | null = null;
let _processor: ScriptProcessorNode | null = null;
let _playCtx: AudioContext | null = null;
let _nextPlayTime = 0;
let _recognition: any = null;
let _sessionToken: string | null = null;
let _reconnectAttempts = 0;
let _reconnectConfig: { mode: VoxMode; config?: Partial<VoxConfig> } | null = null;
let _resumeTimeout: ReturnType<typeof setTimeout> | null = null;

// Navigation callback (injected by React layer — INSIGHT-004)
let _navigateFn: ((path: string) => void) | null = null;
let _locationFn: (() => string) | null = null;

// Tour state
type Tour = { name: string; description: string; steps: any[] };
let _activeTour: Tour | null = null;

// ── Event emitter (INSIGHT-006: bridge to React re-renders) ──────────
type EventCallback = (data: any) => void;
const _listeners: Map<string, Set<EventCallback>> = new Map();

function emit(event: string, data: any) {
  const fns = _listeners.get(event);
  if (!fns) return;
  fns.forEach(fn => { try { fn(data); } catch (_) {} });
}

export function on(event: string, cb: EventCallback): () => void {
  if (!_listeners.has(event)) _listeners.set(event, new Set());
  _listeners.get(event)!.add(cb);
  return () => { _listeners.get(event)?.delete(cb); };
}

export function off(event: string, cb: EventCallback) {
  _listeners.get(event)?.delete(cb);
}

// ── State helpers ─────────────────────────────────────────────────────
function _setState(patch: Partial<VoxState>) {
  _state = { ..._state, ...patch };
  emit('state_change', _state);
}

export function getState(): VoxState {
  return { ..._state };
}

export function getActiveTour(): Tour | null {
  return _activeTour;
}

// ── Injectors (called by React layer) ────────────────────────────────
export function setNavigator(fn: (path: string) => void) {
  _navigateFn = fn;
}

export function setLocationGetter(fn: () => string) {
  _locationFn = fn;
}

// ── Transcript/log helpers ────────────────────────────────────────────
function addTranscript(role: 'user' | 'model' | 'system', text: string) {
  const entry: VoxTranscriptEntry = { role, text, timestamp: Date.now() };
  _setState({
    transcript: [..._state.transcript.slice(-(MAX_TRANSCRIPT - 1)), entry],
  });
  emit('transcript', entry);
}

function addFunctionLog(name: string, args: Record<string, any>, serverHandled: boolean): VoxFunctionEntry {
  const entry: VoxFunctionEntry = { name, args, serverHandled, timestamp: Date.now(), status: 'pending' };
  _setState({
    functionLog: [..._state.functionLog.slice(-(MAX_FUNCTION_LOG - 1)), entry],
    functionCount: _state.functionCount + 1,
  });
  return entry;
}

function updateFunctionLog(name: string, result: any, status: 'success' | 'error') {
  _setState({
    functionLog: _state.functionLog.map(f =>
      f.name === name && f.status === 'pending' ? { ...f, result, status } : f
    ),
  });
}

// ── Audio playback (Gemini mode — 24kHz output) ──────────────────────
function ensurePlayContext() {
  if (!_playCtx) {
    const Ctx = (window as any).AudioContext || (window as any).webkitAudioContext;
    _playCtx = new Ctx({ sampleRate: 24000 });
    _nextPlayTime = 0;
  }
}

function playAudioChunk(b64Data: string) {
  ensurePlayContext();
  const ctx = _playCtx!;

  const binary = atob(b64Data);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const int16 = new Int16Array(bytes.buffer);
  const float32 = new Float32Array(int16.length);
  for (let j = 0; j < int16.length; j++) float32[j] = int16[j] / 32768.0;

  const audioBuffer = ctx.createBuffer(1, float32.length, 24000);
  audioBuffer.getChannelData(0).set(float32);
  const sourceNode = ctx.createBufferSource();
  sourceNode.buffer = audioBuffer;
  sourceNode.connect(ctx.destination);

  const now = ctx.currentTime;
  if (_nextPlayTime < now) _nextPlayTime = now + 0.01;
  sourceNode.start(_nextPlayTime);
  _nextPlayTime += audioBuffer.duration;

  _setState({ speaking: true });
  sourceNode.onended = () => { _setState({ speaking: false }); };
}

// ── Mic capture (16kHz input) ─────────────────────────────────────────
function downsample(buffer: Float32Array, fromRate: number, toRate: number): Float32Array {
  if (fromRate === toRate) return buffer;
  const ratio = fromRate / toRate;
  const newLength = Math.floor(buffer.length / ratio);
  const result = new Float32Array(newLength);
  for (let i = 0; i < newLength; i++) result[i] = buffer[Math.floor(i * ratio)];
  return result;
}

function sendPCMChunk(samples: Float32Array) {
  if (!_ws || _ws.readyState !== WebSocket.OPEN) return;
  const int16 = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    int16[i] = s < 0 ? s * 32768 : s * 32767;
  }
  const bytes = new Uint8Array(int16.buffer);
  let bin = '';
  for (let j = 0; j < bytes.length; j++) bin += String.fromCharCode(bytes[j]);
  _ws.send(JSON.stringify({ type: 'audio', data: btoa(bin) }));
}

function startMic() {
  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    _micStream = stream;
    const Ctx = (window as any).AudioContext || (window as any).webkitAudioContext;
    let ctx: AudioContext;
    try { ctx = new Ctx({ sampleRate: 16000 }); } catch (_) { ctx = new Ctx(); }
    _captureCtx = ctx;

    const source = ctx.createMediaStreamSource(stream);
    const processor = ctx.createScriptProcessor(4096, 1, 1);
    _processor = processor;

    const nativeRate = ctx.sampleRate;
    const targetRate = 16000;

    processor.onaudioprocess = (e) => {
      if (!_state.connected || !_ws || _ws.readyState !== WebSocket.OPEN) return;
      const raw = e.inputBuffer.getChannelData(0);
      const samples = nativeRate !== targetRate ? downsample(raw, nativeRate, targetRate) : raw;
      sendPCMChunk(samples as Float32Array);
    };

    source.connect(processor);
    processor.connect(ctx.destination);
    _setState({ listening: true });
    addTranscript('system', `Mic active (${nativeRate}Hz)`);
  }).catch(err => {
    addTranscript('system', `Mic access denied: ${err.message}`);
  });
}

function stopMic() {
  if (_processor) { _processor.disconnect(); _processor = null; }
  if (_captureCtx) { _captureCtx.close().catch(() => {}); _captureCtx = null; }
  if (_micStream) { _micStream.getTracks().forEach(t => t.stop()); _micStream = null; }
  _setState({ listening: false });
}

// ── Browser STT for Claude mode ───────────────────────────────────────
function startSpeechRecognition() {
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SR) { addTranscript('system', 'Speech recognition not supported'); return; }

  const recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onresult = (event: any) => {
    const last = event.results[event.results.length - 1];
    if (last.isFinal) {
      const text = last[0].transcript.trim();
      if (text) {
        addTranscript('user', text);
        if (_ws && _ws.readyState === WebSocket.OPEN) {
          _ws.send(JSON.stringify({ type: 'text', text }));
        }
      }
    }
  };
  recognition.onerror = (event: any) => {
    if (event.error !== 'no-speech') addTranscript('system', `Recognition error: ${event.error}`);
  };
  recognition.onend = () => {
    if (_state.connected && _state.mode === 'claude') {
      try { recognition.start(); } catch (_) {}
    }
  };
  recognition.start();
  _recognition = recognition;
  _setState({ listening: true });
}

function stopSpeechRecognition() {
  if (_recognition) { _recognition.stop(); _recognition = null; }
}

// ── Browser TTS for Claude mode ───────────────────────────────────────
function speakText(text: string) {
  if (!('speechSynthesis' in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.1;
  utterance.pitch = 1.0;
  _setState({ speaking: true });
  utterance.onend = () => _setState({ speaking: false });
  window.speechSynthesis.speak(utterance);
}

// ── Browser function execution (INSIGHT-004, INSIGHT-005) ─────────────
const PAGE_PATHS: Record<string, string> = {
  chat: '/chat', coding: '/coding', agents: '/agents',
  playbooks: '/playbooks', workflows: '/workflows',
  'kg-studio': '/kg-studio', 'kg studio': '/kg-studio',
  experts: '/experts', builder: '/builder', studio: '/builder',
  tools: '/tools', vox: '/vox', integrations: '/integrations',
  settings: '/settings', games: '/games', news: '/news',
};

function executeBrowserFunction(name: string, args: any): any {
  const currentPath = _locationFn?.() || '/';

  switch (name) {
    case 'navigate_page': {
      const path = args.path || args.page || '';
      const resolved = PAGE_PATHS[path.toLowerCase().replace(/^\//, '')] || path;
      _navigateFn?.(resolved);
      return { success: true, navigated_to: resolved };
    }
    case 'get_current_page':
      return { path: currentPath };
    case 'get_workspace_state':
      return { page: currentPath };
    case 'switch_model':
      return { success: true, note: 'Model switch handled by context' };
    case 'switch_theme':
      return { success: true, note: 'Theme switch handled by context' };
    case 'read_page_content': {
      const main = document.querySelector('main') || document.querySelector('.flex-1');
      const content = main?.textContent?.replace(/\s+/g, ' ').trim().slice(0, 2000) || '';
      return { success: true, page: currentPath, content };
    }
    default:
      return { success: false, error: `Unknown browser function: ${name}` };
  }
}

// ── WebSocket message handler ─────────────────────────────────────────
function handleMessage(raw: string) {
  let msg: any;
  try { msg = JSON.parse(raw); } catch (_) { return; }
  const mt = msg.type || '';

  if (_resumeTimeout) { clearTimeout(_resumeTimeout); _resumeTimeout = null; }

  switch (mt) {
    case 'setup_complete':
      _setState({
        connected: true,
        sessionId: msg.sessionId,
        reconnecting: false,
        error: null,
      });
      _reconnectAttempts = 0;
      addTranscript('system', msg.resumed ? 'Session resumed! Mic active.' : 'Connected! Mic active.');
      if (_state.mode === 'gemini') startMic();
      else if (_state.mode === 'claude') startSpeechRecognition();
      emit('connected', { sessionId: msg.sessionId, resumed: msg.resumed });
      break;

    case 'audio':
      playAudioChunk(msg.data);
      break;

    case 'text':
      addTranscript('model', msg.text);
      if (_state.mode === 'claude') speakText(msg.text);
      break;

    case 'transcript':
      addTranscript(msg.role === 'user' ? 'user' : 'model', msg.text);
      break;

    case 'turn_complete':
      _setState({ turnCount: msg.turn || _state.turnCount + 1 });
      emit('turn_complete', { turn: msg.turn });
      break;

    case 'function_call': {
      const fnName = msg.name;
      const fnArgs = msg.args || {};
      addFunctionLog(fnName, fnArgs, msg.server_handled);
      addTranscript('system', `Function: ${fnName}(${JSON.stringify(fnArgs).slice(0, 100)})`);

      if (!msg.server_handled) {
        const result = executeBrowserFunction(fnName, fnArgs);
        updateFunctionLog(fnName, result, result.success ? 'success' : 'error');
        emit('function_result', { name: fnName, result });
        if (_ws && _ws.readyState === WebSocket.OPEN) {
          _ws.send(JSON.stringify({
            type: 'browser_function_result',
            name: fnName,
            result,
            fn_call_id: msg.fn_call_id || '',
          }));
        }
      }
      break;
    }

    case 'function_result':
      updateFunctionLog(msg.name, msg.result, msg.result?.success ? 'success' : 'error');
      addTranscript('system', `${msg.name} -> ${msg.result?.success ? 'OK' : 'Error'}`);
      break;

    case 'start_tour': {
      const tour = msg.tour as Tour;
      if (tour) {
        _activeTour = tour;
        emit('tour_start', tour);
        if (msg.page) {
          const path = PAGE_PATHS[msg.page] || `/${msg.page}`;
          _navigateFn?.(path);
        }
        addTranscript('system', `Starting guided tour: ${tour.name}`);
      }
      break;
    }

    case 'async_task_started':
      addTranscript('system', `Async task started: ${msg.function} [${msg.task_id}]`);
      emit('async_task_started', msg);
      break;

    case 'async_task_complete':
      addTranscript('system', `Async task complete: ${msg.function} [${msg.task_id}]`);
      emit('async_task_complete', msg);
      break;

    case 'go_away':
      _sessionToken = msg.session_token || null;
      addTranscript('system', 'Reconnecting...');
      _setState({ reconnecting: true });
      break;

    case 'error':
      _setState({ error: msg.message });
      addTranscript('system', `Error: ${msg.message}`);
      emit('error', { message: msg.message });
      break;
  }
}

// ── Auto-reconnect ────────────────────────────────────────────────────
function attemptReconnect() {
  if (_reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    addTranscript('system', 'Max reconnect attempts reached. Please reconnect manually.');
    _setState({ reconnecting: false, connected: false });
    return;
  }

  const attempt = _reconnectAttempts;
  const delay = RECONNECT_BASE_DELAY * Math.pow(2, attempt);
  _reconnectAttempts = attempt + 1;

  addTranscript('system', `Reconnecting in ${delay}ms (attempt ${attempt + 1}/${MAX_RECONNECT_ATTEMPTS})...`);

  setTimeout(() => {
    const cfg = _reconnectConfig;
    if (!cfg) return;

    const mode = cfg.mode;
    const config = cfg.config || {};
    const voice = config.voice || _state.voice;
    const model = config.model || '';
    const systemPrompt = config.systemPrompt || '';

    _setState({ mode, voice, error: null });

    try {
      const ws = new WebSocket(`${WS_BASE}/ws/vox`);
      _ws = ws;

      ws.onopen = () => {
        const initMsg: any = { type: 'start', mode, voice, model, systemPrompt };
        if (_sessionToken && mode === 'gemini') initMsg.session_token = _sessionToken;
        ws.send(JSON.stringify(initMsg));

        _resumeTimeout = setTimeout(() => {
          if (_ws?.readyState === WebSocket.OPEN) {
            addTranscript('system', 'Session token stale, starting fresh session...');
            _sessionToken = null;
            _ws.send(JSON.stringify({ type: 'start', mode, voice, model, systemPrompt }));
          }
        }, 5000);
      };

      ws.onmessage = (event) => handleMessage(event.data);
      ws.onerror = () => { _setState({ error: 'Reconnection error' }); };
      ws.onclose = () => {
        if (_state.reconnecting) attemptReconnect();
        else { _setState({ connected: false }); stopMic(); stopSpeechRecognition(); }
      };
    } catch (err: any) {
      _setState({ error: err.message });
    }
  }, delay);
}

// ── Public API ────────────────────────────────────────────────────────

export function connect(mode: VoxMode, config?: Partial<VoxConfig>) {
  const voice = config?.voice || _state.voice;
  const model = config?.model || '';
  const systemPrompt = config?.systemPrompt || '';

  _reconnectConfig = { mode, config };
  _reconnectAttempts = 0;

  _setState({
    mode, voice, error: null,
    transcript: [], functionLog: [],
    turnCount: 0, functionCount: 0,
  });

  try {
    const ws = new WebSocket(`${WS_BASE}/ws/vox`);
    _ws = ws;

    ws.onopen = () => {
      const initMsg: any = { type: 'start', mode, voice, model, systemPrompt };
      if (_sessionToken && mode === 'gemini') initMsg.session_token = _sessionToken;
      ws.send(JSON.stringify(initMsg));
    };

    ws.onmessage = (event) => handleMessage(event.data);
    ws.onerror = () => { _setState({ error: 'Connection error' }); };
    ws.onclose = () => {
      if (_state.reconnecting) attemptReconnect();
      else { _setState({ connected: false }); stopMic(); stopSpeechRecognition(); }
    };
  } catch (err: any) {
    _setState({ error: err.message });
  }
}

export function disconnect() {
  _reconnectConfig = null;
  _reconnectAttempts = 0;
  if (_resumeTimeout) { clearTimeout(_resumeTimeout); _resumeTimeout = null; }
  stopMic();
  stopSpeechRecognition();
  if (_ws) {
    try { _ws.send(JSON.stringify({ type: 'end' })); } catch (_) {}
    _ws.close();
    _ws = null;
  }
  if (_playCtx) { _playCtx.close().catch(() => {}); _playCtx = null; }
  _activeTour = null;
  _setState({
    connected: false, sessionId: null, listening: false,
    speaking: false, mode: null, reconnecting: false,
  });
  emit('disconnected', {});
  emit('tour_end', null);
}

export function toggleMic() {
  if (_state.listening) {
    stopMic();
    stopSpeechRecognition();
  } else {
    if (_state.mode === 'gemini') startMic();
    else if (_state.mode === 'claude') startSpeechRecognition();
  }
}

export function sendText(text: string) {
  if (!_ws || _ws.readyState !== WebSocket.OPEN) return;
  addTranscript('user', text);
  _ws.send(JSON.stringify({ type: 'text', text }));
}

export function setVoice(v: string) {
  _setState({ voice: v });
  localStorage.setItem('voxVoice', v);
}

export function clearTour() {
  _activeTour = null;
  emit('tour_end', null);
}

export function reportPageVisit(path: string) {
  fetch(`${API_BASE}/vox/awareness`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      event_type: 'page_visit',
      page: path,
      metadata: { timestamp: Date.now() },
    }),
  }).catch(() => {});
}
