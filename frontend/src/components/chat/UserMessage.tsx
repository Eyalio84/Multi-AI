import React from 'react';
import { Message } from '../../types/index';

const UserMessage: React.FC<{ message: Message }> = ({ message }) => (
  <div className="t-card p-3 rounded-2xl max-w-full break-words rounded-br-none overflow-hidden" style={{ background: 'var(--t-primary)', color: 'var(--t-text)', overflowWrap: 'anywhere' }}>
    {message.parts.map((part, i) => (
      <div key={i}>
        {part.text && <div className="whitespace-pre-wrap">{part.text}</div>}
        {part.imageUrl && <img src={part.imageUrl} alt="uploaded" className="mt-2 rounded-lg max-w-xs" />}
      </div>
    ))}
  </div>
);

export default UserMessage;
