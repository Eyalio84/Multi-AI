import React from 'react';
import { Message } from '../../types/index';

const UserMessage: React.FC<{ message: Message }> = ({ message }) => (
  <div className="t-card p-3 rounded-2xl max-w-lg lg:max-w-2xl xl:max-w-4xl break-words rounded-br-none" style={{ background: 'var(--t-primary)', color: 'var(--t-text)' }}>
    {message.parts.map((part, i) => (
      <div key={i}>
        {part.text && <div className="whitespace-pre-wrap">{part.text}</div>}
        {part.imageUrl && <img src={part.imageUrl} alt="uploaded" className="mt-2 rounded-lg max-w-xs" />}
      </div>
    ))}
  </div>
);

export default UserMessage;
