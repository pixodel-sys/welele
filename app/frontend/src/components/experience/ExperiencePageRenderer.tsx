import React, { useState, useEffect, useMemo } from 'react';
import { ExperienceManifest, ExperienceSection } from '../../types/experience';
import { Story, Episode } from '../../types';
import { experienceApi } from '../../services/api';
import { useApp } from '../../context/AppContext';
import { getDefaultExperienceManifest, hydrateManifest } from '../../utils/experienceFallback';
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
  const { stories } = useApp();

  // Instant fallback manifest ready on first frame
  const fallbackManifest = useMemo(
    () => getDefaultExperienceManifest(pageId, stories),
    [pageId, stories]
  );

  const [manifest, setManifest] = useState<ExperienceManifest>(() => {
    if (manifestOverride) {
      return hydrateManifest(manifestOverride, stories);
    }
    return fallbackManifest;
  });

  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (manifestOverride) {
      setManifest(hydrateManifest(manifestOverride, stories));
      return;
    }

    let isMounted = true;

    experienceApi
      .getPageExperience(pageId)
      .then((data) => {
        if (!isMounted) return;
        if (data && Array.isArray(data.sections) && data.sections.length > 0) {
          setManifest(hydrateManifest(data, stories));
        } else {
          setManifest(fallbackManifest);
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        console.warn(`[WEE Surface Renderer] Network/backend unavailable for ${pageId}, using canonical manifest:`, err);
        setManifest(fallbackManifest);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [pageId, manifestOverride, stories, fallbackManifest]);

  if (!manifest || !manifest.sections || manifest.sections.length === 0) {
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
