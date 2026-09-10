import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { Story, Episode } from '../../types';
import {
  X,
  Play,
  Lock,
  Star,
  Plus,
  Heart,
  Bookmark,
  Share2,
  Download,
  Check,
  Languages,
  Film,
} from 'lucide-react';

interface StoryDetailModalProps {
  story: Story | null;
  onClose: () => void;
  onPlayEpisode: (story: Story, episode: Episode) => void;
}

export const StoryDetailModal: React.FC<StoryDetailModalProps> = ({
  story,
  onClose,
  onPlayEpisode,
}) => {
  const {
    unlockedEpisodes,
    likedStories,
    toggleLikeStory,
    bookmarks,
    toggleBookmark,
  } = useApp();

  const [activeTab, setActiveTab] = useState<'episodes' | 'about' | 'more'>('episodes');

  if (!story) return null;

  const isLiked = likedStories.has(story.id);
  const isBookmarked = bookmarks.has(story.id);

  // Format seconds to mm:ss (e.g., 78 -> 01:18)
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-md animate-fade-in select-none">
      <div className="relative w-full max-w-lg bg-[#0E0F12] border border-white/10 rounded-[7px] shadow-2xl overflow-hidden max-h-[92vh] flex flex-col">
        {/* Top Floating Controls */}
        <div className="absolute top-3 left-3 right-3 z-30 flex items-center justify-between pointer-events-none">
          <button
            onClick={onClose}
            aria-label="Back"
            className="w-8 h-8 rounded-[7px] bg-black/60 hover:bg-black/90 backdrop-blur-md flex items-center justify-center text-white border border-white/10 pointer-events-auto transition-transform active:scale-95"
          >
            <X className="w-4 h-4" />
          </button>

          <button
            onClick={() => {
              if (navigator.share) {
                navigator.share({ title: story.title, text: story.synopsis, url: window.location.href }).catch(() => {});
              }
            }}
            aria-label="Share"
            className="w-8 h-8 rounded-[7px] bg-black/60 hover:bg-black/90 backdrop-blur-md flex items-center justify-center text-white border border-white/10 pointer-events-auto"
          >
            <Share2 className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Video / Cover Showcase Banner */}
        <div className="relative aspect-[16/10] w-full shrink-0 group">
          <img
            src={story.cover_image}
            alt={story.title}
            className="w-full h-full object-cover filter brightness-95"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0E0F12] via-[#0E0F12]/30 to-transparent" />

          {/* Central Hero Play Trigger */}
          <div
            onClick={() => {
              if (story.episodes.length > 0) {
                onPlayEpisode(story, story.episodes[0]);
                onClose();
              }
            }}
            className="absolute inset-0 flex items-center justify-center cursor-pointer"
          >
            <div className="w-14 h-14 rounded-[7px] bg-gradient-welele flex items-center justify-center text-white shadow-2xl shadow-orange-500/50 hover:scale-110 transition-transform">
              <Play className="w-6 h-6 fill-current ml-0.5" />
            </div>
          </div>
        </div>

        {/* Story Metadata & Title Bar */}
        <div className="px-5 pt-2 pb-3 border-b border-white/10 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xl sm:text-2xl font-black text-[#FFF8F0] tracking-tight">
              {story.title}
            </h2>
          </div>

          {/* Metadata Row */}
          <div className="flex items-center gap-2 text-xs text-welele-muted">
            <span className="text-welele-orange font-bold">{story.genre}</span>
            <span>•</span>
            <span>1 Season</span>
            <span>•</span>
            <span>
              {story.episodes?.length || story.total_episodes || 0}{' '}
              {(story.episodes?.length || story.total_episodes || 0) === 1 ? 'Episode' : 'Episodes'}
            </span>
            <span>•</span>
            <span className="px-1.5 py-0.2 rounded-[7px] bg-white/10 text-[10px] font-bold text-white">16+</span>
          </div>

          {/* Tagline / Hook */}
          <p className="text-xs text-white/90 leading-relaxed font-medium italic">
            "{story.tagline}"
          </p>

          {/* Action Row: My List, Like, Share */}
          <div className="flex items-center gap-6 pt-2">
            <button
              onClick={() => toggleBookmark(story.id)}
              className="flex items-center gap-1.5 text-xs text-white hover:text-welele-orange transition-colors"
            >
              {isBookmarked ? <Check className="w-4 h-4 text-emerald-400" /> : <Plus className="w-4 h-4" />}
              <span className="font-semibold">{isBookmarked ? 'Added' : 'My List'}</span>
            </button>

            <button
              onClick={() => toggleLikeStory(story.id)}
              className={`flex items-center gap-1.5 text-xs transition-colors ${
                isLiked ? 'text-welele-red' : 'text-white hover:text-welele-red'
              }`}
            >
              <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
              <span className="font-semibold">Like</span>
            </button>

            <button
              onClick={() => {
                if (navigator.share) {
                  navigator.share({ title: story.title, text: story.synopsis, url: window.location.href }).catch(() => {});
                }
              }}
              className="flex items-center gap-1.5 text-xs text-white hover:text-welele-orange transition-colors"
            >
              <Share2 className="w-4 h-4" />
              <span className="font-semibold">Share</span>
            </button>
          </div>
        </div>

        {/* Tab Header Navigation: Episodes | About | More Like This */}
        <div className="flex items-center px-5 border-b border-white/10 gap-6 text-xs font-bold">
          <button
            onClick={() => setActiveTab('episodes')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'episodes'
                ? 'border-welele-orange text-welele-orange'
                : 'border-transparent text-welele-muted hover:text-white'
            }`}
          >
            Episodes
          </button>
          <button
            onClick={() => setActiveTab('about')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'about'
                ? 'border-welele-orange text-welele-orange'
                : 'border-transparent text-welele-muted hover:text-white'
            }`}
          >
            About
          </button>
          <button
            onClick={() => setActiveTab('more')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'more'
                ? 'border-welele-orange text-welele-orange'
                : 'border-transparent text-welele-muted hover:text-white'
            }`}
          >
            More Like This
          </button>
        </div>

        {/* Tab Body Content */}
        <div className="p-5 overflow-y-auto flex-1 space-y-3">
          {activeTab === 'episodes' && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs text-welele-muted mb-1">
                <span className="font-bold text-white">Season 1</span>
                <span>
                  {story.free_episodes_count || story.episodes?.filter((e) => e.is_free).length || 0}{' '}
                  Free{' '}
                  {(story.free_episodes_count || story.episodes?.filter((e) => e.is_free).length || 0) === 1
                    ? 'Episode'
                    : 'Episodes'}
                </span>
              </div>

              {story.episodes.map((ep) => {
                const isUnlocked = ep.is_free || unlockedEpisodes.has(ep.id);
                return (
                  <div
                    key={ep.id}
                    onClick={() => {
                      onPlayEpisode(story, ep);
                      onClose();
                    }}
                    className="p-2.5 rounded-[7px] bg-[#15161A] hover:bg-welele-surface-2 border border-white/5 flex items-center justify-between cursor-pointer transition-all group hover:border-welele-orange/30"
                  >
                    <div className="flex items-center gap-3">
                      <div className="relative w-14 h-16 rounded-[7px] overflow-hidden shrink-0">
                        <img
                          src={ep.thumbnail_url || story.cover_image}
                          alt={ep.title}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                          {isUnlocked ? (
                            <Play className="w-4 h-4 text-white fill-current group-hover:scale-110 transition-transform" />
                          ) : (
                            <Lock className="w-4 h-4 text-welele-gold" />
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-bold text-white group-hover:text-welele-orange transition-colors">
                            {ep.episode_number}. {ep.title}
                          </h4>
                          {ep.is_free ? (
                            <span className="text-[8px] font-black text-emerald-400 px-1.5 py-0.2 rounded-[7px] bg-emerald-500/15">
                              FREE
                            </span>
                          ) : (
                            <span className="text-[8px] font-black text-welele-gold px-1.5 py-0.2 rounded-[7px] bg-amber-500/15">
                              🪙 {ep.coin_price || 5} COINS
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-welele-muted line-clamp-1 mt-0.5">
                          {ep.synopsis}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[11px] text-welele-muted font-mono font-medium">
                        {formatDuration(ep.duration_seconds)}
                      </span>
                      <Download className="w-3.5 h-3.5 text-welele-muted hover:text-white transition-colors" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {activeTab === 'about' && (
            <div className="space-y-4 text-xs">
              <div>
                <h4 className="font-bold text-welele-muted uppercase mb-1">Full Synopsis</h4>
                <p className="text-white/90 leading-relaxed">{story.synopsis}</p>
              </div>

              <div>
                <h4 className="font-bold text-welele-muted uppercase mb-1">Creator & Studio</h4>
                <div className="flex items-center gap-2.5 p-2 rounded-[7px] bg-welele-surface-2 border border-white/5">
                  <img src={story.creator_avatar} alt={story.creator_name} className="w-8 h-8 rounded-circle object-cover" />
                  <div>
                    <h5 className="font-bold text-white">{story.creator_name}</h5>
                    <span className="text-[10px] text-welele-orange">Verified Showrunner</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-bold text-welele-muted uppercase mb-1">Languages & Audio</h4>
                <div className="flex flex-wrap gap-1.5">
                  {story.available_languages.map((l) => (
                    <span key={l} className="px-2.5 py-1 rounded-[7px] bg-white/5 text-[11px] text-white">
                      {l}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'more' && (
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-1">
                <span className="text-[10px] font-bold text-welele-orange">Romance</span>
                <h4 className="text-xs font-bold text-white">Zulu Love Story</h4>
                <p className="text-[10px] text-welele-muted line-clamp-2">Prince Sipho meets a Braamfontein streetwear designer.</p>
              </div>
              <div className="p-3 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-1">
                <span className="text-[10px] font-bold text-welele-orange">Crime</span>
                <h4 className="text-xs font-bold text-white">The Hustlers</h4>
                <p className="text-[10px] text-welele-muted line-clamp-2">Soweto hustlers take over Johannesburg gold syndicate.</p>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Sticky Action CTA */}
        <div className="p-4 border-t border-white/10 bg-[#0E0F12]">
          <button
            onClick={() => {
              if (story.episodes.length > 0) {
                onPlayEpisode(story, story.episodes[0]);
                onClose();
              }
            }}
            className="w-full py-3.5 rounded-[7px] bg-gradient-welele hover:opacity-95 text-white font-extrabold text-xs shadow-xl shadow-orange-500/30 flex items-center justify-center gap-2 transition-transform active:scale-95"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Watch Next Episode</span>
          </button>
        </div>
      </div>
    </div>
  );
};
