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

  const creatorName = user?.name || 'Zola Dlamini';
  const creatorHandle = '@zola_dlamini';

  // Canonical 4-Dimensional Readiness Evaluation Contract
  const getShow4DContract = (story: any) => {
    const epCount = story.episodes?.length || story.total_episodes || 0;
    const underReviewCount = story.under_review_episodes_count || (story.episodes?.filter((e: any) => e.status === 'under_review').length || 0);
    const hasStory = Boolean(story.synopsis && story.title);
    const hasMedia = epCount > 0;
    const hasRights = Boolean(story.creator_id || story.ip_id);
    const views = story.total_views || story.views || 0;

    // Overall Readiness
    let readiness: 'READY' | 'READY_WITH_WARNINGS' | 'NEEDS_INPUT' | 'BLOCKED' = 'READY';
    if (!hasStory) {
      readiness = 'BLOCKED';
    } else if (!hasMedia) {
      readiness = 'NEEDS_INPUT';
    } else if (underReviewCount > 0) {
      readiness = 'READY_WITH_WARNINGS';
    }

    // Audience Evidence State
    let audienceState = 'NO AUDIENCE DATA YET';
    let audienceColor = 'bg-zinc-500';
    if (views > 0 && views < 1000) {
      audienceState = 'COLLECTING EVIDENCE';
      audienceColor = 'bg-amber-400';
    } else if (views >= 1000 && views < 10000) {
      audienceState = 'EARLY SIGNAL';
      audienceColor = 'bg-emerald-400';
    } else if (views >= 10000) {
      audienceState = 'MEASURED';
      audienceColor = 'bg-sky-400';
    }

    return {
      readiness,
      storyDimension: {
        state: hasStory ? 'READY' : 'NEEDS_INPUT',
        label: hasStory ? 'Story: Ready' : 'Story: Incomplete',
        dotColor: hasStory ? 'bg-emerald-400' : 'bg-red-400'
      },
      mediaDimension: {
        state: epCount === 0 ? 'NEEDS_INPUT' : (underReviewCount > 0 ? 'WARNINGS' : 'READY'),
        label: epCount === 0 ? 'Media: Empty' : (underReviewCount > 0 ? `Media: ${underReviewCount} in review` : 'Media: 9:16 HD'),
        dotColor: epCount === 0 ? 'bg-amber-400' : (underReviewCount > 0 ? 'bg-amber-300' : 'bg-emerald-400')
      },
      rightsDimension: {
        state: hasRights ? 'READY' : 'NEEDS_INPUT',
        label: hasRights ? 'Rights: Declared' : 'Rights: Unset',
        dotColor: hasRights ? 'bg-emerald-400' : 'bg-amber-400'
      },
      audienceDimension: {
        state: audienceState,
        label: audienceState,
        dotColor: audienceColor
      }
    };
  };

  return (
    <div className="space-y-6 pb-24 text-white animate-fade-in max-w-7xl mx-auto px-4">
      {/* ========================================================================= */}
      {/* LAYER 1: WHO AM I? + CREATOR COMMAND BAR (GLOBAL CONTEXT & TOOLS) */}
      {/* ========================================================================= */}
      <div className="p-4 rounded-[7px] bg-[#101116] border border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-md">
        {/* Creator Identity Context */}
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-[7px] bg-gradient-to-tr from-[#E6007A] to-[#FF2A6D] flex items-center justify-center text-white font-black text-lg shadow-md shrink-0">
            {creatorName.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-extrabold text-base text-white">{creatorName}</span>
              <span className="text-xs font-mono text-welele-gold font-bold">{creatorHandle}</span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold">
                <ShieldCheck className="w-3 h-3" /> Verified Showrunner
              </span>
            </div>
            <div className="flex items-center gap-2.5 mt-1 text-[11px] text-welele-muted">
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

        {/* Creator Command Actions */}
        <div className="flex items-center gap-2 flex-wrap shrink-0">
          <button
            onClick={() => setActiveNavTab('story_forge')}
            className={`px-3.5 py-2 rounded-[7px] font-bold text-xs flex items-center gap-1.5 transition-all shadow-sm cursor-pointer ${
              activeNavTab === 'story_forge'
                ? 'bg-welele-gold text-black shadow-md shadow-amber-500/20'
                : 'bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 border border-amber-500/40 text-amber-300'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-welele-gold" />
            <span>✨ Story Forge™</span>
          </button>

          <button
            onClick={() => setIsCreateShowOpen(true)}
            className="px-3.5 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <PlusCircle className="w-3.5 h-3.5 text-pink-400" />
            <span>+ Create Show</span>
          </button>

          <button
            onClick={() => handleOpenPipeline(selectedSeriesId || stories[0]?.id)}
            className="px-4 py-2 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-pink-500/20 hover:opacity-95 transition-all cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Add Episode</span>
          </button>

          <button
            onClick={() => attemptModeChange('viewer')}
            className="px-3 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-white hover:text-pink-400 text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer"
            title="Switch to consumer mobile viewer view"
          >
            <Tv className="w-3.5 h-3.5 text-pink-400" />
            <span className="hidden sm:inline">Switch to Viewer App</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* LAYER 2 & 3: WHAT AM I WORKING ON? & WHAT CAN I DO WITH IT? */}
      {/* ========================================================================= */}

      {/* VIEW: STORY FORGE™ WORKSPACE */}
      {activeNavTab === 'story_forge' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setActiveNavTab('shows')}
              className="text-xs text-welele-muted hover:text-white font-bold flex items-center gap-1.5 cursor-pointer py-1"
            >
              ← Back to My Shows
            </button>
          </div>
          <StoryForgeDoorway
            onSendToProduction={handleForgeHandoff}
          />
        </div>
      )}

      {/* VIEW: SHOWS WORKSPACE */}
      {activeNavTab === 'shows' && (
        <div>
          {selectedSeriesId ? (
            /* LAYER 2 + 3: ACTIVE SHOW WORKSPACE (Command Room with Embedded Tabs) */
            <SeriesCommandRoom
              seriesId={selectedSeriesId}
              onBack={() => setSelectedSeriesId(null)}
              onOpenEpisodePipeline={(sId, epNum) => handleOpenPipeline(sId, epNum)}
            />
          ) : (
            /* ALL SHOWS ROSTER (Overview & 4D Readiness Matrix) */
            <div className="space-y-6">
              {/* Creator Greeting & Section Header */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div>
                  <h1 className="text-2xl font-black text-white font-cinematic uppercase tracking-tight">
                    {getGreeting()}, {creatorName.split(' ')[0]} 👋
                  </h1>
                  <p className="text-xs text-welele-muted mt-0.5">
                    Your Shows • Select a show to manage episodes, review audience performance, and track earnings.
                  </p>
                </div>
              </div>

              {/* Show Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
                {(creatorShows.length > 0 ? creatorShows : stories).map((story) => {
                  const contract4d = getShow4DContract(story);
                  const franchiseCode = story.franchise_code || `IP-WEL-${story.id.replace(/[^a-zA-Z0-9]/g, '').slice(-4).toUpperCase()}`;

                  return (
                    <div
                      key={story.id}
                      onClick={() => handleOpenShow(story.id)}
                      className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 hover:border-[#E6007A]/50 transition-all group flex flex-col justify-between cursor-pointer hover:shadow-xl hover:shadow-pink-500/10"
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
                            <ReadinessBadge level={contract4d.readiness} size="sm" />
                          </div>
                        </div>

                        <div>
                          <div className="flex items-center justify-between gap-1 mb-1">
                            <span className="text-[10px] font-mono text-welele-muted uppercase">
                              {story.genre}
                            </span>
                            <span className="text-[10px] font-mono text-welele-gold font-semibold">
                              {contract4d.audienceDimension.label}
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

                        {/* Canonical 4-Dimensional Readiness Snapshot */}
                        <div className="p-2.5 rounded-[7px] bg-black/40 border border-white/5 grid grid-cols-2 gap-1.5 text-[10px]">
                          <div className="flex items-center gap-1.5 text-white/80">
                            <span className={`w-1.5 h-1.5 rounded-full ${contract4d.storyDimension.dotColor}`} />
                            <span className="truncate">{contract4d.storyDimension.label}</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-white/80">
                            <span className={`w-1.5 h-1.5 rounded-full ${contract4d.mediaDimension.dotColor}`} />
                            <span className="truncate">{contract4d.mediaDimension.label}</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-white/80">
                            <span className={`w-1.5 h-1.5 rounded-full ${contract4d.rightsDimension.dotColor}`} />
                            <span className="truncate">{contract4d.rightsDimension.label}</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-white/80">
                            <span className={`w-1.5 h-1.5 rounded-full ${contract4d.audienceDimension.dotColor}`} />
                            <span className="truncate">{contract4d.audienceDimension.label}</span>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                        <div className="w-full py-2 rounded-[7px] bg-white/5 group-hover:bg-gradient-to-r group-hover:from-[#E6007A] group-hover:to-[#FF2A6D] text-white text-xs font-bold border border-white/10 group-hover:border-transparent transition-all flex items-center justify-center gap-1.5">
                          <span>Open Show Workspace</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </div>
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
