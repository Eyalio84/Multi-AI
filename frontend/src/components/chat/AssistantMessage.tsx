import React from 'react';
import { Message } from '../../types/index';
import { renderTextWithCodeBlocks } from '../../utils/ui';

interface Props {
  message: Message;
  onUseImage?: (url: string) => void;
}

const AssistantMessage: React.FC<Props> = ({ message, onUseImage }) => {
  const textContent = message.parts.map(p => p.text).filter(Boolean).join('\n');

  return (
    <div className="t-card p-3 rounded-2xl max-w-lg lg:max-w-2xl xl:max-w-4xl break-words rounded-bl-none" style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}>
      {/* Thinking block */}
      {message.thinkingContent && (
        <details className="mb-2 text-xs">
          <summary className="cursor-pointer font-medium" style={{ color: 'var(--t-accent1)' }}>Thinking...</summary>
          <div className="mt-1 p-2 rounded whitespace-pre-wrap max-h-40 overflow-y-auto" style={{ background: 'var(--t-surface)', color: 'var(--t-muted)' }}>
            {message.thinkingContent}
          </div>
        </details>
      )}

      {/* Content */}
      {message.parts.map((part, i) => (
        <div key={i}>
          {part.text && <div className="whitespace-pre-wrap">{renderTextWithCodeBlocks(part.text)}</div>}
          {part.imageUrl && (
            <div className="mt-2">
              <img src={part.imageUrl} alt="content" className="rounded-lg max-w-xs md:max-w-sm" />
              {onUseImage && (
                <button onClick={() => onUseImage(part.imageUrl!)} className="t-btn mt-1 px-2 py-1 text-xs rounded transition-colors" style={{ background: 'var(--t-surface2)', color: 'var(--t-text)' }}>
                  Use this image
                </button>
              )}
            </div>
          )}
          {part.audioUrl && (
            <div className="mt-2">
              <audio src={part.audioUrl} controls className="w-full max-w-sm" />
            </div>
          )}
          {part.videoUrl && (
            <video src={part.videoUrl} controls className="mt-2 rounded-lg max-w-sm" />
          )}
        </div>
      ))}

      {/* Tool call info */}
      {message.toolCall && (
        <div className="mt-2 p-2 border rounded-lg text-sm" style={{ background: 'var(--t-surface)', borderColor: 'var(--t-border)' }}>
          <div className="flex items-center gap-2 font-mono text-xs" style={{ color: 'var(--t-primary)' }}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
            Tool: {message.toolCall.name}
          </div>
          <pre className="mt-1 p-2 rounded text-xs overflow-x-auto" style={{ background: 'var(--t-bg)', color: 'var(--t-text2)' }}><code>{JSON.stringify(message.toolCall.args, null, 2)}</code></pre>
        </div>
      )}

      {/* Grounding sources */}
      {message.groundingMetadata && message.groundingMetadata.length > 0 && (
        <div className="mt-3 pt-2 border-t" style={{ borderColor: 'var(--t-border)' }}>
          <h4 className="text-xs font-semibold mb-1" style={{ color: 'var(--t-text2)' }}>Sources</h4>
          <ul className="space-y-0.5">
            {message.groundingMetadata.map((g, i) => (
              <li key={i} className="text-xs">
                <a href={g.web.uri} target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: 'var(--t-primary)' }}>
                  {g.web.title || g.web.uri}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Provider badge */}
      <div className="mt-2 flex justify-end">
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${message.provider === 'claude' ? 'bg-orange-800/50 text-orange-300' : 'bg-blue-800/50 text-blue-300'}`}>
          {message.provider === 'claude' ? 'Claude' : 'Gemini'}
        </span>
      </div>
    </div>
  );
};

export default AssistantMessage;
