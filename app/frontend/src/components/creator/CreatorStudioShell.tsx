import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { aiApi, creatorApi } from '../../services/api';
import { AIStatus } from '../../types';
import { SeriesCommandRoom } from './SeriesCommandRoom';
import { EpisodePipelineModal } from './EpisodePipelineModal';
import { CreateShowModal } from './CreateShowModal';
import { StoryForgeDoorway } from './StoryForgeDoorway';
import { CreatorEarnings } from './CreatorEarnings';
import { CreatorDashboard } from './CreatorDashboard';
import { ReadinessBadge } from '../common/patterns/ReadinessBadge';
import { ProvenanceBadge } from '../common/patterns/ProvenanceBadge';
import { StatusBadge } from '../common/patterns/StatusBadge';
import {
  Video,
  Sparkles,
  BarChart3,
  Coins,
  PlusCircle,
  Play,
  Flame,
  ArrowRight,
  ShieldCheck,
  Globe,
  Lock,
  Tv,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export type SimpleCreatorTab = 'shows' | 'story_forge' | 'insights' | 'earnings';

export const CreatorStudioShell: React.FC = () => {
  const { stories, user, refreshStories, market, attemptModeChange } = useApp();

  const [activeNavTab, setActiveNavTab] = useState<SimpleCreatorTab>('shows');
  const [selectedSeriesId, setSelectedSeriesId] = useState<string | null>(null);
  const [creatorShows, setCreatorShows] = useState<any[]>([]);

  // Modals
  const [isPipelineOpen, setIsPipelineOpen] = useState<boolean>(false);
  const [isCreateShowOpen, setIsCreateShowOpen] = useState<boolean>(false);
  const [pipelineSeriesId, setPipelineSeriesId] = useState<string | undefined>(undefined);
  const [pipelineEpisodeNumber, setPipelineEpisodeNumber] = useState<number | undefined>(undefined);
  const [pipelinePackageData, setPipelinePackageData] = useState<any>(undefined);

  // AI Connection Status
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);

  const fetchCreatorShows = async () => {
    try {
      const res = await creatorApi.getDashboard(user?.id || 'creator_zola');
      if (res && res.series) {
        setCreatorShows(res.series);
      }
    } catch (e) {
      console.warn('Could not load creator specific dashboard shows:', e);
    }
  };

  useEffect(() => {
    aiApi.getStatus().then((st) => setAiStatus(st)).catch(() => {});
    fetchCreatorShows();
  }, [user]);

  const handleOpenPipeline = (seriesId?: string, episodeNumber?: number, packageData?: any) => {
    setPipelineSeriesId(seriesId || stories[0]?.id);
    setPipelineEpisodeNumber(episodeNumber);
    setPipelinePackageData(packageData);
    setIsPipelineOpen(true);
  };

  const handleOpenShow = (seriesId: string) => {
    setSelectedSeriesId(seriesId);
    setActiveNavTab('shows');
  };

  const handleForgeHandoff = (forgedPackage: any) => {
    const targetSeriesId = forgedPackage?.series_id || stories[0]?.id;
    const targetEpNum = (stories.find(s => s.id === targetSeriesId)?.episodes?.length || 0) + 1;
    handleOpenPipeline(targetSeriesId, targetEpNum, forgedPackage);
  };

  // Determine time-based greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const creatorName = user?.name?.split(' ')[0] || 'Zola';
  const creatorHandle = `@${(user?.name || 'Zola Mthembu').toLowerCase().replace(/\s+/g, '_')}`;

  // Helper to derive 4-dimensional readiness state
  const getShowReadiness = (story: any): 'READY' | 'READY_WITH_WARNINGS' | 'NEEDS_INPUT' | 'BLOCKED' => {
    const epCount = story.episodes?.length || story.total_episodes || 0;
    if (epCount === 0) return 'NEEDS_INPUT';
    if (!story.vertical_poster || !story.synopsis) return 'NEEDS_INPUT';
    if (story.under_review_episodes_count > 0) return 'READY_WITH_WARNINGS';
    return 'READY';
  };

  // Helper to derive audience state deterministically
  const getAudienceState = (story: any): string => {
    const views = story.total_views || story.views || 0;
    if (views === 0) return 'NO AUDIENCE DATA YET';
    if (views < 1000) return 'COLLECTING EVIDENCE';
    if (views < 10000) return 'EARLY SIGNAL';
    return 'MEASURED';
  };

  return (
    <div className="space-y-6 pb-24 text-white animate-fade-in max-w-7xl mx-auto px-4">
      {/* Creator Top Identity & Operational Context Bar */}
      <div className="p-3.5 rounded-[7px] bg-[#101116] border border-white/10 flex flex-wrap items-center justify-between gap-3 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-[7px] bg-gradient-to-tr from-[#E6007A] to-[#FF2A6D] flex items-center justify-center text-white font-bold text-base shadow">
            {creatorName.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-sm text-white">{user?.name || 'Zola Mthembu'}</span>
              <span className="text-xs font-mono text-welele-gold font-bold">{creatorHandle}</span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold">
                <ShieldCheck className="w-3 h-3" /> Verified Showrunner
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-[11px] text-welele-muted">
              <span className="inline-flex items-center gap-1">
                <Globe className="w-3 h-3 text-welele-gold" /> Market: <strong className="text-white">{market || 'ZA'}</strong> (South Africa)
              </span>
              <span>•</span>
              <span className="inline-flex items-center gap-1">
                <Lock className="w-3 h-3 text-pink-400" /> DRM: <strong className="text-white">Active (FairPlay/Widevine)</strong>
              </span>
            </div>
          </div>
        </div>

        {/* Consumer Switch & Mode Indicator */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => attemptModeChange('viewer')}
            className="px-3 py-1.5 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-white hover:text-pink-400 text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer"
            title="Switch to consumer mobile viewer view"
          >
            <Tv className="w-3.5 h-3.5 text-pink-400" />
            <span>Switch to Viewer App</span>
          </button>
        </div>
      </div>

      {/* Top Level Creator Studio Navigation Bar */}
      <div className="p-3 rounded-[7px] bg-[#14151B] border border-white/5 flex items-center justify-between gap-4 overflow-x-auto">
        <div className="flex items-center gap-1.5 shrink-0">
          {[
            { id: 'shows', label: 'My Shows', icon: Video },
            { id: 'story_forge', label: 'Story Forge™', icon: Sparkles, badge: 'AI' },
            { id: 'insights', label: 'Insights', icon: BarChart3 },
            { id: 'earnings', label: 'Earnings', icon: Coins },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeNavTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveNavTab(tab.id as SimpleCreatorTab);
                  if (tab.id !== 'shows') {
                    setSelectedSeriesId(null);
                  }
                }}
                className={`px-3.5 py-2 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white shadow-lg shadow-pink-500/20'
                    : 'bg-black/30 text-welele-muted hover:text-white border border-white/5 hover:border-white/10'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
                {tab.badge && (
                  <span className="px-1.5 py-0.2 rounded-[7px] text-[9px] font-extrabold bg-welele-gold text-black">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={() => setIsCreateShowOpen(true)}
            className="px-3 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold text-xs flex items-center gap-1.5 transition-all"
          >
            <PlusCircle className="w-3.5 h-3.5 text-pink-400" />
            <span className="hidden sm:inline">+ Create Show</span>
          </button>

          <button
            onClick={() => handleOpenPipeline()}
            className="px-4 py-2 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-pink-500/20 hover:opacity-95 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Add Episode</span>
          </button>
        </div>
      </div>

      {/* SUB-VIEW: MY SHOWS */}
      {activeNavTab === 'shows' && (
        <div>
          {selectedSeriesId ? (
            <SeriesCommandRoom
              seriesId={selectedSeriesId}
              onBack={() => setSelectedSeriesId(null)}
              onOpenEpisodePipeline={(sId, epNum) => handleOpenPipeline(sId, epNum)}
            />
          ) : (
            <div className="space-y-6">
              {/* Creator Greeting & Section Header */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div>
                  <h1 className="text-2xl font-black text-white font-cinematic uppercase tracking-tight">
                    {getGreeting()}, {creatorName} 👋
                  </h1>
                  <p className="text-xs text-welele-muted mt-0.5">
                    Your Shows • Select a show to add episodes, review performance, or update scripts.
                  </p>
                </div>

                <button
                  onClick={() => setIsCreateShowOpen(true)}
                  className="px-4 py-2 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-pink-500/20 hover:opacity-95 transition-all"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>+ Create Show</span>
                </button>
              </div>

              {/* Show Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
                {(creatorShows.length > 0 ? creatorShows : stories).map((story) => {
                  const readiness = getShowReadiness(story);
                  const franchiseCode = story.franchise_code || `IP-WEL-${story.id.replace(/[^a-zA-Z0-9]/g, '').slice(-4).toUpperCase()}`;
                  const audienceState = getAudienceState(story);

                  return (
                    <div
                      key={story.id}
                      className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 hover:border-[#E6007A]/50 transition-all group flex flex-col justify-between"
                    >
                      <div className="space-y-3">
                        <div className="aspect-[9/16] w-full max-h-56 rounded-[7px] overflow-hidden relative">
                          <img
                            src={story.vertical_poster}
                            alt={story.title}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                          <div className="absolute top-2 left-2">
                            <span className="px-2 py-0.5 rounded-[7px] bg-black/80 border border-white/20 text-welele-gold text-[10px] font-mono font-bold shadow">
                              {franchiseCode}
                            </span>
                          </div>
                          <div className="absolute top-2 right-2">
                            <ReadinessBadge level={readiness} size="sm" />
                          </div>
                        </div>

                        <div>
                          <div className="flex items-center justify-between gap-1 mb-1">
                            <span className="text-[10px] font-mono text-welele-muted uppercase">
                              {story.genre}
                            </span>
                            <span className="text-[10px] font-mono text-emerald-400/90 font-semibold">
                              {audienceState}
                            </span>
                          </div>
                          <h3 className="text-base font-black text-white group-hover:text-[#FF2A6D] truncate uppercase tracking-tight">
                            {story.title}
                          </h3>
                          <p className="text-xs text-welele-muted mt-1">
                            {story.total_episodes || story.episodes?.length || 1}{' '}
                            {(story.total_episodes || story.episodes?.length || 1) === 1 ? 'Episode' : 'Episodes'}
                            {story.under_review_episodes_count > 0 ? (
                              <span className="text-amber-300 font-semibold"> ({story.under_review_episodes_count} in review)</span>
                            ) : ''}
                          </p>
                        </div>

                        {/* 4-Dimensional Readiness Snapshot */}
                        <div className="p-2.5 rounded-[7px] bg-black/40 border border-white/5 grid grid-cols-2 gap-1.5 text-[10px]">
                          <div className="flex items-center gap-1 text-white/70">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            <span>Story: Ready</span>
                          </div>
                          <div className="flex items-center gap-1 text-white/70">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            <span>Media: 9:16 HD</span>
                          </div>
                          <div className="flex items-center gap-1 text-white/70">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            <span>Rights: Declared</span>
                          </div>
                          <div className="flex items-center gap-1 text-white/70">
                            <span className="w-1.5 h-1.5 rounded-full bg-welele-gold" />
                            <span className="truncate">{audienceState}</span>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                        <button
                          onClick={() => handleOpenShow(story.id)}
                          className="w-full py-2 rounded-[7px] bg-white/5 hover:bg-gradient-to-r hover:from-[#E6007A] hover:to-[#FF2A6D] text-white text-xs font-bold border border-white/10 hover:border-transparent transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                        >
                          <span>Command Room</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}

                {/* Create Show Quick Card */}
                <div
                  onClick={() => setIsCreateShowOpen(true)}
                  className="p-6 rounded-[7px] border-2 border-dashed border-white/15 hover:border-pink-500/50 bg-[#14151B]/50 hover:bg-pink-950/10 cursor-pointer transition-all flex flex-col items-center justify-center text-center space-y-3 min-h-[260px] group"
                >
                  <div className="w-12 h-12 rounded-full bg-pink-500/10 text-pink-400 group-hover:scale-110 transition-transform flex items-center justify-center">
                    <PlusCircle className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white group-hover:text-pink-400">
                      + Create Show
                    </h4>
                    <p className="text-xs text-welele-muted mt-1 max-w-[200px]">
                      Start a new microdrama production and upload Episode 1.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUB-VIEW: STORY FORGE */}
      {activeNavTab === 'story_forge' && (
        <StoryForgeDoorway onSendToProduction={handleForgeHandoff} />
      )}

      {/* SUB-VIEW: INSIGHTS */}
      {activeNavTab === 'insights' && (
        <CreatorDashboard
          onNavigateToUpload={() => handleOpenPipeline()}
          onNavigateToSeries={() => {
            setSelectedSeriesId(null);
            setActiveNavTab('shows');
          }}
          onNavigateToEarnings={() => setActiveNavTab('earnings')}
        />
      )}

      {/* SUB-VIEW: EARNINGS */}
      {activeNavTab === 'earnings' && <CreatorEarnings />}

      {/* Add Episode 5-Step Pipeline Modal */}
      <EpisodePipelineModal
        isOpen={isPipelineOpen}
        onClose={() => setIsPipelineOpen(false)}
        onSuccess={(createdEp) => {
          fetchCreatorShows();
          refreshStories();
          const targetId = pipelineSeriesId || createdEp?.series_id;
          if (targetId) {
            setSelectedSeriesId(targetId);
          }
          setActiveNavTab('shows');
        }}
        initialSeriesId={pipelineSeriesId}
        initialEpisodeNumber={pipelineEpisodeNumber}
        initialPackageData={pipelinePackageData}
      />

      {/* Create Show Modal */}
      <CreateShowModal
        isOpen={isCreateShowOpen}
        onClose={() => setIsCreateShowOpen(false)}
        onSuccess={(newId) => {
          setSelectedSeriesId(newId);
          setActiveNavTab('shows');
        }}
      />
    </div>
  );
};
