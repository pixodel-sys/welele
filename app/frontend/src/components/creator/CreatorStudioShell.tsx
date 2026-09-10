import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { aiApi } from '../../services/api';
import { AIStatus } from '../../types';
import { SeriesCommandRoom } from './SeriesCommandRoom';
import { EpisodePipelineModal } from './EpisodePipelineModal';
import { CreateShowModal } from './CreateShowModal';
import { StoryForgeDoorway } from './StoryForgeDoorway';
import { CreatorEarnings } from './CreatorEarnings';
import { CreatorDashboard } from './CreatorDashboard';
import {
  Video,
  Sparkles,
  BarChart3,
  Coins,
  PlusCircle,
  Play,
  Flame,
  ArrowRight
} from 'lucide-react';

export type SimpleCreatorTab = 'shows' | 'story_forge' | 'insights' | 'earnings';

export const CreatorStudioShell: React.FC = () => {
  const { stories, user } = useApp();

  const [activeNavTab, setActiveNavTab] = useState<SimpleCreatorTab>('shows');
  const [selectedSeriesId, setSelectedSeriesId] = useState<string | null>(null);

  // Modals
  const [isPipelineOpen, setIsPipelineOpen] = useState<boolean>(false);
  const [isCreateShowOpen, setIsCreateShowOpen] = useState<boolean>(false);
  const [pipelineSeriesId, setPipelineSeriesId] = useState<string | undefined>(undefined);
  const [pipelineEpisodeNumber, setPipelineEpisodeNumber] = useState<number | undefined>(undefined);

  // AI Connection Status
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);

  useEffect(() => {
    aiApi.getStatus().then((st) => setAiStatus(st)).catch(() => {});
  }, []);

  const handleOpenPipeline = (seriesId?: string, episodeNumber?: number) => {
    setPipelineSeriesId(seriesId || stories[0]?.id);
    setPipelineEpisodeNumber(episodeNumber);
    setIsPipelineOpen(true);
  };

  const handleOpenShow = (seriesId: string) => {
    setSelectedSeriesId(seriesId);
    setActiveNavTab('shows');
  };

  const handleForgeHandoff = (_forgedPackage: any) => {
    handleOpenPipeline(stories[0]?.id, (stories[0]?.episodes?.length || 0) + 1);
  };

  // Determine time-based greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const creatorName = user?.name?.split(' ')[0] || 'Zola';

  return (
    <div className="space-y-6 pb-24 text-white animate-fade-in max-w-7xl mx-auto px-4">
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
                {stories.map((story) => (
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
                        <div className="absolute top-2 right-2 px-2 py-0.5 rounded-[7px] bg-black/80 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                          Live
                        </div>
                      </div>

                      <div>
                        <h3 className="text-base font-black text-white group-hover:text-[#FF2A6D] truncate uppercase tracking-tight">
                          {story.title}
                        </h3>
                        <p className="text-xs text-welele-muted">
                          {story.episodes?.length || story.total_episodes || 1}{' '}
                          {(story.episodes?.length || story.total_episodes || 1) === 1 ? 'Episode' : 'Episodes'} • {story.genre}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                      <button
                        onClick={() => handleOpenShow(story.id)}
                        className="w-full py-2 rounded-[7px] bg-white/5 hover:bg-gradient-to-r hover:from-[#E6007A] hover:to-[#FF2A6D] text-white text-xs font-bold border border-white/10 hover:border-transparent transition-all flex items-center justify-center gap-1.5"
                      >
                        <span>Continue Show</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}

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
        onSuccess={() => {}}
        initialSeriesId={pipelineSeriesId}
        initialEpisodeNumber={pipelineEpisodeNumber}
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
