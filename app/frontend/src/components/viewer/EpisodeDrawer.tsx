import React from 'react';
import { useApp } from '../../context/AppContext';
import { Story, Episode } from '../../types';
import { X, Lock, Play, Sparkles } from 'lucide-react';

interface EpisodeDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  story: Story;
  currentEpisode: Episode;
  onSelectEpisode: (ep: Episode) => void;
}

export const EpisodeDrawer: React.FC<EpisodeDrawerProps> = ({
  isOpen,
  onClose,
  story,
  currentEpisode,
  onSelectEpisode,
}) => {
  const { unlockedEpisodes, coins, setIsCoinModalOpen } = useApp();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md bg-welele-surface h-full border-l border-white/10 p-5 flex flex-col shadow-2xl animate-slide-left">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-1.5">
              Episodes List
              <span className="text-xs text-welele-muted">
                ({story.episodes.length} episodes)
              </span>
            </h3>
            <p className="text-xs text-welele-orange truncate max-w-[280px]">
              {story.title}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close Episode Drawer"
            className="w-8 h-8 rounded-[7px] bg-white/5 hover:bg-white/10 flex items-center justify-center text-welele-muted hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Quick Info Bar */}
        <div className="my-3 p-2.5 rounded-[7px] bg-welele-surface-2 border border-white/5 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="text-welele-muted">Your Coins:</span>
            <span className="font-bold text-welele-gold">🪙 {coins}</span>
          </div>
          <button
            onClick={() => setIsCoinModalOpen(true)}
            className="text-[11px] font-bold text-welele-orange hover:underline"
          >
            + Get More Coins
          </button>
        </div>

        {/* Episodes Scroll List */}
        <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
          {story.episodes.map((ep) => {
            const isCurrent = currentEpisode.id === ep.id;
            const isUnlocked = ep.is_free || unlockedEpisodes.has(ep.id);

            return (
              <div
                key={ep.id}
                onClick={() => {
                  onSelectEpisode(ep);
                  onClose();
                }}
                className={`p-3 rounded-[7px] border flex items-center gap-3 cursor-pointer transition-all ${
                  isCurrent
                    ? 'border-welele-orange bg-welele-orange/15 shadow-md shadow-orange-500/10'
                    : 'border-white/5 bg-welele-surface-2/60 hover:border-white/15'
                }`}
              >
                {/* Thumbnail & Status Badge */}
                <div className="relative w-16 h-20 rounded-[7px] overflow-hidden shrink-0 bg-black">
                  <img
                    src={ep.thumbnail_url}
                    alt={ep.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                    {isCurrent ? (
                      <div className="w-6 h-6 rounded-[7px] bg-welele-orange text-black flex items-center justify-center font-bold text-xs">
                        ▶
                      </div>
                    ) : isUnlocked ? (
                      <Play className="w-4 h-4 text-white/80" />
                    ) : (
                      <Lock className="w-4 h-4 text-welele-gold" />
                    )}
                  </div>
                  <span className="absolute bottom-1 right-1 px-1 py-0.2 rounded-[7px] bg-black/80 text-[9px] text-white/90 font-mono">
                    {ep.duration_seconds}s
                  </span>
                </div>

                {/* Episode Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-[11px] font-bold text-welele-orange">
                      EP {ep.episode_number}
                    </span>
                    {!isUnlocked && (
                      <span className="text-[10px] font-extrabold text-welele-gold px-1.5 py-0.5 rounded-[7px] bg-amber-500/15 border border-amber-500/30 flex items-center gap-0.5">
                        🪙 {ep.coin_price || 5}
                      </span>
                    )}
                    {ep.is_free && (
                      <span className="text-[10px] font-bold text-emerald-400 px-1.5 py-0.5 rounded-[7px] bg-emerald-500/15 border border-emerald-500/30">
                        FREE
                      </span>
                    )}
                  </div>
                  <h4 className="text-xs font-bold text-white truncate mt-0.5">
                    {ep.title}
                  </h4>
                  <p className="text-[11px] text-welele-muted line-clamp-2 mt-0.5">
                    {ep.synopsis}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
