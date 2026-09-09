import React from 'react';
import { useChat } from '../../context/ChatContext';

export const FloatingReactions: React.FC = () => {
  const { floatingReactions } = useChat();

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-20">
      {floatingReactions.map((reaction) => (
        <div
          key={reaction.id}
          className="absolute bottom-24 right-12 text-3xl animate-float-up select-none filter drop-shadow-lg"
          style={{
            transform: `translateX(${reaction.xOffset}px)`,
          }}
        >
          {reaction.emoji}
        </div>
      ))}
    </div>
  );
};
