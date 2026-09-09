import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { creatorApi, aiApi } from '../../services/api';
import { CreatorNavTab, Story, AIStatus } from '../../types';
import { SeriesCommandRoom } from './SeriesCommandRoom';
import { EpisodePipelineModal } from './EpisodePipelineModal';
import { StoryForgeDoorway } from './StoryForgeDoorway';
import { GlobalEpisodesManager } from './GlobalEpisodesManager';
import { CreatorEarnings } from './CreatorEarnings';
import { CreatorDashboard } from './CreatorDashboard';
import {
  TrendingUp,
  Eye,
  Heart,
  Coins,
  DollarSign,
  PlusCircle,
  Video,
  Sparkles,
  Zap,
  BookOpen,
  BarChart3,
  Layers,
  User,
  ShieldCheck,
  Flame,
  ArrowRight,
  Clock,
  Cpu,
  RefreshCw
} from 'lucide-react';

export const CreatorStudioShell: React.FC = () => {
  const { stories, refreshStories } = useApp();

  const [activeNavTab, setActiveNavTab] = useState<CreatorNavTab>('overview');
  const [selectedSeriesId, setSelectedSeriesId] = useState<string | null>(null);
  
  // AI Status
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);

  useEffect(() => {
    aiApi.getStatus().then((st) => setAiStatus(st)).catch(() => {});
  }, []);

  // Pipeline Modal State
  const [isPipelineOpen, setIsPipelineOpen] = useState<boolean>(false);
  const [pipelineSeriesId, setPipelineSeriesId] = useState<string | undefined>(undefined);
  const [pipelineEpisodeNumber, setPipelineEpisodeNumber] = useState<number | undefined>(undefined);

  const handleOpenPipeline = (seriesId?: string, episodeNumber?: number) => {
    setPipelineSeriesId(seriesId);
    setPipelineEpisodeNumber(episodeNumber);
    setIsPipelineOpen(true);
  };

  const handleOpenSeriesCommandRoom = (seriesId: string) => {
    setSelectedSeriesId(seriesId);
    setActiveNavTab('series');
  };

  const handleForgeHandoff = (forgedPackage: any) => {
    handleOpenPipeline(stories[0]?.id, (stories[0]?.episodes?.length || 0) + 1);
  };

  return (
    <div className="space-y-6 pb-24 text-white animate-fade-in max-w-7xl mx-auto px-4">
      {/* Top Level Creator Studio Navigation Bar */}
      <div className="p-3 rounded-[7px] bg-[#14151B] border border-white/5 flex items-center justify-between gap-4 overflow-x-auto">
        <div className="flex items-center gap-1.5 shrink-0">
          {[
            { id: 'overview', label: 'Studio Overview', icon: BarChart3 },
            { id: 'series', label: 'Series Command Rooms', icon: Video },
            { id: 'story_forge', label: 'Story Forge™ AI', icon: Sparkles, badge: 'AI' },
            { id: 'episodes', label: 'Episode Ingestion', icon: Layers },
            { id: 'analytics', label: 'Retention & Drop-off', icon: Flame },
            { id: 'earnings', label: 'MoMo Payouts', icon: Coins },
            { id: 'profile', label: 'Showrunner KYC', icon: User },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeNavTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveNavTab(tab.id as CreatorNavTab);
                  if (tab.id !== 'series') {
                    setSelectedSeriesId(null);
                  }
                }}
                className={`px-3 py-2 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all whitespace-nowrap ${
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
          {/* AI Connectivity status pill */}
          {aiStatus && (
            <div
              className={`px-2.5 py-1.5 rounded-[7px] text-[10px] font-bold border flex items-center gap-1.5 ${
                aiStatus.is_connected
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${aiStatus.is_connected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="hidden sm:inline">{aiStatus.is_connected ? 'Gemini AI Live' : 'AI Offline Fallback'}</span>
            </div>
          )}

          <button
            onClick={() => handleOpenPipeline()}
            className="px-4 py-2 rounded-[7px] bg-welele-gold hover:bg-yellow-400 text-black font-bold text-xs flex items-center gap-1.5 shadow transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Upload Episode</span>
          </button>
        </div>
      </div>

      {/* SUB-VIEW: OVERVIEW & ANALYTICS */}
      {(activeNavTab === 'overview' || activeNavTab === 'analytics') && (
        <CreatorDashboard
          onNavigateToUpload={() => handleOpenPipeline()}
          onNavigateToSeries={() => {
            setSelectedSeriesId(null);
            setActiveNavTab('series');
          }}
          onNavigateToEarnings={() => setActiveNavTab('earnings')}
        />
      )}

      {/* SUB-VIEW: SERIES */}
      {activeNavTab === 'series' && (
        <div>
          {selectedSeriesId ? (
            <SeriesCommandRoom
              seriesId={selectedSeriesId}
              onBack={() => setSelectedSeriesId(null)}
              onOpenEpisodePipeline={(sId, epNum) => handleOpenPipeline(sId, epNum)}
            />
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-black text-white font-cinematic uppercase tracking-tight">
                    Microdrama Series Catalogue
                  </h2>
                  <p className="text-xs text-welele-muted">
                    Select a series to open its production Command Room, manage episodes, and inspect Story Bible.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {stories.map((story) => (
                  <div
                    key={story.id}
                    onClick={() => handleOpenSeriesCommandRoom(story.id)}
                    className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 hover:border-[#E6007A]/50 transition-all cursor-pointer group flex flex-col justify-between"
                  >
                    <div className="space-y-3">
                      <div className="aspect-[9/16] w-full max-h-56 rounded-[7px] overflow-hidden relative">
                        <img
                          src={story.vertical_poster}
                          alt={story.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                        <div className="absolute top-2 right-2 px-2 py-0.5 rounded-[7px] bg-black/70 text-emerald-400 text-[10px] font-bold">
                          {story.episodes?.length || 10} Episodes
                        </div>
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white group-hover:text-[#FF2A6D] truncate">
                          {story.title}
                        </h3>
                        <p className="text-xs text-welele-muted line-clamp-1">{story.tagline || story.synopsis}</p>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs">
                      <span className="text-welele-gold font-bold">🪙 {story.coin_price_per_episode || 5} Coins/ep</span>
                      <span className="text-pink-400 font-bold flex items-center gap-1 group-hover:underline">
                        Open Command Room →
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUB-VIEW: STORY FORGE */}
      {activeNavTab === 'story_forge' && (
        <StoryForgeDoorway onSendToProduction={handleForgeHandoff} />
      )}

      {/* SUB-VIEW: EPISODES GLOBAL MANAGER */}
      {activeNavTab === 'episodes' && (
        <GlobalEpisodesManager
          onOpenEpisodePipeline={(sId, epNum) => handleOpenPipeline(sId, epNum)}
        />
      )}

      {/* SUB-VIEW: EARNINGS */}
      {activeNavTab === 'earnings' && <CreatorEarnings />}

      {/* SUB-VIEW: PROFILE */}
      {activeNavTab === 'profile' && (
        <div className="p-6 rounded-[7px] bg-[#14151B] border border-white/10 max-w-2xl mx-auto space-y-4 text-xs">
          <div className="flex items-center gap-4">
            <img
              src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80"
              alt="Zola Dlamini"
              className="w-16 h-16 rounded-[7px] object-cover border border-pink-500/40"
            />
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">Zola Dlamini</h3>
                <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-pink-500/20 text-[#FF2A6D] border border-pink-500/30">
                  VERIFIED SHOWRUNNER
                </span>
              </div>
              <p className="text-welele-muted">@zola_cinemas • Johannesburg, South Africa</p>
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <label className="text-welele-muted font-bold block">Bio</label>
            <p className="p-3 rounded-[7px] bg-[#0F1014] text-white/90">
              Johannesburg crime & dynasty showrunner. Master of the 60-second Mzansi cliffhanger. Creator of Blood Ties and Queen of Jozi.
            </p>
          </div>
        </div>
      )}

      {/* Global 5-Step Episode Pipeline Modal */}
      <EpisodePipelineModal
        isOpen={isPipelineOpen}
        onClose={() => setIsPipelineOpen(false)}
        onSuccess={() => {
          refreshStories();
        }}
        initialSeriesId={pipelineSeriesId}
        initialEpisodeNumber={pipelineEpisodeNumber}
      />
    </div>
  );
};
