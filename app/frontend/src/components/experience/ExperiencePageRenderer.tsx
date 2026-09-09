import React, { useState, useEffect } from 'react';
import { ExperienceManifest, ExperienceSection } from '../../types/experience';
import { Story, Episode } from '../../types';
import { experienceApi } from '../../services/api';
import { HeroCarouselSection } from './HeroCarouselSection';
import { HorizontalRowSection } from './HorizontalRowSection';
import { EditorialBannerSection } from './EditorialBannerSection';
import { EditorialSpotlightSection } from './EditorialSpotlightSection';
import { PosterGridSection } from './PosterGridSection';
import { ComingSoonSection } from './ComingSoonSection';

interface ExperiencePageRendererProps {
  pageId: string;
  manifestOverride?: ExperienceManifest | null;
  onOpenPlayer: (story: Story, episode: Episode) => void;
  onOpenStoryDetail: (story: Story) => void;
  onOpenPaymentModal: () => void;
  bookmarks?: Set<string>;
  onToggleBookmark?: (storyId: string) => void;
  highlightedSectionId?: string | null;
  onSectionClick?: (sectionId: string) => void;
}

export const ExperiencePageRenderer: React.FC<ExperiencePageRendererProps> = ({
  pageId,
  manifestOverride,
  onOpenPlayer,
  onOpenStoryDetail,
  onOpenPaymentModal,
  bookmarks = new Set(),
  onToggleBookmark = () => {},
  highlightedSectionId,
  onSectionClick,
}) => {
  const [manifest, setManifest] = useState<ExperienceManifest | null>(manifestOverride || null);
  const [loading, setLoading] = useState<boolean>(!manifestOverride);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (manifestOverride) {
      setManifest(manifestOverride);
      setLoading(false);
      return;
    }

    setLoading(true);
    experienceApi
      .getPageExperience(pageId)
      .then((data) => {
        setManifest(data);
        setError(null);
      })
      .catch((err) => {
        console.warn(`[WEE Surface Renderer] Could not fetch manifest for ${pageId}, using fallback:`, err);
        setError('Failed to load dynamic experience');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [pageId, manifestOverride]);

  if (loading && !manifest) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="w-full aspect-[9/12] sm:aspect-[16/9] rounded-[7px] bg-white/5" />
        <div className="h-6 w-48 bg-white/5 rounded-[7px]" />
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
          {[1, 2, 3, 4, 5].map((n) => (
            <div key={n} className="aspect-[9/14] bg-white/5 rounded-[7px]" />
          ))}
        </div>
      </div>
    );
  }

  if (!manifest || manifest.sections.length === 0) {
    return null;
  }

  // Sort visible sections by order
  const sortedSections = [...manifest.sections]
    .filter((s) => s.is_visible !== false)
    .sort((a, b) => a.order - b.order);

  const renderSectionComponent = (section: ExperienceSection) => {
    switch (section.type) {
      case 'HERO_CAROUSEL':
        return (
          <HeroCarouselSection
            section={section}
            onOpenPlayer={onOpenPlayer}
            onOpenStoryDetail={onOpenStoryDetail}
            bookmarks={bookmarks}
            onToggleBookmark={onToggleBookmark}
          />
        );

      case 'HORIZONTAL_ROW':
        return (
          <HorizontalRowSection
            section={section}
            onOpenPlayer={onOpenPlayer}
            onOpenStoryDetail={onOpenStoryDetail}
          />
        );

      case 'EDITORIAL_BANNER':
        return (
          <EditorialBannerSection
            section={section}
            onOpenPaymentModal={onOpenPaymentModal}
          />
        );

      case 'EDITORIAL_SPOTLIGHT':
        return (
          <EditorialSpotlightSection
            section={section}
            onOpenPlayer={onOpenPlayer}
            onOpenStoryDetail={onOpenStoryDetail}
          />
        );

      case 'POSTER_GRID':
        return (
          <PosterGridSection
            section={section}
            onOpenPlayer={onOpenPlayer}
            onOpenStoryDetail={onOpenStoryDetail}
          />
        );

      case 'COMING_SOON_RADAR':
        return (
          <ComingSoonSection
            section={section}
            onOpenStoryDetail={onOpenStoryDetail}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-8">
      {sortedSections.map((section: ExperienceSection) => {
        const isHighlighted = highlightedSectionId === section.section_id;

        return (
          <div
            key={section.section_id}
            id={`preview-sec-${section.section_id}`}
            onClick={(e) => {
              if (onSectionClick) {
                e.stopPropagation();
                onSectionClick(section.section_id);
              }
            }}
            className={`transition-all duration-300 rounded-[7px] relative ${
              isHighlighted
                ? 'ring-2 ring-welele-orange shadow-[0_0_30px_rgba(255,107,0,0.35)] scale-[1.005]'
                : ''
            }`}
          >
            {renderSectionComponent(section)}
          </div>
        );
      })}
    </div>
  );
};
