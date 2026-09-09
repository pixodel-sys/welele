import React, { createContext, useContext, useState, useEffect } from 'react';
import { Comment, Reaction } from '../types';
import { chatApi } from '../services/api';

interface FloatingReaction {
  id: string;
  emoji: string;
  xOffset: number;
}

interface ChatContextType {
  comments: Comment[];
  loadingComments: boolean;
  addComment: (episodeId: string, text: string, userName: string, avatar: string) => Promise<void>;
  floatingReactions: FloatingReaction[];
  triggerReaction: (episodeId: string, emoji: string) => void;
  loadEpisodeComments: (episodeId: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loadingComments, setLoadingComments] = useState<boolean>(false);
  const [floatingReactions, setFloatingReactions] = useState<FloatingReaction[]>([]);

  const loadEpisodeComments = async (episodeId: string) => {
    try {
      setLoadingComments(true);
      const res = await chatApi.getComments(episodeId);
      setComments(res.comments);
    } catch (err) {
      console.error("Failed to load comments:", err);
    } finally {
      setLoadingComments(false);
    }
  };

  const addComment = async (episodeId: string, text: string, userName: string, avatar: string) => {
    try {
      const res = await chatApi.postComment(episodeId, { user_name: userName, text, avatar });
      if (res.comment) {
        setComments(prev => [res.comment, ...prev]);
      }
    } catch (err) {
      console.error("Failed to post comment:", err);
    }
  };

  const triggerReaction = (episodeId: string, emoji: string) => {
    const newReaction: FloatingReaction = {
      id: `${Date.now()}_${Math.random()}`,
      emoji,
      xOffset: Math.floor(Math.random() * 80) - 40, // random dispersion
    };

    setFloatingReactions(prev => [...prev, newReaction]);

    // Send to backend
    chatApi.sendReaction(episodeId, { emoji, timestamp_seconds: Math.floor(Date.now() / 1000) }).catch(() => {});

    // Remove reaction after animation completes (2.5s)
    setTimeout(() => {
      setFloatingReactions(prev => prev.filter(r => r.id !== newReaction.id));
    }, 2400);
  };

  return (
    <ChatContext.Provider
      value={{
        comments,
        loadingComments,
        addComment,
        floatingReactions,
        triggerReaction,
        loadEpisodeComments,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within ChatProvider');
  return context;
};
