import React, { useState, useEffect } from 'react';
import { Story, Episode } from '../../types';
import { creatorApi } from '../../services/api';
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
  Flame,
  DollarSign
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
            Ready to publish
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 pb-24 max-w-7xl mx-auto animate-fade-in text-white">
      {/* Show Top Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="w-9 h-9 rounded-[7px] bg-white/5 hover:bg-white/10 flex items-center justify-center text-white border border-white/10 transition-all"
            aria-label="Back to My Shows"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black text-white uppercase tracking-tight font-cinematic">
                {series.title}
              </h1>
              <span className="px-2 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Live
              </span>
            </div>
            <p className="text-xs text-welele-muted mt-0.5">
              {series.genre} • {episodes.length} Episodes • {series.language}
            </p>
          </div>
        </div>

        {/* Hero CTA */}
        <div className="flex items-center gap-2.5 self-end sm:self-center">
          <button
            onClick={() => onOpenEpisodePipeline(series.id, episodes.length + 1)}
            className="px-5 py-2.5 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-bold text-xs shadow-lg shadow-pink-500/20 flex items-center gap-2 hover:opacity-95 transition-all"
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
          { id: 'story', label: 'Story & Bible', icon: BookOpen },
          { id: 'insights', label: 'Insights', icon: BarChart3 },
          { id: 'earnings', label: 'Earnings', icon: Coins },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as ShowTab)}
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

      {/* TAB CONTENT: EPISODES */}
      {activeTab === 'episodes' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Episodes List
            </h3>
            <button
              onClick={() => onOpenEpisodePipeline(series.id, episodes.length + 1)}
              className="text-xs text-pink-400 hover:text-pink-300 font-bold flex items-center gap-1"
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
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Access</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {episodes.map((ep, idx) => {
                  const epNum = ep.episode_number || idx + 1;
                  const formattedNum = epNum < 10 ? `0${epNum}` : `${epNum}`;
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

      {/* TAB CONTENT: STORY & BIBLE */}
      {activeTab === 'story' && (
        <div className="space-y-4">
          <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-pink-400" />
              Story & World
            </h3>

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
                    className="px-2.5 py-1 rounded-[7px] bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400"
                  >
                    {lang}
                  </span>
                ))}
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
