import { useState, useCallback } from 'react';
import { Message, MessageAuthor, MessagePart, ToolCall, ChatMode, Project, Persona, CustomAiStyle } from '../types/index';
import { generateUniqueId } from '../utils/common';
import * as apiService from '../services/apiService';

export const useChat = (
  projects: Project[],
  persona: Persona,
  provider: 'gemini' | 'claude',
  model: string,
  useWebSearch: boolean,
  customStyles: CustomAiStyle[],
  thinkingBudget: number,
  aiFileOperations: {
    listFiles: (projectId: string) => Promise<string[]>;
    createFile: (projectId: string, path: string, content: string) => Promise<any>;
    readFile: (projectId: string, path: string) => Promise<string | null>;
    updateFile: (projectId: string, path: string, newContent: string) => Promise<any>;
    deleteFile: (projectId: string, path: string) => Promise<boolean>;
  },
) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [injectionMeta, setInjectionMeta] = useState<{ memories?: boolean; skills?: boolean } | null>(null);

  const addMessage = useCallback((author: MessageAuthor, parts: MessagePart[], extra?: Partial<Message>) => {
    const msg: Message = { id: generateUniqueId(), author, parts, provider, ...extra };
    setMessages(prev => [...prev, msg]);
    return msg;
  }, [provider]);

  const handleToolCall = useCallback(async (toolCall: ToolCall, relatedProjects: Project[]): Promise<any> => {
    const { name, args } = toolCall;
    const targetProjectId = relatedProjects[0]?.id;
    try {
      switch (name) {
        case 'runPython': {
          const pyodide = (window as any).loadPyodide;
          if (!pyodide) return { error: 'Pyodide not loaded' };
          const py = await pyodide();
          const result = py.runPython(args.code);
          return { result: String(result), originalCode: args.code };
        }
        case 'searchNpm': {
          const res = await fetch(`/api/npm-search?packageName=${encodeURIComponent(args.packageName)}`);
          return res.json();
        }
        case 'listFiles':
          if (!targetProjectId) throw new Error('No project selected');
          return { files: await aiFileOperations.listFiles(targetProjectId) };
        case 'createFile':
          if (!targetProjectId) throw new Error('No project selected');
          await aiFileOperations.createFile(targetProjectId, args.path, args.content);
          return { success: true, message: `Created ${args.path}` };
        case 'readFile':
          if (!targetProjectId) throw new Error('No project selected');
          return { content: (await aiFileOperations.readFile(targetProjectId, args.path)) ?? `Not found: ${args.path}` };
        case 'updateFile':
          if (!targetProjectId) throw new Error('No project selected');
          await aiFileOperations.updateFile(targetProjectId, args.path, args.newContent);
          return { success: true, message: `Updated ${args.path}` };
        case 'deleteFile':
          if (!targetProjectId) throw new Error('No project selected');
          const ok = await aiFileOperations.deleteFile(targetProjectId, args.path);
          return { success: ok, message: ok ? `Deleted ${args.path}` : `Not found: ${args.path}` };
        default:
          return { error: `Unknown tool: ${name}` };
      }
    } catch (e: any) {
      return { error: e.message };
    }
  }, [aiFileOperations]);

  const processAgentStream = useCallback(async (stream: ReadableStream<Uint8Array>) => {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let currentResponse: Message | null = null;
    let accText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n').filter(l => l.startsWith('data: '));

      for (const line of lines) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'conversation_start' || data.type === 'injection_meta' || data.type === 'done') continue;

          if (!currentResponse) {
            currentResponse = { id: generateUniqueId(), author: MessageAuthor.ASSISTANT, parts: [{ text: '' }], provider: 'claude' };
            setMessages(prev => [...prev, currentResponse!]);
          }

          if (data.type === 'token' && currentResponse) {
            accText += data.content;
            currentResponse.parts = [{ text: accText }];
            setMessages(prev => prev.map(m => m.id === currentResponse!.id ? { ...currentResponse! } : m));
          } else if (data.type === 'error' && currentResponse) {
            accText += `\n\nError: ${data.content}`;
            currentResponse.parts = [{ text: accText }];
            setMessages(prev => prev.map(m => m.id === currentResponse!.id ? { ...currentResponse! } : m));
          }
        } catch {}
      }
    }
  }, []);

  const processSSEStream = useCallback(async (stream: ReadableStream<Uint8Array>, existingMessages: Message[], currentMode: ChatMode) => {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let currentResponse: Message | null = null;
    let accText = '';
    let accThinking = '';
    let pendingToolCall: ToolCall | null = null;
    let toolCallJson = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n').filter(l => l.startsWith('data: '));

      for (const line of lines) {
        try {
          const data = JSON.parse(line.slice(6));

          // Track conversation and injection metadata
          if (data.type === 'conversation_start') {
            setConversationId(data.conversation_id);
            continue;
          }
          if (data.type === 'injection_meta') {
            setInjectionMeta({ memories: data.memories, skills: data.skills });
            continue;
          }

          if (!currentResponse && data.type !== 'done') {
            currentResponse = { id: generateUniqueId(), author: MessageAuthor.ASSISTANT, parts: [{ text: '' }], provider };
            setMessages(prev => [...prev, currentResponse!]);
          }

          if (data.type === 'token' && currentResponse) {
            accText += data.content;
            currentResponse.parts = [{ text: accText }];
            setMessages(prev => prev.map(m => m.id === currentResponse!.id ? { ...currentResponse! } : m));
          } else if (data.type === 'thinking_start') {
            accThinking = '';
          } else if (data.type === 'thinking' && currentResponse) {
            accThinking += data.content;
            currentResponse.thinkingContent = accThinking;
            setMessages(prev => prev.map(m => m.id === currentResponse!.id ? { ...currentResponse! } : m));
          } else if (data.type === 'tool_call' && currentResponse) {
            pendingToolCall = { name: data.name, args: data.args };
          } else if (data.type === 'tool_call_start') {
            pendingToolCall = { id: data.id, name: data.name, args: {} };
            toolCallJson = '';
          } else if (data.type === 'tool_call_delta') {
            toolCallJson += data.content;
          } else if (data.type === 'grounding' && currentResponse) {
            currentResponse.groundingMetadata = data.sources.map((s: any) => ({ web: s }));
            setMessages(prev => prev.map(m => m.id === currentResponse!.id ? { ...currentResponse! } : m));
          } else if (data.type === 'error') {
            if (currentResponse) {
              accText += `\n\nError: ${data.content}`;
              currentResponse.parts = [{ text: accText }];
              setMessages(prev => prev.map(m => m.id === currentResponse!.id ? { ...currentResponse! } : m));
            }
          }
        } catch {}
      }
    }

    // Finalize tool call from deltas
    if (pendingToolCall && toolCallJson && !pendingToolCall.args?.path) {
      try { pendingToolCall.args = JSON.parse(toolCallJson); } catch {}
    }

    // Handle tool calls
    if (pendingToolCall && currentResponse) {
      currentResponse.toolCall = pendingToolCall;
      setMessages(prev => prev.map(m => m.id === currentResponse!.id ? { ...currentResponse! } : m));

      const activeProjects = currentMode === 'coding' ? projects : [];
      const toolResult = await handleToolCall(pendingToolCall, activeProjects);
      const toolMessage = addMessage(MessageAuthor.TOOL, [], {
        toolResponse: { name: pendingToolCall.name, tool_use_id: pendingToolCall.id, response: { content: toolResult } },
      });

      // Follow-up with tool result
      const history = [...existingMessages, currentResponse, toolMessage];
      const followUpStream = await apiService.streamCoding(history, activeProjects, persona, provider, model, useWebSearch, customStyles, thinkingBudget);
      await processSSEStream(followUpStream, history, currentMode);
    }
  }, [addMessage, projects, persona, provider, model, useWebSearch, customStyles, thinkingBudget, handleToolCall]);

  const handleSlashCommand = async (prompt: string): Promise<boolean> => {
    if (!prompt.startsWith('/')) return false;
    const [cmd, ...rest] = prompt.slice(1).split(' ');
    const arg = rest.join(' ');

    switch (cmd.toLowerCase()) {
      case 'help':
        addMessage(MessageAuthor.SYSTEM, [{ text:
          'Available commands:\n' +
          '  /image <prompt> — Generate an image\n' +
          '  /tts <text> — Text-to-speech\n' +
          '  /video <prompt> — Generate a video\n' +
          '  /agent <prompt> — Run an autonomous agent\n' +
          '  /help — Show this help'
        }]);
        return true;

      case 'image':
        if (!arg) { addMessage(MessageAuthor.SYSTEM, [{ text: 'Usage: /image <prompt>' }]); return true; }
        addMessage(MessageAuthor.USER, [{ text: prompt }]);
        setStatusText('Generating image...');
        try {
          const results = await apiService.generateImageSDK(arg);
          const parts: MessagePart[] = Array.isArray(results)
            ? results.map((r: any) => ({ imageUrl: r.imageUrl, text: r.text }))
            : [{ text: JSON.stringify(results) }];
          addMessage(MessageAuthor.ASSISTANT, parts, { provider: 'gemini' });
        } catch (e: any) {
          addMessage(MessageAuthor.SYSTEM, [{ text: `Image error: ${e.message}` }]);
        }
        return true;

      case 'tts':
        if (!arg) { addMessage(MessageAuthor.SYSTEM, [{ text: 'Usage: /tts <text>' }]); return true; }
        addMessage(MessageAuthor.USER, [{ text: prompt }]);
        setStatusText('Generating speech...');
        try {
          const result = await apiService.generateTTSSDK(arg);
          addMessage(MessageAuthor.ASSISTANT, [{ audioUrl: result.audioUrl, text: `TTS generated (${result.duration?.toFixed(1) || '?'}s)` }], { provider: 'gemini' });
        } catch (e: any) {
          addMessage(MessageAuthor.SYSTEM, [{ text: `TTS error: ${e.message}` }]);
        }
        return true;

      case 'video':
        if (!arg) { addMessage(MessageAuthor.SYSTEM, [{ text: 'Usage: /video <prompt>' }]); return true; }
        addMessage(MessageAuthor.USER, [{ text: prompt }]);
        setStatusText('Starting video generation...');
        try {
          const result = await apiService.generateVideoSDK(arg);
          addMessage(MessageAuthor.ASSISTANT, [{ text: `Video generation started.\nOperation: ${result.operationName}\n\nUse the video status endpoint to check progress.` }], { provider: 'gemini' });
        } catch (e: any) {
          addMessage(MessageAuthor.SYSTEM, [{ text: `Video error: ${e.message}` }]);
        }
        return true;

      case 'agent':
        if (!arg) { addMessage(MessageAuthor.SYSTEM, [{ text: 'Usage: /agent <prompt>' }]); return true; }
        const agentMsg = addMessage(MessageAuthor.USER, [{ text: prompt }]);
        setStatusText('Running Claude agent...');
        try {
          const agentHistory = [...messages, agentMsg];
          const stream = await apiService.streamChat(agentHistory, 'claude', 'claude-sonnet-4-6', persona, customStyles, false, 0);
          await processAgentStream(stream);
        } catch (e: any) {
          addMessage(MessageAuthor.SYSTEM, [{ text: `Agent error: ${e.message}` }]);
        }
        return true;

      default:
        return false;
    }
  };

  const sendMessage = async (prompt: string, mode: ChatMode, file?: File | null) => {
    if (isLoading) return;
    setIsLoading(true);
    setStatusText('Thinking...');

    try {
      // Check for slash commands first
      if (await handleSlashCommand(prompt)) return;

      const userParts: MessagePart[] = [{ text: prompt }];
      if (mode === 'image-edit' && file) userParts.push({ imageUrl: URL.createObjectURL(file) });
      const userMessage = addMessage(MessageAuthor.USER, userParts);

      if (mode === 'image-edit') {
        if (!file) throw new Error('Image file required');
        const resultParts = await apiService.editImage(prompt, file);
        addMessage(MessageAuthor.ASSISTANT, resultParts);
      } else if (mode === 'video-gen') {
        const resultParts = await apiService.generateVideo(prompt, file || null, setStatusText);
        addMessage(MessageAuthor.ASSISTANT, resultParts);
      } else {
        const history = [...messages, userMessage];
        const activeProjects = mode === 'coding' ? projects : [];
        const stream = await apiService.streamCoding(history, activeProjects, persona, provider, model, useWebSearch, customStyles, thinkingBudget);
        await processSSEStream(stream, history, mode);
      }
    } catch (e: any) {
      addMessage(MessageAuthor.SYSTEM, [{ text: `Error: ${e.message}` }]);
    } finally {
      setIsLoading(false);
      setStatusText('');
    }
  };

  const clearMessages = () => setMessages([]);

  return { messages, isLoading, statusText, sendMessage, clearMessages, conversationId, injectionMeta };
};
