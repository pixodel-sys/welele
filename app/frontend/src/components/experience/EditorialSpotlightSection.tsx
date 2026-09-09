import React from 'react';
import { ExperienceSection, SlotItem } from '../../types/experience';
import { Story, Episode } from '../../types';
import { Play, Sparkles, Star, UserCheck, Flame, Info } from 'lucide-react';

interface EditorialSpotlightSectionProps {
  section: ExperienceSection;
  onOpenPlayer: (story: Story, episode: Episode) => void;
  onOpenStoryDetail: (story: Story) => void;
}

export const EditorialSpotlightSection: React.FC<EditorialSpotlightSectionProps> = ({
  section,
  onOpenPlayer,
  onOpenStoryDetail,
}) => {
  const item: SlotItem | undefined = section.items.find((it) => it.is_active !== false && it.story);
  if (!item || !item.story) return null;

  const story: Story = item.story;
  const headline = item.headline_override || story.title;
  const subheadline = item.subheadline_override || story.synopsis;
  const badge = item.badge || "EDITOR'S SPOTLIGHT";
  const ctaText = item.cta_text || 'Watch Episode 1 Free';
  const bannerArt = item.artwork_overrides?.desktop_16_9 || story.cover_image || story.vertical_poster;

  const handlePlay = () => {
    const ep = story.episodes && story.episodes.length > 0 ? story.episodes[0] : ({} as Episode);
    onOpenPlayer(story, ep);
  };

  return (
    <div className="space-y-2.5">
      {section.title && (
        <div className="flex items-center justify-between px-1">
          <h3 className="text-base sm:text-lg font-bold text-white tracking-wide flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-welele-orange" />
            {section.title}
          </h3>
          {section.subtitle && (
            <span className="text-[11px] text-welele-muted hidden sm:inline">{section.subtitle}</span>
          )}
        </div>
      )}

      <div className="relative overflow-hidden rounded-[7px] bg-welele-surface-2 border border-white/10 shadow-2xl">
        <div className="flex flex-col md:flex-row">
          {/* Visual Artwork Area */}
          <div className="relative w-full md:w-5/12 aspect-[16/10] md:aspect-auto overflow-hidden bg-black">
            <img
              src={bannerArt}
              alt={headline}
              className="w-full h-full object-cover object-center"
            />
            <div className="absolute inset-0 bg-gradient-to-t md:bg-gradient-to-r from-black/80 via-black/20 to-transparent" />
            
            {/* Top Badge */}
            <div className="absolute top-3 left-3 z-10">
              <span className="px-2.5 py-0.5 rounded-[7px] text-[9px] font-black uppercase tracking-wider bg-welele-orange text-black shadow-lg flex items-center gap-1">
                <Star className="w-2.5 h-2.5 fill-black" />
                {badge}
              </span>
            </div>
          </div>

          {/* Editorial Content Area */}
          <div className="flex-1 p-4 sm:p-6 flex flex-col justify-between space-y-3 bg-gradient-to-b from-welele-surface to-welele-surface-2">
            <div className="space-y-2">
              {/* Creator Pill */}
              {story.creator_name && (
                <div className="flex items-center gap-2">
                  {story.creator_avatar ? (
                    <img
                      src={story.creator_avatar}
                      alt={story.creator_name}
                      className="w-5 h-5 rounded-circle object-cover border border-welele-orange/50"
                    />
                  ) : null}
                  <span className="text-[11px] font-semibold text-white/90 truncate">
                    By {story.creator_name}
                  </span>
                  <span className="px-1.5 py-0.2 rounded-[7px] text-[8px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 shrink-0">
                    Verified Director
                  </span>
                </div>
              )}

              <h4 className="text-base sm:text-xl font-black text-[#FFF8F0] tracking-tight font-sans leading-snug break-words">
                {headline}
              </h4>

              <p className="text-xs text-welele-muted leading-relaxed line-clamp-2">
                {subheadline}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-1 pt-0.5">
                {story.tags?.slice(0, 3).map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded-[7px] text-[9px] font-medium bg-white/5 text-white/70 border border-white/5"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={handlePlay}
                className="flex-1 sm:flex-initial px-4 py-2.5 rounded-[7px] bg-gradient-to-r from-welele-orange to-amber-500 hover:from-orange-600 text-black font-extrabold text-xs shadow-lg flex items-center justify-center gap-1.5 transform active:scale-95 transition-all cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 fill-black" />
                <span>{ctaText}</span>
              </button>

              <button
                onClick={() => onOpenStoryDetail(story)}
                className="px-3.5 py-2.5 rounded-[7px] bg-white/10 hover:bg-white/20 border border-white/10 text-white text-xs font-semibold flex items-center justify-center gap-1 transition-all cursor-pointer"
              >
                <Info className="w-3.5 h-3.5" />
                <span>Details</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
