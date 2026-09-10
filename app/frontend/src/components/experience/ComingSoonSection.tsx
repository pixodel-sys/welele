import React, { useState } from 'react';
import { ExperienceSection, SlotItem } from '../../types/experience';
import { Story } from '../../types';
import { Bell, BellCheck, Calendar, Clock, Play } from 'lucide-react';

interface ComingSoonSectionProps {
  section: ExperienceSection;
  onOpenStoryDetail: (story: Story) => void;
}

export const ComingSoonSection: React.FC<ComingSoonSectionProps> = ({
  section,
  onOpenStoryDetail,
}) => {
  const items = section.items.filter((it) => it.is_active !== false && it.story);
  const [remindedSlots, setRemindedSlots] = useState<Set<string>>(new Set());

  if (items.length === 0) return null;

  const toggleReminder = (e: React.MouseEvent, slotId: string) => {
    e.stopPropagation();
    setRemindedSlots((prev) => {
      const next = new Set(prev);
      if (next.has(slotId)) {
        next.delete(slotId);
      } else {
        next.add(slotId);
      }
      return next;
    });
  };

  return (
    <div className="space-y-4">
      {(section.title || section.subtitle) && (
        <div className="px-1">
          {section.title && (
            <h3 className="text-lg sm:text-xl font-bold text-white tracking-wide flex items-center gap-2">
              <Calendar className="w-4 h-4 text-welele-orange" />
              {section.title}
            </h3>
          )}
          {section.subtitle && (
            <p className="text-xs text-welele-muted line-clamp-1">{section.subtitle}</p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {items.map((slotItem: SlotItem) => {
          const story: Story = slotItem.story!;
          const headline = slotItem.headline_override || story.title;
          const isReminded = remindedSlots.has(slotItem.slot_id);
          const bannerArt = slotItem.artwork_overrides?.desktop_16_9 || story.cover_image || story.vertical_poster;

          return (
            <div
              key={slotItem.slot_id}
              onClick={() => onOpenStoryDetail(story)}
              className="relative overflow-hidden rounded-[7px] bg-welele-surface-2 border border-white/10 shadow-lg cursor-pointer group hover:border-welele-orange/50 transition-all p-4 flex gap-4 items-center"
            >
              {/* Thumbnail */}
              <div className="relative w-24 sm:w-28 aspect-[9/14] rounded-[7px] overflow-hidden flex-shrink-0 bg-black">
                <img
                  src={story.vertical_poster || bannerArt}
                  alt={headline}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                />
                <div className="absolute top-1.5 left-1.5">
                  <span className="px-1.5 py-0.5 rounded-[7px] text-[8px] font-bold bg-black/70 text-welele-orange border border-welele-orange/30">
                    COMING SOON
                  </span>
                </div>
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0 space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-welele-orange font-bold flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Dropping Friday
                  </span>
                  {story.language && (
                    <span className="text-[10px] text-welele-muted">• {story.language}</span>
                  )}
                </div>

                <h4 className="text-sm sm:text-base font-bold text-white group-hover:text-welele-orange transition-colors truncate">
                  {headline}
                </h4>

                <p className="text-xs text-welele-muted line-clamp-2 leading-relaxed">
                  {story.synopsis}
                </p>

                {/* Reminder Button */}
                <div className="pt-2">
                  <button
                    onClick={(e) => toggleReminder(e, slotItem.slot_id)}
                    className={`px-3 py-1.5 rounded-[7px] text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                      isReminded
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-white/10 text-white hover:bg-white/20 border border-white/10'
                    }`}
                  >
                    {isReminded ? (
                      <>
                        <BellCheck className="w-3.5 h-3.5" />
                        Reminder Set
                      </>
                    ) : (
                      <>
                        <Bell className="w-3.5 h-3.5" />
                        Remind Me
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
