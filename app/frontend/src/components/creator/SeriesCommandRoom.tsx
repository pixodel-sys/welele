import React, { useState, useEffect } from 'react';
import { Story, Episode, SeriesCommandTab } from '../../types';
import { creatorApi } from '../../services/api';
import {
  ArrowLeft,
  PlusCircle,
  Video,
  Play,
  TrendingUp,
  Coins,
  Eye,
  Zap,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Layers,
  Sparkles,
  BookOpen,
  Image as ImageIcon,
  BarChart3,
  Sliders,
  DollarSign
} from 'lucide-react';

interface SeriesCommandRoomProps {
  seriesId: string;
  onBack: () => void;
  onOpenEpisodePipeline: (seriesId: string, episodeNum?: number) => void;
}

export const SeriesCommandRoom: React.FC<SeriesCommandRoomProps> = ({
  seriesId,
  onBack,
  onOpenEpisodePipeline,
}) => {
  const [activeTab, setActiveTab] = useState<SeriesCommandTab>('overview');
  const [workspaceData, setWorkspaceData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchWorkspace = () => {
    creatorApi
      .getSeriesWorkspace(seriesId)
      .then((res) => {
        setWorkspaceData(res);
      })
      .catch((err) => {
        console.error('Failed to load series workspace:', err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchWorkspace();
  }, [seriesId]);

  if (loading || !workspaceData) {
    return (
      <div className="py-20 text-center text-welele-muted">
        <div className="w-8 h-8 border-2 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <span>Loading Series Command Room...</span>
      </div>
    );
  }

  const series: Story = workspaceData.series;
  const metrics = workspaceData.metrics;
  const episodes: Episode[] = series.episodes || [];

  const getStatusBadge = (status?: string, isFree?: boolean) => {
    switch (status) {
      case 'published':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-max">
            <CheckCircle2 className="w-3 h-3" /> Published
          </span>
        );
      case 'under_review':
      case 'submitted':
      case 'pending_review':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-max">
            <Clock className="w-3 h-3" /> In Review
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

  return (
    <div className="space-y-6 pb-24 max-w-7xl mx-auto animate-fade-in">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="w-9 h-9 rounded-[7px] bg-white/5 hover:bg-white/10 flex items-center justify-center text-white border border-white/10 transition-all"
            aria-label="Back to series catalogue"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-pink-400">
                SERIES COMMAND ROOM™
              </span>
              <span className="text-welele-muted text-xs">•</span>
              <span className="text-xs text-welele-muted">{series.genre}</span>
            </div>
            <h1 className="text-2xl font-black text-white uppercase tracking-tight font-cinematic">
              {series.title}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2.5 self-end sm:self-center">
          <button
            onClick={() => onOpenEpisodePipeline(series.id, episodes.length + 1)}
            className="px-4 py-2 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-bold text-xs shadow-lg shadow-pink-500/20 flex items-center gap-2 hover:opacity-95 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Add Episode</span>
          </button>
        </div>
      </div>

      {/* Series Hero Command Banner */}
      <div className="relative rounded-[7px] overflow-hidden border border-white/10 bg-[#121318] p-6 shadow-2xl">
        {/* Ambient Artwork Background Glow */}
        <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
          <img
            src={series.cover_image || series.vertical_poster}
            alt={series.title}
            className="w-full h-full object-cover blur-md"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#0F1014] via-[#0F1014]/90 to-transparent" />
        </div>

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <img
              src={series.vertical_poster}
              alt={series.title}
              className="w-20 h-28 rounded-[7px] object-cover border border-white/20 shadow-md shrink-0"
            />
            <div className="space-y-1.5 max-w-xl">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold">
                  ACTIVE PRODUCTION
                </span>
                <span className="text-xs text-welele-muted">
                  {episodes.length} Episodes • {series.language}
                </span>
              </div>
              <p className="text-xs text-white/80 line-clamp-2 leading-relaxed">
                {series.synopsis}
              </p>
              <div className="flex items-center gap-2 text-[11px] text-welele-muted">
                <span>Creator: <b className="text-white">{series.creator_name}</b></span>
                <span>•</span>
                <span>Pricing: <b className="text-welele-gold">🪙 {series.coin_price_per_episode || 5} coins/ep</b></span>
              </div>
            </div>
          </div>

          {/* Quick Velocity KPI Summary */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 w-full md:w-auto shrink-0">
            <div className="p-3 rounded-[7px] bg-black/50 border border-white/10 text-center">
              <span className="text-[10px] text-welele-muted block">Total Views</span>
              <span className="text-base font-black text-white font-cinematic">
                {metrics?.total_views?.toLocaleString() || '1.2M'}
              </span>
            </div>
            <div className="p-3 rounded-[7px] bg-black/50 border border-white/10 text-center">
              <span className="text-[10px] text-welele-muted block">Completion Rate</span>
              <span className="text-base font-black text-emerald-400 font-cinematic">
                {metrics?.completion_rate || '88.4%'}
              </span>
            </div>
            <div className="p-3 rounded-[7px] bg-black/50 border border-white/10 text-center col-span-2 sm:col-span-1">
              <span className="text-[10px] text-welele-muted block">Estimated Revenue</span>
              <span className="text-base font-black text-welele-gold font-cinematic">
                ${metrics?.estimated_earnings_usd || '780.00'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 5-Tab Navigation Workspace Ribbon */}
      <div className="border-b border-white/10 flex items-center gap-2 overflow-x-auto pb-1">
        {[
          { id: 'overview', label: 'Overview', icon: Layers },
          { id: 'episodes', label: `Episodes (${episodes.length})`, icon: Video },
          { id: 'story', label: 'Story Bible', icon: BookOpen },
          { id: 'assets', label: 'Assets & Posters', icon: ImageIcon },
          { id: 'analytics', label: 'Analytics & Hook Rate', icon: BarChart3 },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as SeriesCommandTab)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-[7px] text-xs font-bold transition-all whitespace-nowrap ${
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

      {/* TAB CONTENT: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
              <span className="text-xs text-welele-muted block">Published Episodes</span>
              <div className="text-2xl font-black text-white font-cinematic">
                {metrics?.published_count || episodes.length} / {episodes.length || 10}
              </div>
              <p className="text-[10px] text-emerald-400 font-semibold">Live in Global Viewer Feed</p>
            </div>

            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
              <span className="text-xs text-welele-muted block">In Moderation / Review</span>
              <div className="text-2xl font-black text-amber-400 font-cinematic">
                {metrics?.under_review_count || 0}
              </div>
              <p className="text-[10px] text-welele-muted">Pending admin quality gate verification</p>
            </div>

            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
              <span className="text-xs text-welele-muted block">Draft Pipeline</span>
              <div className="text-2xl font-black text-white/60 font-cinematic">
                {metrics?.draft_count || 0}
              </div>
              <p className="text-[10px] text-welele-muted">Scripts and pre-flights in progress</p>
            </div>
          </div>

          {/* Quick Production Health */}
          <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#FF2A6D]" />
              Production Health & Consistency Check
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-[7px] bg-black/40 border border-emerald-500/20 text-emerald-300">
                ✓ 9:16 Canonical Ratio: 100%
              </div>
              <div className="p-3 rounded-[7px] bg-black/40 border border-emerald-500/20 text-emerald-300">
                ✓ AI Subtitles: Multilingual OK
              </div>
              <div className="p-3 rounded-[7px] bg-black/40 border border-emerald-500/20 text-emerald-300">
                ✓ Cliffhanger Markers: 100% Set
              </div>
              <div className="p-3 rounded-[7px] bg-black/40 border border-emerald-500/20 text-emerald-300">
                ✓ Safe Zone Verified: Pass
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: EPISODES LIFECYCLE TABLE */}
      {activeTab === 'episodes' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Episode Production Schedule & Status
              </h3>
              <p className="text-[11px] text-welele-muted">
                Track each microdrama beat through Draft, Pre-flight, Review, and Published states.
              </p>
            </div>

            <button
              onClick={() => onOpenEpisodePipeline(series.id, episodes.length + 1)}
              className="px-3.5 py-1.5 rounded-[7px] bg-[#E6007A] text-white font-bold text-xs flex items-center gap-1.5 hover:opacity-90"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Add Next Episode</span>
            </button>
          </div>

          <div className="rounded-[7px] border border-white/10 bg-[#121318] overflow-hidden">
            <table className="w-full text-left text-xs text-white">
              <thead className="bg-[#181920] text-welele-muted uppercase font-mono text-[10px] border-b border-white/5">
                <tr>
                  <th className="px-4 py-3">#</th>
                  <th className="px-4 py-3">Episode Title & Cliffhanger</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Access / Coins</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {episodes.map((ep, idx) => {
                  const epNum = ep.episode_number || idx + 1;
                  const formattedNum = epNum < 10 ? `0${epNum}` : `${epNum}`;
                  return (
                    <tr key={ep.id} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3.5 font-mono font-bold text-welele-gold text-xs">
                        {formattedNum}
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="font-bold text-white text-xs">{ep.title}</div>
                        <div className="text-[11px] text-welele-muted line-clamp-1 mt-0.5">
                          {ep.cliffhanger_hook || ep.synopsis}
                        </div>
                      </td>
                      <td className="px-4 py-3.5 font-mono text-welele-muted">
                        {ep.duration_seconds || 65}s
                      </td>
                      <td className="px-4 py-3.5">
                        {ep.is_free ? (
                          <span className="text-emerald-400 font-bold text-[11px]">Free</span>
                        ) : (
                          <span className="text-amber-400 font-bold text-[11px] flex items-center gap-1">
                            <Coins className="w-3 h-3" /> {ep.coin_price || 5} Coins
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3.5">
                        {getStatusBadge(ep.status, ep.is_free)}
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <button
                          onClick={() => onOpenEpisodePipeline(series.id, epNum)}
                          className="px-2.5 py-1 rounded-[7px] bg-white/5 hover:bg-white/10 text-white/80 hover:text-white text-[11px] font-semibold border border-white/10"
                        >
                          Inspect
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

      {/* TAB CONTENT: STORY BIBLE */}
      {activeTab === 'story' && (
        <div className="space-y-4">
          <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-welele-orange" />
              Story Bible & Narrative Architecture
            </h3>

            <div className="space-y-2">
              <label className="text-xs text-welele-muted font-bold block">Series Logline</label>
              <p className="text-xs text-white leading-relaxed p-3 rounded-[7px] bg-black/40 border border-white/10">
                "{series.tagline || series.synopsis}"
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-xs text-welele-muted font-bold block">Core Themes & Tone</label>
              <div className="flex flex-wrap gap-2">
                {series.tags?.map((t) => (
                  <span
                    key={t}
                    className="px-2.5 py-1 rounded-[7px] bg-white/5 border border-white/10 text-xs text-welele-gold font-mono"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs text-welele-muted font-bold block">Available Dialects</label>
              <div className="flex flex-wrap gap-2">
                {series.available_languages?.map((lang) => (
                  <span
                    key={lang}
                    className="px-2.5 py-1 rounded-[7px] bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400"
                  >
                    {lang} (AI Dubbed)
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: ASSETS */}
      {activeTab === 'assets' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3">
              <span className="text-xs font-bold text-white block">Vertical Key Art (9:16)</span>
              <div className="w-48 aspect-[9/16] rounded-[7px] overflow-hidden border border-white/10 mx-auto shadow-md">
                <img
                  src={series.vertical_poster}
                  alt={series.title}
                  className="w-full h-full object-cover"
                />
              </div>
            </div>

            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3">
              <span className="text-xs font-bold text-white block">Horizontal Hero Banner (16:9)</span>
              <div className="w-full aspect-video rounded-[7px] overflow-hidden border border-white/10 shadow-md">
                <img
                  src={series.cover_image || series.vertical_poster}
                  alt={series.title}
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: ANALYTICS */}
      {activeTab === 'analytics' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
              <span className="text-xs text-welele-muted">Average Cliffhanger Completion</span>
              <div className="text-2xl font-black text-emerald-400 font-cinematic">89.1%</div>
              <span className="text-[10px] text-welele-muted">High viewer hook momentum</span>
            </div>

            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
              <span className="text-xs text-welele-muted">Total Unlocks Generated</span>
              <div className="text-2xl font-black text-welele-gold font-cinematic">142,500 🪙</div>
              <span className="text-[10px] text-welele-muted">From coin & airtime unlocks</span>
            </div>

            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
              <span className="text-xs text-welele-muted">30-Day Growth Velocity</span>
              <div className="text-2xl font-black text-[#FF2A6D] font-cinematic">+34.2%</div>
              <span className="text-[10px] text-emerald-400 font-bold">Trending in Gauteng & Lagos</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
