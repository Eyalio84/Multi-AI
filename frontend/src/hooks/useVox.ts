/**
 * useVox — React hook for VOX voice integration.
 *
 * Ported from AI-LAB's useVox.js (Vue 3 composable).
 * Handles WebSocket audio streaming to Gemini Live API,
 * browser STT/TTS for Claude mode, and workspace function execution.
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import type { VoxState, VoxConfig, VoxTranscriptEntry, VoxFunctionEntry, VoxMode } from '../types/vox';

const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000`;

const initialState: VoxState = {
  connected: false,
  mode: null,
  voice: 'Puck',
  speaking: false,
  listening: false,
  turnCount: 0,
  functionCount: 0,
  sessionId: null,
  transcript: [],
  functionLog: [],
  error: null,
  reconnecting: false,
};

export type VoxEventCallback = (data: any) => void;

export function useVox() {
  const [state, setState] = useState<VoxState>(() => ({
    ...initialState,
    voice: localStorage.getItem('voxVoice') || 'Puck',
  }));

  const navigate = useNavigate();
  const location = useLocation();

  // Refs for non-reactive internals
  const wsRef = useRef<WebSocket | null>(null);
  const captureCtxRef = useRef<AudioContext | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const playCtxRef = useRef<AudioContext | null>(null);
  const nextPlayTimeRef = useRef<number>(0);
  const recognitionRef = useRef<any>(null);
  const listenersRef = useRef<Record<string, VoxEventCallback[]>>({});
  const stateRef = useRef(state);
  const sessionTokenRef = useRef<string | null>(null);

  // Keep stateRef synced
  useEffect(() => { stateRef.current = state; }, [state]);

  // ── Event system ──────────────────────────────────────────────────
  const emit = useCallback((event: string, data: any) => {
    const fns = listenersRef.current[event];
    if (!fns) return;
    fns.forEach(fn => { try { fn(data); } catch (_) {} });
  }, []);

  const on = useCallback((event: string, fn: VoxEventCallback) => {
    if (!listenersRef.current[event]) listenersRef.current[event] = [];
    listenersRef.current[event].push(fn);
  }, []);

  const off = useCallback((event: string, fn: VoxEventCallback) => {
    if (!listenersRef.current[event]) return;
    listenersRef.current[event] = listenersRef.current[event].filter(f => f !== fn);
  }, []);

  // ── Transcript helper ─────────────────────────────────────────────
  const addTranscript = useCallback((role: 'user' | 'model' | 'system', text: string) => {
    const entry: VoxTranscriptEntry = { role, text, timestamp: Date.now() };
    setState(prev => ({
      ...prev,
      transcript: [...prev.transcript.slice(-49), entry],
    }));
    emit('transcript', entry);
  }, [emit]);

  const addFunctionLog = useCallback((name: string, args: Record<string, any>, serverHandled: boolean) => {
    const entry: VoxFunctionEntry = { name, args, serverHandled, timestamp: Date.now(), status: 'pending' };
    setState(prev => ({
      ...prev,
      functionLog: [...prev.functionLog.slice(-29), entry],
      functionCount: prev.functionCount + 1,
    }));
    return entry;
  }, []);

  const updateFunctionLog = useCallback((name: string, result: any, status: 'success' | 'error') => {
    setState(prev => ({
      ...prev,
      functionLog: prev.functionLog.map(f =>
        f.name === name && f.status === 'pending' ? { ...f, result, status } : f
      ),
    }));
  }, []);

  // ── Audio playback (Gemini mode) ──────────────────────────────────
  const ensurePlayContext = useCallback(() => {
    if (!playCtxRef.current) {
      const CtxClass = (window as any).AudioContext || (window as any).webkitAudioContext;
      playCtxRef.current = new CtxClass({ sampleRate: 24000 });
      nextPlayTimeRef.current = 0;
    }
  }, []);

  const playAudioChunk = useCallback((b64Data: string) => {
    ensurePlayContext();
    const ctx = playCtxRef.current!;

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
    if (nextPlayTimeRef.current < now) nextPlayTimeRef.current = now + 0.01;
    sourceNode.start(nextPlayTimeRef.current);
    nextPlayTimeRef.current += audioBuffer.duration;

    setState(prev => ({ ...prev, speaking: true }));
    sourceNode.onended = () => {
      setState(prev => ({ ...prev, speaking: false }));
    };
  }, [ensurePlayContext]);

  // ── Mic capture ───────────────────────────────────────────────────
  const downsample = (buffer: Float32Array, fromRate: number, toRate: number): Float32Array => {
    if (fromRate === toRate) return buffer;
    const ratio = fromRate / toRate;
    const newLength = Math.floor(buffer.length / ratio);
    const result = new Float32Array(newLength);
    for (let i = 0; i < newLength; i++) result[i] = buffer[Math.floor(i * ratio)];
    return result;
  };

  const sendPCMChunk = useCallback((samples: Float32Array) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const int16 = new Int16Array(samples.length);
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      int16[i] = s < 0 ? s * 32768 : s * 32767;
    }
    const bytes = new Uint8Array(int16.buffer);
    let binary = '';
    for (let j = 0; j < bytes.length; j++) binary += String.fromCharCode(bytes[j]);
    ws.send(JSON.stringify({ type: 'audio', data: btoa(binary) }));
  }, []);

  const startMic = useCallback(() => {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      micStreamRef.current = stream;
      const CtxClass = (window as any).AudioContext || (window as any).webkitAudioContext;
      let ctx: AudioContext;
      try {
        ctx = new CtxClass({ sampleRate: 16000 });
      } catch (_) {
        ctx = new CtxClass();
      }
      captureCtxRef.current = ctx;

      const source = ctx.createMediaStreamSource(stream);
      const processor = ctx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      const nativeRate = ctx.sampleRate;
      const targetRate = 16000;

      processor.onaudioprocess = (e) => {
        if (!stateRef.current.connected || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        let samples = e.inputBuffer.getChannelData(0);
        if (nativeRate !== targetRate) samples = downsample(samples, nativeRate, targetRate);
        sendPCMChunk(samples);
      };

      source.connect(processor);
      processor.connect(ctx.destination);
      setState(prev => ({ ...prev, listening: true }));
      addTranscript('system', `Mic active (${nativeRate}Hz)`);
    }).catch(err => {
      addTranscript('system', `Mic access denied: ${err.message}`);
    });
  }, [sendPCMChunk, addTranscript]);

  const stopMic = useCallback(() => {
    if (processorRef.current) { processorRef.current.disconnect(); processorRef.current = null; }
    if (captureCtxRef.current) { captureCtxRef.current.close().catch(() => {}); captureCtxRef.current = null; }
    if (micStreamRef.current) { micStreamRef.current.getTracks().forEach(t => t.stop()); micStreamRef.current = null; }
    setState(prev => ({ ...prev, listening: false }));
  }, []);

  // ── Browser STT for Claude mode ───────────────────────────────────
  const startSpeechRecognition = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      addTranscript('system', 'Speech recognition not supported in this browser');
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      const last = event.results[event.results.length - 1];
      if (last.isFinal) {
        const text = last[0].transcript.trim();
        if (text) {
          addTranscript('user', text);
          // Send to backend via WS
          const ws = wsRef.current;
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'text', text }));
          }
        }
      }
    };
    recognition.onerror = (event: any) => {
      if (event.error !== 'no-speech') {
        addTranscript('system', `Recognition error: ${event.error}`);
      }
    };
    recognition.onend = () => {
      // Auto-restart if still connected
      if (stateRef.current.connected && stateRef.current.mode === 'claude') {
        try { recognition.start(); } catch (_) {}
      }
    };
    recognition.start();
    recognitionRef.current = recognition;
    setState(prev => ({ ...prev, listening: true }));
  }, [addTranscript]);

  const stopSpeechRecognition = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
  }, []);

  // ── Browser TTS for Claude mode ───────────────────────────────────
  const speakText = useCallback((text: string) => {
    if (!('speechSynthesis' in window)) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.1;
    utterance.pitch = 1.0;
    setState(prev => ({ ...prev, speaking: true }));
    utterance.onend = () => setState(prev => ({ ...prev, speaking: false }));
    window.speechSynthesis.speak(utterance);
  }, []);

  // ── Browser function execution ────────────────────────────────────
  const executeBrowserFunction = useCallback((name: string, args: any): any => {
    switch (name) {
      case 'navigate_page': {
        const path = args.path || args.page || '';
        const pagePaths: Record<string, string> = {
          chat: '/chat', coding: '/coding', agents: '/agents',
          playbooks: '/playbooks', workflows: '/workflows',
          'kg-studio': '/kg-studio', 'kg studio': '/kg-studio',
          experts: '/experts', builder: '/builder', studio: '/builder',
          tools: '/tools', vox: '/vox', integrations: '/integrations',
          settings: '/settings',
        };
        const resolved = pagePaths[path.toLowerCase().replace(/^\//, '')] || path;
        navigate(resolved);
        return { success: true, navigated_to: resolved };
      }
      case 'get_current_page':
        return { path: location.pathname };
      case 'get_workspace_state':
        return { page: location.pathname };
      case 'switch_model':
        return { success: true, note: 'Model switch handled by context' };
      case 'switch_theme':
        return { success: true, note: 'Theme switch handled by context' };
      case 'read_page_content': {
        const main = document.querySelector('main') || document.querySelector('.flex-1');
        const content = main?.textContent?.replace(/\s+/g, ' ').trim().slice(0, 2000) || '';
        return { success: true, page: location.pathname, content };
      }
      default:
        return { success: false, error: `Unknown browser function: ${name}` };
    }
  }, [navigate, location.pathname]);

  // ── WebSocket message handler ─────────────────────────────────────
  const handleMessage = useCallback((raw: string) => {
    let msg: any;
    try { msg = JSON.parse(raw); } catch (_) { return; }
    const mt = msg.type || '';

    switch (mt) {
      case 'setup_complete':
        setState(prev => ({
          ...prev,
          connected: true,
          sessionId: msg.sessionId,
          reconnecting: false,
          error: null,
        }));
        addTranscript('system', msg.resumed ? 'Session resumed! Mic active.' : 'Connected! Mic active.');
        // Start mic for Gemini, speech recognition for Claude
        if (stateRef.current.mode === 'gemini') {
          startMic();
        } else if (stateRef.current.mode === 'claude') {
          startSpeechRecognition();
        }
        emit('connected', { sessionId: msg.sessionId, resumed: msg.resumed });
        break;

      case 'audio':
        playAudioChunk(msg.data);
        break;

      case 'text':
        addTranscript('model', msg.text);
        // Claude mode: speak the text via browser TTS
        if (stateRef.current.mode === 'claude') {
          speakText(msg.text);
        }
        break;

      case 'transcript':
        addTranscript(msg.role === 'user' ? 'user' : 'model', msg.text);
        break;

      case 'turn_complete':
        setState(prev => ({ ...prev, turnCount: msg.turn || prev.turnCount + 1 }));
        emit('turn_complete', { turn: msg.turn });
        break;

      case 'function_call': {
        const fnName = msg.name;
        const fnArgs = msg.args || {};
        addFunctionLog(fnName, fnArgs, msg.server_handled);
        addTranscript('system', `Function: ${fnName}(${JSON.stringify(fnArgs).slice(0, 100)})`);

        // Browser-side functions: execute locally and send result back
        if (!msg.server_handled) {
          const result = executeBrowserFunction(fnName, fnArgs);
          updateFunctionLog(fnName, result, result.success ? 'success' : 'error');
          emit('function_result', { name: fnName, result });
          // Send result back through WS
          const ws = wsRef.current;
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
              type: 'browser_function_result',
              name: fnName,
              result,
            }));
          }
        }
        break;
      }

      case 'function_result':
        updateFunctionLog(msg.name, msg.result, msg.result?.success ? 'success' : 'error');
        addTranscript('system', `${msg.name} → ${msg.result?.success ? 'OK' : 'Error'}`);
        break;

      case 'go_away':
        sessionTokenRef.current = msg.session_token || null;
        addTranscript('system', 'Reconnecting...');
        setState(prev => ({ ...prev, reconnecting: true }));
        // Will auto-reconnect
        break;

      case 'error':
        setState(prev => ({ ...prev, error: msg.message }));
        addTranscript('system', `Error: ${msg.message}`);
        emit('error', { message: msg.message });
        break;
    }
  }, [addTranscript, addFunctionLog, updateFunctionLog, emit, playAudioChunk, speakText, startMic, startSpeechRecognition, executeBrowserFunction]);

  // ── Connect ───────────────────────────────────────────────────────
  const connect = useCallback((mode: VoxMode, config?: Partial<VoxConfig>) => {
    const voice = config?.voice || state.voice;
    const model = config?.model || '';
    const systemPrompt = config?.systemPrompt || '';

    setState(prev => ({ ...prev, mode, voice, error: null, transcript: [], functionLog: [], turnCount: 0, functionCount: 0 }));

    try {
      const ws = new WebSocket(`${WS_BASE}/ws/vox`);
      wsRef.current = ws;

      ws.onopen = () => {
        const initMsg: any = { type: 'start', mode, voice, model, systemPrompt };
        if (sessionTokenRef.current && mode === 'gemini') {
          initMsg.session_token = sessionTokenRef.current;
        }
        ws.send(JSON.stringify(initMsg));
      };

      ws.onmessage = (event) => handleMessage(event.data);

      ws.onerror = () => {
        setState(prev => ({ ...prev, error: 'Connection error' }));
      };

      ws.onclose = () => {
        setState(prev => {
          if (prev.connected && !prev.reconnecting) {
            return { ...prev, connected: false };
          }
          return { ...prev, connected: false };
        });
        stopMic();
        stopSpeechRecognition();
      };
    } catch (err: any) {
      setState(prev => ({ ...prev, error: err.message }));
    }
  }, [state.voice, handleMessage, stopMic, stopSpeechRecognition]);

  // ── Disconnect ────────────────────────────────────────────────────
  const disconnect = useCallback(() => {
    stopMic();
    stopSpeechRecognition();
    if (wsRef.current) {
      try {
        wsRef.current.send(JSON.stringify({ type: 'end' }));
      } catch (_) {}
      wsRef.current.close();
      wsRef.current = null;
    }
    if (playCtxRef.current) {
      playCtxRef.current.close().catch(() => {});
      playCtxRef.current = null;
    }
    setState(prev => ({
      ...prev,
      connected: false,
      sessionId: null,
      listening: false,
      speaking: false,
      mode: null,
    }));
    emit('disconnected', {});
  }, [stopMic, stopSpeechRecognition, emit]);

  // ── Toggle mic ────────────────────────────────────────────────────
  const toggleMic = useCallback(() => {
    if (state.listening) {
      stopMic();
      stopSpeechRecognition();
    } else {
      if (state.mode === 'gemini') startMic();
      else if (state.mode === 'claude') startSpeechRecognition();
    }
  }, [state.listening, state.mode, startMic, stopMic, startSpeechRecognition, stopSpeechRecognition]);

  // ── Send text ─────────────────────────────────────────────────────
  const sendText = useCallback((text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    addTranscript('user', text);
    wsRef.current.send(JSON.stringify({ type: 'text', text }));
  }, [addTranscript]);

  // ── Set voice ─────────────────────────────────────────────────────
  const setVoice = useCallback((v: string) => {
    setState(prev => ({ ...prev, voice: v }));
    localStorage.setItem('voxVoice', v);
  }, []);

  // ── Cleanup on unmount ────────────────────────────────────────────
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (_) {}
      }
      if (captureCtxRef.current) {
        captureCtxRef.current.close().catch(() => {});
      }
      if (micStreamRef.current) {
        micStreamRef.current.getTracks().forEach(t => t.stop());
      }
      if (playCtxRef.current) {
        playCtxRef.current.close().catch(() => {});
      }
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (_) {}
      }
    };
  }, []);

  return {
    state,
    connect,
    disconnect,
    toggleMic,
    sendText,
    setVoice,
    on,
    off,
  };
}
