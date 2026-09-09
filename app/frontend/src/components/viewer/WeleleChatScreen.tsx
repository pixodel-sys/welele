import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { useChat } from '../../context/ChatContext';
import { MessageSquare, Send, Sparkles, Flame, Heart } from 'lucide-react';

export const WeleleChatScreen: React.FC = () => {
  const { currentStory, currentEpisode } = useApp();
  const { comments, addComment, triggerReaction } = useChat();
  const [text, setText] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || !currentEpisode) return;
    await addComment(
      currentEpisode.id,
      text,
      'Temi Adebayo',
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80'
    );
    setText('');
  };

  return (
    <div className="space-y-4 pb-24 max-w-lg mx-auto">
      {/* Header Info */}
      <div className="p-4 rounded-[7px] bg-welele-surface-2 border border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-[7px] bg-gradient-welele flex items-center justify-center text-white shadow">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              Welele Story Chat™
              <span className="w-2 h-2 rounded-circle bg-emerald-400 animate-pulse" />
            </h3>
            <p className="text-xs text-welele-muted">
              Live room: <span className="text-welele-orange font-semibold">{currentStory?.title || 'General Chat'}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 bg-black/40 px-2 py-1 rounded-[7px] border border-white/5 text-[11px] text-welele-gold font-bold">
          🔥 Live Room
        </div>
      </div>

      {/* Floating Reaction Bar */}
      <div className="flex items-center justify-between bg-welele-surface-2/80 px-4 py-2.5 rounded-[7px] border border-white/5">
        <span className="text-xs text-welele-muted font-medium">Quick React:</span>
        <div className="flex items-center gap-2">
          {['🔥', '👑', '😱', '👏', '⚡'].map((emoji) => (
            <button
              key={emoji}
              onClick={() => currentEpisode && triggerReaction(currentEpisode.id, emoji)}
              className="w-8 h-8 rounded-[7px] hover:bg-white/10 flex items-center justify-center text-lg transition-transform active:scale-125"
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>

      {/* Comments List */}
      <div className="space-y-2.5 min-h-[320px]">
        {comments.map((comment) => (
          <div
            key={comment.id}
            className="p-3 rounded-[7px] bg-welele-surface-2/70 border border-white/5 hover:border-white/10 transition-colors"
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <img
                  src={comment.avatar}
                  alt={comment.user_name}
                  className="w-6 h-6 rounded-circle object-cover border border-white/10"
                />
                <span className="text-xs font-bold text-white">{comment.user_name}</span>
              </div>
              <span className="text-[10px] text-welele-muted">{comment.time_ago}</span>
            </div>
            <p className="text-xs text-white/90 pl-8">{comment.text}</p>
          </div>
        ))}
      </div>

      {/* Post Form */}
      <form onSubmit={handleSubmit} className="flex gap-2 sticky bottom-16 pt-2">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Share your thoughts or theories on this cliffhanger..."
          className="flex-1 bg-welele-surface-2 px-4 py-3 rounded-[7px] border border-white/10 text-xs text-white placeholder-welele-muted focus:outline-none focus:border-welele-orange shadow-lg"
        />
        <button
          type="submit"
          className="px-5 py-3 rounded-[7px] bg-gradient-welele text-white font-bold text-xs shadow-lg shadow-orange-500/20 hover:opacity-90 flex items-center justify-center"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
