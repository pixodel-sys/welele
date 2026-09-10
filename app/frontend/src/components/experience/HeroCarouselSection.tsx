import React, { useState, useEffect, useRef } from 'react';
import { ExperienceSection, SlotItem } from '../../types/experience';
import { Story, Episode } from '../../types';
import {
  Play,
  Flame,
  Star,
  Sparkles,
  Volume2,
  VolumeX,
  ChevronLeft,
  ChevronRight,
  Plus,
  Check,
  Info,
  Eye,
} from 'lucide-react';

interface HeroCarouselSectionProps {
  section: ExperienceSection;
  onOpenPlayer: (story: Story, episode: Episode) => void;
  onOpenStoryDetail: (story: Story) => void;
  bookmarks: Set<string>;
  onToggleBookmark: (storyId: string) => void;
}

export const HeroCarouselSection: React.FC<HeroCarouselSectionProps> = ({
  section,
  onOpenPlayer,
  onOpenStoryDetail,
  bookmarks,
  onToggleBookmark,
}) => {
  const items = section.items.filter((it) => it.is_active !== false && it.story);
  const [activeIndex, setActiveIndex] = useState<number>(0);
  const [isHovered, setIsHovered] = useState<boolean>(false);
  const [isVideoMuted, setIsVideoMuted] = useState<boolean>(true);
  const [showVideoTeaser, setShowVideoTeaser] = useState<boolean>(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const autoPlaySeconds = section.config.auto_play_seconds || 8;

  // Auto-advance
  useEffect(() => {
    if (items.length <= 1 || isHovered) return;
    const timer = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % items.length);
      setShowVideoTeaser(false);
    }, autoPlaySeconds * 1000);
    return () => clearInterval(timer);
  }, [items.length, isHovered, autoPlaySeconds]);

  if (items.length === 0) return null;

  const currentSlot: SlotItem = items[activeIndex] || items[0];
  const story: Story = currentSlot.story!;
  const isBookmarked = bookmarks.has(story.id);

  // Exact Title & Description
  const title = currentSlot.headline_override || story.title;
  const synopsis = currentSlot.subheadline_override || story.synopsis || story.tagline;
  const badgeText = currentSlot.badge || (story.is_original ? 'SPOTLIGHT ORIGINAL' : 'TOP RATED #1');
  const ctaText = currentSlot.cta_text || 'Watch Now';

  // Artwork
  const heroArtwork = currentSlot.artwork_overrides?.mobile_9_16 || story.cover_image || story.vertical_poster;
  const desktopArtwork = currentSlot.artwork_overrides?.desktop_16_9 || story.cover_image || story.vertical_poster;
  const trailerVideo = currentSlot.artwork_overrides?.trailer_video_url;

  const handleNext = () => {
    setActiveIndex((prev) => (prev + 1) % items.length);
    setShowVideoTeaser(false);
  };

  const handlePrev = () => {
    setActiveIndex((prev) => (prev - 1 + items.length) % items.length);
    setShowVideoTeaser(false);
  };

  const handlePlayClick = () => {
    const ep = story.episodes && story.episodes.length > 0 ? story.episodes[0] : ({} as Episode);
    onOpenPlayer(story, ep);
  };

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="relative rounded-[7px] overflow-hidden shadow-2xl border border-white/10 group transition-all"
    >
      {/* Cinematic Visual Stage */}
      <div className="aspect-[4/5] sm:aspect-[16/8] md:aspect-[21/9] max-h-[540px] w-full relative overflow-hidden bg-black">
        {/* Slides Layer */}
        {items.map((slotItem, idx) => {
          const s = slotItem.story!;
          const isActive = idx === activeIndex;
          const art = slotItem.artwork_overrides?.desktop_16_9 || s.cover_image || s.vertical_poster;

          return (
            <div
              key={slotItem.slot_id || s.id}
              className={`absolute inset-0 transition-opacity duration-1000 ease-in-out ${
                isActive ? 'opacity-100 pointer-events-auto z-0' : 'opacity-0 pointer-events-none z-[-1]'
              }`}
            >
              {trailerVideo && showVideoTeaser && isActive ? (
                <video
                  ref={videoRef}
                  src={trailerVideo}
                  autoPlay
                  loop
                  muted={isVideoMuted}
                  playsInline
                  className="w-full h-full object-cover animate-fade-in"
                />
              ) : (
                <img
                  src={art}
                  alt={s.title}
                  onError={(e) => {
                    const fallback = s.cover_image || s.vertical_poster || '/banners/blood_ties_banner.jpg';
                    if (e.currentTarget.src !== fallback) {
                      e.currentTarget.src = fallback;
                    }
                  }}
                  className={`w-full h-full object-cover object-[center_28%] filter brightness-95 transform-gpu ${
                    isActive ? 'animate-ken-burns' : ''
                  }`}
                />
              )}
            </div>
          );
        })}

        {/* Cinematic Gradient Overlays for Readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#0B0C0E] via-[#0B0C0E]/50 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#0B0C0E]/90 via-[#0B0C0E]/40 to-transparent" />

        {/* Ambient Glow */}
        <div className="absolute top-1/4 left-1/4 w-44 h-44 bg-orange-600/20 rounded-[7px] blur-3xl pointer-events-none" />

        {/* Top-Right Progress Indicator Pills & Arrows */}
        <div className="absolute top-4 right-4 sm:top-6 sm:right-6 flex items-center gap-2 z-20">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-[7px] bg-black/45 backdrop-blur-md border border-white/10">
            {items.map((it, idx) => (
              <button
                key={it.slot_id || idx}
                onClick={() => {
                  setActiveIndex(idx);
                  setShowVideoTeaser(false);
                }}
                aria-label={`Jump to slide ${idx + 1}`}
                className={`h-1.5 rounded-[7px] transition-all duration-500 ${
                  idx === activeIndex
                    ? 'w-6 bg-gradient-welele shadow-sm shadow-orange-500/50'
                    : 'w-1.5 bg-white/30 hover:bg-white/60'
                }`}
              />
            ))}
          </div>

          <div className="hidden sm:flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <button
              onClick={handlePrev}
              aria-label="Previous story"
              className="w-7 h-7 rounded-[7px] bg-black/50 hover:bg-black/80 text-white/80 hover:text-white border border-white/10 flex items-center justify-center transition-colors backdrop-blur-md cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={handleNext}
              aria-label="Next story"
              className="w-7 h-7 rounded-[7px] bg-black/50 hover:bg-black/80 text-white/80 hover:text-white border border-white/10 flex items-center justify-center transition-colors backdrop-blur-md cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Active Hero Dynamic Content Info & Actions */}
        <div
          key={story.id}
          className="absolute bottom-4 left-4 right-4 sm:bottom-8 sm:left-8 max-w-xl z-10 animate-hero-content"
        >
          {/* Top Badges */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-[7px] text-[10px] font-black bg-gradient-welele text-white shadow-lg tracking-wider flex items-center gap-1">
              <Flame className="w-3 h-3 fill-white" />
              {badgeText}
            </span>
            <span className="text-[11px] font-bold text-welele-orange flex items-center gap-1 bg-black/40 px-2 py-0.5 rounded-[7px] backdrop-blur-md border border-white/5">
              <Star className="w-3.5 h-3.5 fill-current text-welele-gold" /> {story.rating || 4.98}
            </span>
            <span className="text-[10px] text-white/70 font-semibold hidden sm:inline-flex items-center gap-1 bg-white/5 px-2 py-0.5 rounded-[7px]">
              <Eye className="w-3 h-3 text-welele-orange" /> {((story.total_views || 3800000) / 1000000).toFixed(1)}M Views
            </span>
          </div>

          {/* Actual Series Title */}
          <h1 className="text-2xl sm:text-5xl font-black text-[#FFF8F0] tracking-tight uppercase font-sans leading-none drop-shadow-xl">
            {title}
          </h1>

          {/* Metadata Subtitle */}
          <div className="flex items-center gap-2 text-xs font-semibold text-welele-muted mt-2">
            <span>{story.genre || 'Drama'}</span>
            <span>•</span>
            <span>
              {story.episodes?.length || story.total_episodes || 1}{' '}
              {(story.episodes?.length || story.total_episodes || 1) === 1 ? 'Episode' : 'Episodes'}
            </span>
            <span>•</span>
            <span className="text-white/80">{story.language?.split('/')[0].trim() || 'isiZulu'}</span>
          </div>

          {/* Full Rich Story Synopsis / Description */}
          <p className="text-xs text-white/80 line-clamp-2 mt-2 hidden sm:block max-w-lg leading-relaxed">
            {synopsis}
          </p>

          {/* Action CTAs */}
          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={handlePlayClick}
              className="px-6 py-3 rounded-[7px] bg-gradient-welele hover:opacity-95 text-white font-extrabold text-xs shadow-xl shadow-orange-500/30 flex items-center gap-2 transition-transform active:scale-95 cursor-pointer"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{ctaText}</span>
            </button>

            <button
              onClick={() => onToggleBookmark(story.id)}
              className={`px-4 py-3 rounded-[7px] backdrop-blur-md text-white font-bold text-xs border border-white/15 flex items-center gap-1.5 transition-colors cursor-pointer ${
                isBookmarked
                  ? 'bg-orange-500/20 border-orange-500 text-welele-orange shadow-lg shadow-orange-500/20'
                  : 'bg-white/10 hover:bg-white/20'
              }`}
            >
              {isBookmarked ? <Check className="w-4 h-4 text-emerald-400" /> : <Plus className="w-4 h-4" />}
              <span>{isBookmarked ? 'In List' : 'My List'}</span>
            </button>

            <button
              onClick={() => onOpenStoryDetail(story)}
              className="px-3.5 py-3 rounded-[7px] bg-welele-surface-2 hover:bg-welele-surface-3 text-white/80 hover:text-white font-bold text-xs border border-white/10 flex items-center transition-colors cursor-pointer"
              aria-label="Story details"
            >
              <Info className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Interactive Spotlight Thumbnail Rail: Title Selection Changes the Hero */}
      <div className="bg-[#121317] border-t border-white/10 px-3 sm:px-4 py-2.5 sm:py-3 flex items-center gap-2 sm:gap-3 w-full">
        <span className="text-[10px] uppercase font-black tracking-widest text-welele-muted shrink-0 flex items-center gap-1 pr-1">
          <Sparkles className="w-3 h-3 text-welele-orange" />
          <span className="hidden sm:inline">FEATURED:</span>
        </span>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 sm:gap-2.5 w-full flex-1">
          {items.slice(0, 5).map((slotItem, idx) => {
            const s = slotItem.story!;
            const isCurrent = idx === activeIndex;
            return (
              <button
                key={slotItem.slot_id || s.id}
                onClick={() => {
                  setActiveIndex(idx);
                  setShowVideoTeaser(false);
                }}
                className={`group/btn flex items-center gap-2 sm:gap-2.5 px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-[7px] border text-left transition-all w-full min-w-0 cursor-pointer ${
                  idx >= 2 ? 'hidden md:flex' : 'flex'
                } ${
                  isCurrent
                    ? 'bg-welele-surface-3 border-welele-orange text-white shadow-md shadow-orange-500/10'
                    : 'bg-welele-surface-2/70 border-white/5 text-welele-muted hover:text-white hover:border-white/20'
                }`}
              >
                <div className="w-7 sm:w-8 h-9 sm:h-10 rounded-[7px] overflow-hidden bg-black shrink-0 relative">
                  <img
                    src={s.vertical_poster || s.cover_image}
                    alt={s.title}
                    onError={(e) => {
                      const fallback = s.cover_image || s.vertical_poster || '/posters/blood_ties.jpg';
                      if (e.currentTarget.src !== fallback) {
                        e.currentTarget.src = fallback;
                      }
                    }}
                    className="w-full h-full object-cover group-hover/btn:scale-105 transition-transform"
                  />
                  {isCurrent && (
                    <div className="absolute inset-0 bg-orange-500/20 border border-orange-400/60 rounded-[7px]" />
                  )}
                </div>
                <div className="min-w-0 flex-1 pr-0.5">
                  <span className="text-xs font-bold block truncate">
                    {s.title}
                  </span>
                  <span className="text-[9px] sm:text-[10px] text-welele-muted block truncate mt-0.5">
                    ★ {s.rating} • {s.genre?.split('•')[0].trim() || 'Drama'}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
