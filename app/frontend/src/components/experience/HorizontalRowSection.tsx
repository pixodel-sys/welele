import React, { useRef } from 'react';
import { ExperienceSection, SlotItem } from '../../types/experience';
import { Story, Episode } from '../../types';
import { Play, Flame, Star, ChevronLeft, ChevronRight, Lock } from 'lucide-react';

interface HorizontalRowSectionProps {
  section: ExperienceSection;
  onOpenPlayer: (story: Story, episode: Episode) => void;
  onOpenStoryDetail: (story: Story) => void;
}

export const HorizontalRowSection: React.FC<HorizontalRowSectionProps> = ({
  section,
  onOpenPlayer,
  onOpenStoryDetail,
}) => {
  const rowRef = useRef<HTMLDivElement>(null);
  const items = section.items.filter((it) => it.is_active !== false && it.story);

  if (items.length === 0) return null;

  const showRankNumbers = section.config.show_rank_numbers || false;

  const scroll = (direction: 'left' | 'right') => {
    if (rowRef.current) {
      const scrollAmount = direction === 'left' ? -320 : 320;
      rowRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  return (
    <div className="space-y-3 relative group">
      {/* Header */}
      {(section.title || section.subtitle) && (
        <div className="flex items-end justify-between px-1">
          <div>
            {section.title && (
              <h3 className="text-lg sm:text-xl font-bold text-white tracking-wide flex items-center gap-2">
                {section.title}
              </h3>
            )}
            {section.subtitle && (
              <p className="text-xs text-welele-muted line-clamp-1">{section.subtitle}</p>
            )}
          </div>

          {/* Desktop Scroll Arrows */}
          <div className="hidden sm:flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => scroll('left')}
              className="p-1.5 rounded-[7px] bg-welele-surface-2 border border-white/10 text-white/70 hover:text-white hover:bg-welele-surface transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => scroll('right')}
              className="p-1.5 rounded-[7px] bg-welele-surface-2 border border-white/10 text-white/70 hover:text-white hover:bg-welele-surface transition-all"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Scrollable Track */}
      <div
        ref={rowRef}
        className="flex gap-3 overflow-x-auto pb-4 pt-1 scrollbar-none snap-x snap-mandatory"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {items.map((slotItem: SlotItem, index: number) => {
          const story: Story = slotItem.story!;
          const headline = slotItem.headline_override || story.title;
          const badge = slotItem.badge;
          const posterArt = slotItem.artwork_overrides?.mobile_9_16 || story.vertical_poster || story.cover_image;

          const handleItemClick = () => {
            if (slotItem.cta_action === 'OPEN_STORY_DETAIL') {
              onOpenStoryDetail(story);
            } else {
              const ep = story.episodes && story.episodes.length > 0 ? story.episodes[0] : ({} as Episode);
              onOpenPlayer(story, ep);
            }
          };

          return (
            <div
              key={slotItem.slot_id || `${story.id}_${index}`}
              onClick={handleItemClick}
              className="flex-shrink-0 w-32 sm:w-40 md:w-48 snap-start cursor-pointer group/card relative transition-transform duration-300 hover:scale-[1.03]"
            >
              {/* Card Container (9:16 Aspect) */}
              <div className="relative aspect-[9/14] rounded-[7px] overflow-hidden bg-welele-surface-2 border border-white/10 shadow-lg">
                <img
                  src={posterArt}
                  alt={headline}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105"
                  loading="lazy"
                />

                {/* Ambient Shadow & Overlays */}
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-80 group-hover/card:opacity-90 transition-opacity" />

                {/* Top Badge Overlay */}
                {badge && (
                  <div className="absolute top-2 left-2 z-10">
                    <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-black uppercase tracking-wider bg-welele-orange text-black shadow-md">
                      {badge}
                    </span>
                  </div>
                )}

                {/* Big Rank Number (Top 10 Style) */}
                {showRankNumbers && (
                  <div className="absolute -bottom-2 -left-1 z-10 pointer-events-none select-none">
                    <span className="text-5xl sm:text-6xl font-black font-cinematic text-black/80 stroke-white drop-shadow-[0_2px_10px_rgba(255,107,0,0.6)] text-transparent bg-clip-text bg-gradient-to-t from-welele-orange to-amber-300">
                      {index + 1}
                    </span>
                  </div>
                )}

                {/* Free Episodes Pill */}
                {story.free_episodes_count && (
                  <div className="absolute top-2 right-2 z-10">
                    <span className="px-1.5 py-0.5 rounded-[7px] text-[8px] font-bold bg-black/60 backdrop-blur-md text-emerald-400 border border-emerald-500/30">
                      {story.free_episodes_count} Free
                    </span>
                  </div>
                )}

                {/* Play Hover Trigger */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover/card:opacity-100 transition-opacity z-10">
                  <div className="w-10 h-10 rounded-[7px] bg-welele-orange text-black flex items-center justify-center shadow-xl transform scale-75 group-hover/card:scale-100 transition-transform">
                    <Play className="w-5 h-5 fill-black ml-0.5" />
                  </div>
                </div>

                {/* Bottom Metadata */}
                <div className="absolute bottom-2 left-2 right-2 z-10">
                  <h4 className="text-xs sm:text-sm font-bold text-white line-clamp-1 group-hover/card:text-welele-orange transition-colors">
                    {headline}
                  </h4>
                  <p className="text-[10px] text-welele-muted line-clamp-1">
                    {story.episodes?.length || story.total_episodes || 0} Eps • {story.genre?.split('•')[0].trim() || story.genre}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
