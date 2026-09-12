import React, { useState, useEffect, useRef } from 'react';
import { Story, Episode } from '../../types';
import { creatorApi } from '../../services/api';
import { mediaStore } from '../../services/mediaStore';
import { EntityHierarchyCrumb } from '../common/patterns/EntityHierarchyCrumb';
import { ProvenanceBadge } from '../common/patterns/ProvenanceBadge';
import { ReadinessBadge } from '../common/patterns/ReadinessBadge';
import { StatusBadge } from '../common/patterns/StatusBadge';
import {
  ArrowLeft,
  PlusCircle,
  Video,
  Coins,
  CheckCircle2,
  Clock,
  AlertTriangle,
  BookOpen,
  BarChart3,
  UploadCloud,
  Image as ImageIcon,
  Check,
  ShieldCheck,
  UserCheck,
  Sparkles,
  FileText
} from 'lucide-react';

interface SeriesCommandRoomProps {
  seriesId: string;
  onBack: () => void;
  onOpenEpisodePipeline: (seriesId: string, episodeNum?: number) => void;
}

type ShowTab = 'episodes' | 'story' | 'insights' | 'earnings';

export const SeriesCommandRoom: React.FC<SeriesCommandRoomProps> = ({
  seriesId,
  onBack,
  onOpenEpisodePipeline,
}) => {
  const [activeTab, setActiveTab] = useState<ShowTab>('episodes');
  const [workspaceData, setWorkspaceData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [customPoster, setCustomPoster] = useState<string | null>(null);
  const [customBanner, setCustomBanner] = useState<string | null>(null);

  const posterInputRef = useRef<HTMLInputElement | null>(null);
  const bannerInputRef = useRef<HTMLInputElement | null>(null);

  const fetchWorkspace = () => {
    creatorApi
      .getSeriesWorkspace(seriesId)
      .then((res) => {
        setWorkspaceData(res);
      })
      .catch((err) => {
        console.error('Failed to load show workspace:', err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchWorkspace();
  }, [seriesId]);

  const handleUpdatePoster = async (file: File) => {
    const key = `series_poster_${seriesId}`;
    const url = await mediaStore.saveMedia(key, file);
    setCustomPoster(url);
  };

  const handleUpdateBanner = async (file: File) => {
    const key = `series_banner_${seriesId}`;
    const url = await mediaStore.saveMedia(key, file);
    setCustomBanner(url);
  };

  if (loading || !workspaceData) {
    return (
      <div className="py-20 text-center text-welele-muted">
        <div className="w-8 h-8 border-2 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <span>Loading Show...</span>
      </div>
    );
  }

  const series: Story = workspaceData.series;
  const metrics = workspaceData.metrics;
  const episodes: Episode[] = series.episodes || [];
  const displayPoster = customPoster || series.vertical_poster;
  const displayBanner = customBanner || series.cover_image || series.vertical_poster;
  const franchiseCode = series.franchise_code || `IP-WEL-${series.id.replace(/[^a-zA-Z0-9]/g, '').slice(-4).toUpperCase()}`;

  const getEpisodeReadiness = (ep: Episode): 'READY' | 'READY_WITH_WARNINGS' | 'NEEDS_INPUT' | 'BLOCKED' => {
    if (ep.status === 'published' || ep.status === 'approved') return 'READY';
    if (ep.status === 'under_review' || ep.status === 'submitted') return 'READY_WITH_WARNINGS';
    if (ep.status === 'changes_requested') return 'NEEDS_INPUT';
    if (!ep.video_url || !ep.cliffhanger_hook) return 'NEEDS_INPUT';
    return 'READY';
  };

  const getModerationBadge = (status?: string) => {
    switch (status) {
      case 'published':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-max">
            <CheckCircle2 className="w-3 h-3" /> Published
          </span>
        );
      case 'approved':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-teal-500/20 text-teal-400 border border-teal-500/30 flex items-center gap-1 w-max">
            <Check className="w-3 h-3" /> Approved
          </span>
        );
      case 'under_review':
      case 'submitted':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-max">
            <Clock className="w-3 h-3" /> Under Review
          </span>
        );
      case 'changes_requested':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-orange-500/20 text-orange-400 border border-orange-500/30 flex items-center gap-1 w-max">
            <AlertTriangle className="w-3 h-3" /> Changes Needed
          </span>
        );
      case 'draft':
      default:
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-white/10 text-white/70 border border-white/10 flex items-center gap-1 w-max">
            Draft
          </span>
        );
    }
  };

  const getCommercialBadge = (ep: Episode) => {
    if (ep.is_free) {
      return (
        <div className="flex flex-col">
          <span className="text-emerald-400 font-bold text-[11px] flex items-center gap-1">
            Free Episode
          </span>
          <span className="text-[9px] text-welele-muted">Public Access</span>
        </div>
      );
    }
    return (
      <div className="flex flex-col">
        <span className="text-amber-400 font-bold text-[11px] flex items-center gap-1">
          <Coins className="w-3 h-3" /> Locked • {ep.coin_price || 5} Coins
        </span>
        <span className="text-[9px] text-emerald-400/80 font-medium">Airtime Enabled (R3.00)</span>
      </div>
    );
  };

  return (
    <div className="space-y-6 pb-24 max-w-7xl mx-auto animate-fade-in text-white">
      {/* Canonical Entity Hierarchy Crumb */}
      <div className="p-2.5 rounded-[7px] bg-[#101116] border border-white/5">
        <EntityHierarchyCrumb
          franchiseCode={franchiseCode}
          seriesTitle={series.title}
          onNavigateSeries={onBack}
        />
      </div>

      {/* Show Top Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="w-9 h-9 rounded-[7px] bg-white/5 hover:bg-white/10 flex items-center justify-center text-white border border-white/10 transition-all cursor-pointer"
            aria-label="Back to My Shows"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2 py-0.5 rounded-[7px] bg-black/60 border border-white/15 text-welele-gold font-mono text-[10px] font-bold">
                {franchiseCode}
              </span>
              <h1 className="text-xl sm:text-2xl font-black text-white uppercase tracking-tight font-cinematic">
                {series.title}
              </h1>
              <span className="px-2 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Live
              </span>
            </div>
            <p className="text-xs text-welele-muted mt-0.5">
              {series.genre} • {episodes.length} Episodes {metrics?.under_review_count ? `(${metrics.under_review_count} In Review)` : ''} • {series.language}
            </p>
          </div>
        </div>

        {/* Hero CTA */}
        <div className="flex items-center gap-2.5 self-end sm:self-center">
          <button
            onClick={() => onOpenEpisodePipeline(series.id, episodes.length + 1)}
            className="px-5 py-2.5 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-bold text-xs shadow-lg shadow-pink-500/20 flex items-center gap-2 hover:opacity-95 transition-all cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Add Episode</span>
          </button>
        </div>
      </div>

      {/* Show Workspace Context Navigation */}
      <div className="border-b border-white/10 flex items-center gap-2 overflow-x-auto pb-1">
        {[
          { id: 'episodes', label: `Episodes (${episodes.length})`, icon: Video },
          { id: 'story', label: 'Story & Artwork', icon: BookOpen },
          { id: 'insights', label: 'Insights', icon: BarChart3 },
          { id: 'earnings', label: 'Earnings', icon: Coins },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as ShowTab)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-[7px] text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'bg-pink-500/20 text-white border border-pink-500/40 shadow-sm'
                  : 'text-welele-muted hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-[#FF2A6D]' : 'text-welele-muted'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT: EPISODES */}
      {activeTab === 'episodes' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Episodes Roster ({episodes.length})
              </h3>
              {metrics?.under_review_count > 0 && (
                <span className="px-2 py-0.5 rounded-[7px] bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-bold">
                  {metrics.under_review_count} Under Review
                </span>
              )}
            </div>
            <button
              onClick={() => onOpenEpisodePipeline(series.id, episodes.length + 1)}
              className="text-xs text-pink-400 hover:text-pink-300 font-bold flex items-center gap-1 cursor-pointer"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Add Episode {episodes.length + 1}</span>
            </button>
          </div>

          <div className="rounded-[7px] border border-white/10 bg-[#121318] overflow-hidden">
            <table className="w-full text-left text-xs text-white">
              <thead className="bg-[#181920] text-welele-muted uppercase font-mono text-[10px] border-b border-white/5">
                <tr>
                  <th className="px-4 py-3">#</th>
                  <th className="px-4 py-3">Episode</th>
                  <th className="px-4 py-3">Readiness</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Commercial Policy</th>
                  <th className="px-4 py-3">Moderation State</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {episodes.map((ep, idx) => {
                  const epNum = ep.episode_number || idx + 1;
                  const formattedNum = epNum < 10 ? `0${epNum}` : `${epNum}`;
                  const epReadiness = getEpisodeReadiness(ep);
                  return (
                    <tr key={ep.id} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3.5 font-mono font-bold text-welele-gold text-xs">
                        EP {formattedNum}
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="font-bold text-white text-xs">{ep.title}</div>
                        <div className="text-[11px] text-welele-muted line-clamp-1 mt-0.5">
                          {ep.cliffhanger_hook || ep.synopsis}
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <ReadinessBadge level={epReadiness} size="sm" />
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-welele-muted text-xs">
                            {ep.duration_seconds || 65}s
                          </span>
                          <ProvenanceBadge tier="MEDIA_OBSERVED" size="sm" />
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        {getCommercialBadge(ep)}
                      </td>
                      <td className="px-4 py-3.5">
                        {getModerationBadge(ep.status)}
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <button
                          onClick={() => onOpenEpisodePipeline(series.id, epNum)}
                          className="px-2.5 py-1 rounded-[7px] bg-white/5 hover:bg-white/10 text-white/80 hover:text-white text-[11px] font-semibold border border-white/10 cursor-pointer"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB CONTENT: STORY & ARTWORK */}
      {activeTab === 'story' && (
        <div className="space-y-6">
          {/* Show Premise & Provenance Card */}
          <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-pink-400" />
                Story World & Franchise Premise
              </h3>
              <ProvenanceBadge tier="CREATOR_DECLARED" size="sm" />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-welele-muted font-bold block">Series Synopsis</label>
              <p className="text-xs text-white leading-relaxed p-3 rounded-[7px] bg-black/40 border border-white/10">
                "{series.synopsis || series.tagline}"
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-welele-muted font-bold block">Available Languages & Dialects</label>
              <div className="flex flex-wrap gap-2">
                {series.available_languages?.map((lang) => (
                  <span
                    key={lang}
                    className="px-2.5 py-1 rounded-[7px] bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-medium"
                  >
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Character Roster Deck */}
          <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-emerald-400" />
                Character Roster & Digital IP Bibles
              </h3>
              <span className="text-[10px] text-welele-muted font-mono">
                {series.characters?.length || 3} Registered IP Characters
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {(series.characters || [
                {
                  id: 'c_lead',
                  name: 'Protagonist Lead',
                  role: 'protagonist',
                  archetype: 'The Rightful Heir',
                  secret_motivation: 'Reclaim the family empire without shedding innocent blood.',
                  signature_quote: 'Power is not given in Sandton; it is taken with courage.'
                },
                {
                  id: 'c_antag',
                  name: 'Corporate Rival',
                  role: 'antagonist',
                  archetype: 'The Ruthless Board Leader',
                  secret_motivation: 'Maintain absolute monopoly over the taxi and transit routes.',
                  signature_quote: 'Contracts are written in ink, but enforced in iron.'
                },
                {
                  id: 'c_ally',
                  name: 'Elder Confidant',
                  role: 'confidant',
                  archetype: 'The Keeper of Secrets',
                  secret_motivation: 'Prevent an all-out turf war before the next election cycle.',
                  signature_quote: 'The engine that runs loudest burns out first.'
                }
              ]).map((char: any, i: number) => (
                <div key={char.id || i} className="p-4 rounded-[7px] bg-black/40 border border-white/10 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      {char.role || 'Character'}
                    </span>
                    <span className="text-[10px] text-welele-muted font-mono">{char.archetype}</span>
                  </div>
                  <h4 className="text-sm font-bold text-white">{char.name}</h4>
                  <p className="text-[11px] text-welele-muted leading-relaxed">
                    {char.secret_motivation}
                  </p>
                  <p className="text-[10px] text-welele-gold italic pt-1 border-t border-white/5">
                    "{char.signature_quote}"
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Commercial Rights Declarations & Story Lineage */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Rights Declaration */}
            <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Commercial Rights Declarations
                </h3>
                <ProvenanceBadge tier="CREATOR_DECLARED" size="sm" />
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-white/5">
                  <span className="text-welele-muted">Digital Video On Demand:</span>
                  <span className="text-white font-semibold">Worldwide Exclusive</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-white/5">
                  <span className="text-welele-muted">Original IP Ownership:</span>
                  <span className="text-emerald-400 font-semibold">100% Creator Owned</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-white/5">
                  <span className="text-welele-muted">Linear & Broadcast Sync:</span>
                  <span className="text-white font-semibold">Retained by Showrunner</span>
                </div>
              </div>
            </div>

            {/* Story Lineage */}
            <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-pink-400" />
                  Narrative Lineage & Origin
                </h3>
                <ProvenanceBadge tier="AI_ASSIST" size="sm" />
              </div>
              <div className="space-y-2 text-xs">
                <div className="p-2.5 rounded-[7px] bg-black/40 border border-white/5 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-welele-muted">Source Engine:</span>
                    <span className="text-white font-mono font-bold">Story Forge™ AI v2</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-welele-muted">Human Verification:</span>
                    <span className="text-emerald-400 font-bold">Confirmed by Showrunner</span>
                  </div>
                </div>
                <p className="text-[11px] text-welele-muted leading-relaxed">
                  Narrative hooks and character bibles were originated with Story Forge assistance and accepted into the canonical franchise spine.
                </p>
              </div>
            </div>
          </div>

          {/* Show Artwork Controls */}
          <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-welele-gold" />
                Show Artwork & Key Art
              </h3>
              <ProvenanceBadge tier="MEDIA_OBSERVED" size="sm" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Vertical Poster Box */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">9:16 Vertical Poster</span>
                  <button
                    type="button"
                    onClick={() => posterInputRef.current?.click()}
                    className="text-xs text-pink-400 hover:text-pink-300 font-bold cursor-pointer"
                  >
                    Replace Poster
                  </button>
                  <input
                    type="file"
                    ref={posterInputRef}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleUpdatePoster(e.target.files[0]);
                      }
                    }}
                    accept="image/*"
                    className="hidden"
                  />
                </div>

                <div className="w-36 aspect-[9/16] rounded-[7px] overflow-hidden border border-white/20 bg-black relative shadow-lg">
                  <img src={displayPoster} alt="Poster" className="w-full h-full object-cover" />
                </div>
              </div>

              {/* Horizontal Banner Box */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">16:9 Hero Banner</span>
                  <button
                    type="button"
                    onClick={() => bannerInputRef.current?.click()}
                    className="text-xs text-welele-gold hover:text-yellow-300 font-bold cursor-pointer"
                  >
                    Replace Banner
                  </button>
                  <input
                    type="file"
                    ref={bannerInputRef}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleUpdateBanner(e.target.files[0]);
                      }
                    }}
                    accept="image/*"
                    className="hidden"
                  />
                </div>

                <div className="w-full aspect-video rounded-[7px] overflow-hidden border border-white/20 bg-black relative shadow-lg">
                  <img src={displayBanner} alt="Hero Banner" className="w-full h-full object-cover" />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: INSIGHTS */}
      {activeTab === 'insights' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
              <span className="text-xs text-welele-muted">Average Completion Rate</span>
              <div className="text-2xl font-black text-emerald-400 font-cinematic">
                {metrics?.completion_rate || '89.1%'}
              </div>
              <span className="text-[10px] text-welele-muted">Strong audience retention</span>
            </div>

            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
              <span className="text-xs text-welele-muted">Total Views</span>
              <div className="text-2xl font-black text-white font-cinematic">
                {metrics?.total_views?.toLocaleString() || '1.2M'}
              </div>
              <span className="text-[10px] text-welele-muted">Across all episodes</span>
            </div>

            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
              <span className="text-xs text-welele-muted">Audience Momentum</span>
              <div className="text-2xl font-black text-[#FF2A6D] font-cinematic">+34%</div>
              <span className="text-[10px] text-emerald-400 font-bold">Trending this week</span>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: EARNINGS */}
      {activeTab === 'earnings' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
              <span className="text-xs text-welele-muted">Total Episode Unlocks</span>
              <div className="text-2xl font-black text-welele-gold font-cinematic">
                142,500 🪙
              </div>
              <p className="text-[11px] text-welele-muted">From paid coin & airtime unlocks</p>
            </div>

            <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
              <span className="text-xs text-welele-muted">Creator Payout Balance</span>
              <div className="text-2xl font-black text-emerald-400 font-cinematic">
                R{((metrics?.estimated_earnings_usd || 780) * 18.5).toFixed(2)}
              </div>
              <p className="text-[11px] text-welele-muted">Available for next settlement cycle</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
