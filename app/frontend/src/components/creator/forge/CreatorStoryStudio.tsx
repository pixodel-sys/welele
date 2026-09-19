import React, { useState } from 'react';
import {
  StoryState,
  CurrentAction,
  ForgeCompletionAssessment,
  ChronologyEvent
} from '../../../types/storyForge';
import { CreatorJourneyProgressBar } from './CreatorJourneyProgressBar';
import { CreatorQuestionCard } from './CreatorQuestionCard';
import { ForgeCompleteScreen } from './ForgeCompleteScreen';
import {
  Sparkles,
  RefreshCw,
  BookOpen,
  Users,
  Film,
  Compass,
  CheckCircle2,
  Cpu
} from 'lucide-react';

interface CreatorStoryStudioProps {
  sessionId: string;
  storyState: StoryState;
  currentAction: CurrentAction | null;
  assessment: ForgeCompletionAssessment | null;
  events: ChronologyEvent[];
  isLoading: boolean;
  isWorkingThroughStory: boolean;
  workingStatusMessage?: string;
  errorMessage: string | null;
  onSubmitResponse: (responseText: string, proposalAction?: 'ACCEPT' | 'REJECT' | 'MODIFY') => void;
  onViewStoryPackage: () => void;
  onContinueToEpisodePlanning?: () => void;
  onOpenOperatorConsole: () => void;
}

export const CreatorStoryStudio: React.FC<CreatorStoryStudioProps> = ({
  sessionId,
  storyState,
  currentAction,
  assessment,
  events,
  isLoading,
  isWorkingThroughStory,
  workingStatusMessage = 'Working through your story… Checking how this answer affects the characters and story arc.',
  errorMessage,
  onSubmitResponse,
  onViewStoryPackage,
  onContinueToEpisodePlanning,
  onOpenOperatorConsole,
}) => {
  const isForgeComplete =
    assessment?.status === 'FORGE_COMPLETE' ||
    assessment?.current_milestone === 'FORGE_COMPLETE';

  const characterCount = Object.keys(storyState.characters || {}).length;
  const eventsCount = events.length;

  return (
    <div className="max-w-5xl mx-auto space-y-6 font-sans text-white">
      {/* 1. Persistent 5-Stage Creator Journey Progress Bar */}
      <CreatorJourneyProgressBar
        assessment={assessment}
        currentAction={currentAction}
        eventsCount={eventsCount}
      />

      {/* 2. Compact Story Anchor Card */}
      <div className="p-4 sm:p-5 rounded-2xl bg-[#11131C] border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-[11px] font-mono text-[#FF6500] uppercase font-bold tracking-wider">
            <BookOpen className="w-3.5 h-3.5" />
            <span>Active Story</span>
          </div>
          <h2 className="text-lg sm:text-xl font-black text-white tracking-tight">
            {storyState.title}
          </h2>
          <p className="text-xs text-white/60 line-clamp-1 max-w-2xl">
            {storyState.logline}
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0 text-xs font-mono text-white/60">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
            <Users className="w-3.5 h-3.5 text-[#FFA000]" />
            <span>{characterCount} {characterCount === 1 ? 'Character' : 'Characters'}</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
            <Film className="w-3.5 h-3.5 text-emerald-400" />
            <span>{eventsCount === 0 ? 'Story Foundation' : `${eventsCount} / 6 Beats`}</span>
          </div>
        </div>
      </div>

      {/* 3. Main Work Area: M3 Complete vs Working State vs Creator Question */}
      {isForgeComplete ? (
        <ForgeCompleteScreen
          storyState={storyState}
          assessment={assessment}
          events={events}
          onViewStoryPackage={onViewStoryPackage}
          onContinueToEpisodePlanning={onContinueToEpisodePlanning}
          onOpenOperatorConsole={onOpenOperatorConsole}
        />
      ) : isWorkingThroughStory ? (
        /* Internal Work State: collapses internal transitions into intelligent progress */
        <div className="rounded-3xl bg-gradient-to-b from-[#141622] to-[#0D0E15] border border-white/10 p-10 sm:p-14 text-center shadow-2xl flex flex-col items-center justify-center min-h-[380px] space-y-5 animate-pulse">
          <div className="relative">
            <div className="w-16 h-16 rounded-full bg-[#FF6500]/20 flex items-center justify-center border border-[#FF6500]/40">
              <RefreshCw className="w-8 h-8 text-[#FF6500] animate-spin" />
            </div>
            <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-emerald-500/20 border border-emerald-400/40 flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-emerald-400 animate-pulse" />
            </div>
          </div>

          <div className="space-y-2 max-w-md">
            <h3 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              Working through your story…
            </h3>
            <p className="text-sm text-white/60 leading-relaxed">
              {workingStatusMessage}
            </p>
          </div>

          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[11px] font-mono text-white/40">
            <Cpu className="w-3 h-3 text-[#FF6500]" />
            <span>Synthesizing narrative continuity</span>
          </div>
        </div>
      ) : (
        /* Creator Creative Question Card */
        <CreatorQuestionCard
          currentAction={currentAction}
          storyState={storyState}
          isLoading={isLoading}
          errorMessage={errorMessage}
          onSubmit={onSubmitResponse}
        />
      )}
    </div>
  );
};
