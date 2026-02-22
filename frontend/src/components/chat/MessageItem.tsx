import React from 'react';
import { Message, MessageAuthor } from '../../types/index';
import AssistantMessage from './AssistantMessage';
import UserMessage from './UserMessage';
import ToolMessage from './ToolMessage';

interface Props {
  message: Message;
  onUseImage?: (url: string) => void;
}

const AuthorIcon: React.FC<{ author: MessageAuthor; provider?: string }> = ({ author, provider }) => {
  const base = 'h-8 w-8 rounded-full flex items-center justify-center font-bold flex-shrink-0 text-xs';
  const textStyle = { color: 'var(--t-text)' };
  if (author === MessageAuthor.USER) return <div className={`${base}`} style={{ ...textStyle, background: 'var(--t-primary)' }}>U</div>;
  if (author === MessageAuthor.TOOL) return <div className={`${base}`} style={{ ...textStyle, background: 'var(--t-success)' }}>T</div>;
  return <div className={`${base}`} style={{ ...textStyle, background: provider === 'claude' ? 'var(--t-accent2)' : 'var(--t-accent1)' }}>AI</div>;
};

const MessageItem: React.FC<Props> = ({ message, onUseImage }) => {
  if (message.author === MessageAuthor.SYSTEM) {
    return (
      <div className="text-center my-2 text-xs italic" style={{ color: 'var(--t-muted)' }}>
        {message.parts.map((p, i) => p.text && <span key={i}>{p.text}</span>)}
      </div>
    );
  }

  const isUser = message.author === MessageAuthor.USER;

  return (
    <div className={`flex items-start gap-3 my-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <AuthorIcon author={message.author} provider={message.provider} />
      <div className={`flex flex-col w-full ${isUser ? 'items-end' : 'items-start'}`}>
        {message.author === MessageAuthor.USER && <UserMessage message={message} />}
        {message.author === MessageAuthor.ASSISTANT && <AssistantMessage message={message} onUseImage={onUseImage} />}
        {message.author === MessageAuthor.TOOL && <ToolMessage message={message} />}
      </div>
    </div>
  );
};

export default React.memo(MessageItem);
