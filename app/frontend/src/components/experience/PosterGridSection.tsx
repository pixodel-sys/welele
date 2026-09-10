import React from 'react';
import { ExperienceSection, SlotItem } from '../../types/experience';
import { Story, Episode } from '../../types';
import { Play, Sparkles } from 'lucide-react';

interface PosterGridSectionProps {
  section: ExperienceSection;
  onOpenPlayer: (story: Story, episode: Episode) => void;
  onOpenStoryDetail: (story: Story) => void;
}

export const PosterGridSection: React.FC<PosterGridSectionProps> = ({
  section,
  onOpenPlayer,
  onOpenStoryDetail,
}) => {
  const items = section.items.filter((it) => it.is_active !== false && it.story);
  if (items.length === 0) return null;

  return (
    <div className="space-y-4">
      {(section.title || section.subtitle) && (
        <div className="px-1">
          {section.title && (
            <h3 className="text-lg sm:text-xl font-bold text-white tracking-wide">
              {section.title}
            </h3>
          )}
          {section.subtitle && (
            <p className="text-xs text-welele-muted line-clamp-1">{section.subtitle}</p>
          )}
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 sm:gap-4">
        {items.map((slotItem: SlotItem) => {
          const story: Story = slotItem.story!;
          const headline = slotItem.headline_override || story.title;
          const badge = slotItem.badge;
          const posterArt = slotItem.artwork_overrides?.mobile_9_16 || story.vertical_poster || story.cover_image;

          const handleCardClick = () => {
            if (slotItem.cta_action === 'OPEN_STORY_DETAIL') {
              onOpenStoryDetail(story);
            } else {
              const ep = story.episodes && story.episodes.length > 0 ? story.episodes[0] : ({} as Episode);
              onOpenPlayer(story, ep);
            }
          };

          return (
            <div
              key={slotItem.slot_id}
              onClick={handleCardClick}
              className="cursor-pointer group/card relative transition-transform duration-300 hover:scale-[1.03]"
            >
              <div className="relative aspect-[9/14] rounded-[7px] overflow-hidden bg-welele-surface-2 border border-white/10 shadow-lg">
                <img
                  src={posterArt}
                  alt={headline}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105"
                  loading="lazy"
                />

                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-80 group-hover/card:opacity-90 transition-opacity" />

                {badge && (
                  <div className="absolute top-2 left-2 z-10">
                    <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-black uppercase tracking-wider bg-welele-orange text-black shadow-md">
                      {badge}
                    </span>
                  </div>
                )}

                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover/card:opacity-100 transition-opacity z-10">
                  <div className="w-10 h-10 rounded-[7px] bg-welele-orange text-black flex items-center justify-center shadow-xl">
                    <Play className="w-5 h-5 fill-black ml-0.5" />
                  </div>
                </div>

                <div className="absolute bottom-2 left-2 right-2 z-10">
                  <h4 className="text-xs font-bold text-white line-clamp-1 group-hover/card:text-welele-orange transition-colors">
                    {headline}
                  </h4>
                  <p className="text-[10px] text-welele-muted line-clamp-1">
                    {story.genre?.split('•')[0].trim() || story.genre}
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
