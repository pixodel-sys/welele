import React from 'react';
import { ChevronRight, User, Film, Video, ShieldCheck } from 'lucide-react';

interface EntityHierarchyCrumbProps {
  creatorName?: string;
  creatorVerified?: boolean;
  franchiseCode?: string;
  seriesTitle?: string;
  episodeNumber?: number;
  episodeTitle?: string;
  onNavigateSeries?: () => void;
  onNavigateEpisodes?: () => void;
  className?: string;
}

export const EntityHierarchyCrumb: React.FC<EntityHierarchyCrumbProps> = ({
  creatorName = 'Zola Mthembu',
  creatorVerified = true,
  franchiseCode,
  seriesTitle,
  episodeNumber,
  episodeTitle,
  onNavigateSeries,
  onNavigateEpisodes,
  className = '',
}) => {
  return (
    <nav
      aria-label="IP Spine Lineage"
      className={`flex items-center flex-wrap gap-1.5 text-xs text-welele-muted font-medium py-1.5 px-3 rounded-[6px] bg-black/40 border border-white/5 backdrop-blur-sm ${className}`}
    >
      {/* Creator Tier */}
      <div className="flex items-center gap-1 shrink-0 text-white/80">
        <User className="w-3 h-3 text-welele-orange" />
        <span className="font-semibold">{creatorName}</span>
        {creatorVerified && (
          <span title="KYC Verified Creator" className="flex items-center">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
          </span>
        )}
      </div>

      {/* Franchise Code (if present) */}
      {franchiseCode && (
        <>
          <ChevronRight className="w-3 h-3 text-white/20 shrink-0" />
          <span className="font-mono text-[10px] text-welele-gold/90 bg-welele-gold/10 px-1.5 py-0.2 rounded border border-welele-gold/20 shrink-0">
            {franchiseCode}
          </span>
        </>
      )}

      {/* Series Tier */}
      {seriesTitle && (
        <>
          <ChevronRight className="w-3 h-3 text-white/20 shrink-0" />
          <button
            type="button"
            onClick={onNavigateSeries}
            className={`flex items-center gap-1 font-bold text-white hover:text-welele-orange transition-colors shrink-0 ${
              onNavigateSeries ? 'cursor-pointer hover:underline' : 'cursor-default'
            }`}
          >
            <Film className="w-3 h-3 text-purple-400" />
            <span className="truncate max-w-[140px] sm:max-w-[200px]">{seriesTitle}</span>
          </button>
        </>
      )}

      {/* Episode Tier */}
      {episodeNumber !== undefined && (
        <>
          <ChevronRight className="w-3 h-3 text-white/20 shrink-0" />
          <button
            type="button"
            onClick={onNavigateEpisodes}
            className={`flex items-center gap-1 font-bold text-welele-orange hover:text-orange-300 transition-colors shrink-0 ${
              onNavigateEpisodes ? 'cursor-pointer hover:underline' : 'cursor-default'
            }`}
          >
            <Video className="w-3 h-3 text-welele-orange" />
            <span>Ep #{episodeNumber}</span>
            {episodeTitle && <span className="text-white/60 font-normal truncate max-w-[120px]">({episodeTitle})</span>}
          </button>
        </>
      )}
    </nav>
  );
};
