import React from 'react';
import { ForgeCompletionAssessment, CurrentAction } from '../../../types/storyForge';
import { getCreatorStages } from '../../../utils/creatorVocabulary';
import { CheckCircle2, Circle, Clock, Sparkles, Flame } from 'lucide-react';

interface CreatorJourneyProgressBarProps {
  assessment: ForgeCompletionAssessment | null;
  currentAction: CurrentAction | null;
  eventsCount?: number;
}

export const CreatorJourneyProgressBar: React.FC<CreatorJourneyProgressBarProps> = ({
  assessment,
  currentAction,
  eventsCount = 0,
}) => {
  const { stages, currentStageNumber, progressPercent } = getCreatorStages(
    assessment,
    currentAction,
    eventsCount
  );

  const activeStage = stages.find((s) => s.isCurrent) || stages[0];

  return (
    <div className="w-full bg-[#101118]/90 backdrop-blur-md border border-white/10 rounded-2xl p-4 sm:p-5 shadow-2xl transition-all">
      {/* Top Stage & Status Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-white/5">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-[#FF6500] animate-pulse" />
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-white/90">
            Story Journey
          </span>
          <span className="text-white/20">•</span>
          <span className="text-xs font-mono text-[#FFA000] font-semibold">
            Stage {currentStageNumber} of 5
          </span>
          <span className="hidden md:inline text-xs text-white/40">
            ({progressPercent}% honest completion)
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-white/50 italic">{activeStage.tagline}</span>
        </div>
      </div>

      {/* 5-Step Creator Journey Visual Track */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2.5 mt-4">
        {stages.map((stage) => {
          return (
            <div
              key={stage.stageNumber}
              className={`p-3 rounded-xl border transition-all flex flex-col justify-between ${
                stage.isSatisfied
                  ? 'bg-emerald-950/25 border-emerald-500/40 text-emerald-300'
                  : stage.isCurrent
                  ? 'bg-[#FF6500]/15 border-[#FF6500]/60 text-white shadow-lg shadow-[#FF6500]/10 ring-1 ring-[#FF6500]/30'
                  : 'bg-white/[0.02] border-white/5 text-white/40'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                    stage.isSatisfied
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : stage.isCurrent
                      ? 'bg-[#FF6500]/30 text-[#FFA000]'
                      : 'bg-white/5 text-white/30'
                  }`}
                >
                  Stage {stage.stageNumber}
                </span>

                {stage.isSatisfied ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : stage.isCurrent ? (
                  <div className="w-2.5 h-2.5 rounded-full bg-[#FF6500] animate-ping" />
                ) : (
                  <Circle className="w-3.5 h-3.5 text-white/20" />
                )}
              </div>

              <div>
                <div
                  className={`text-xs font-bold tracking-tight ${
                    stage.isCurrent ? 'text-white' : stage.isSatisfied ? 'text-emerald-200' : 'text-white/50'
                  }`}
                >
                  {stage.name}
                </div>
                <div className="text-[10px] text-white/40 mt-0.5 line-clamp-1">
                  {stage.stageNumber === 5 ? 'M3 Complete' : stage.tagline}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
