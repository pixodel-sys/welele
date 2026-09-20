import React from 'react';
import { MilestoneEnum, ReadinessStatus } from '../../../types/storyForge';
import { CheckCircle2, Circle, Clock, Flame, ShieldCheck, Sparkles } from 'lucide-react';

interface MilestoneProgressBarProps {
  currentMilestone?: MilestoneEnum | string | null;
  targetMilestone?: MilestoneEnum | string;
  satisfiedMilestones?: (MilestoneEnum | string)[];
  readinessStatus?: ReadinessStatus | string;
  chronologyAnchorsCount?: number;
}

export const MilestoneProgressBar: React.FC<MilestoneProgressBarProps> = ({
  currentMilestone,
  targetMilestone = 'FORGE_COMPLETE',
  satisfiedMilestones = [],
  readinessStatus = 'NOT_READY',
  chronologyAnchorsCount = 0,
}) => {
  const isM0Satisfied = satisfiedMilestones.includes('PREMISE_LOCK') || currentMilestone === 'PREMISE_LOCK' || currentMilestone === 'DRAMATIC_ENGINE_LOCK' || currentMilestone === 'EPISODIC_ARC_LOCK' || currentMilestone === 'FORGE_COMPLETE';
  const isM1Satisfied = satisfiedMilestones.includes('DRAMATIC_ENGINE_LOCK') || currentMilestone === 'DRAMATIC_ENGINE_LOCK' || currentMilestone === 'EPISODIC_ARC_LOCK' || currentMilestone === 'FORGE_COMPLETE';
  const isM2Satisfied = satisfiedMilestones.includes('EPISODIC_ARC_LOCK') || currentMilestone === 'EPISODIC_ARC_LOCK' || currentMilestone === 'FORGE_COMPLETE';
  const isM3Satisfied = satisfiedMilestones.includes('FORGE_COMPLETE') || currentMilestone === 'FORGE_COMPLETE' || readinessStatus === 'FORGE_COMPLETE';

  const milestones = [
    {
      id: 'M0',
      name: 'PREMISE',
      code: 'PREMISE_LOCK',
      satisfied: isM0Satisfied,
      isCurrent: currentMilestone === 'PREMISE_LOCK',
      detail: isM0Satisfied ? 'Locked' : 'In Progress',
    },
    {
      id: 'M1',
      name: 'DRAMATIC ENGINE',
      code: 'DRAMATIC_ENGINE_LOCK',
      satisfied: isM1Satisfied,
      isCurrent: currentMilestone === 'DRAMATIC_ENGINE_LOCK',
      detail: isM1Satisfied ? 'Locked' : (isM0Satisfied ? 'Active' : 'Pending'),
    },
    {
      id: 'M2',
      name: 'EPISODIC ARC',
      code: 'EPISODIC_ARC_LOCK',
      satisfied: isM2Satisfied,
      isCurrent: currentMilestone === 'EPISODIC_ARC_LOCK',
      detail: isM2Satisfied ? '6 / 6 Anchors' : `${Math.min(6, chronologyAnchorsCount)} / 6 Anchors`,
    },
    {
      id: 'M3',
      name: 'FORGE COMPLETE',
      code: 'FORGE_COMPLETE',
      satisfied: isM3Satisfied,
      isCurrent: currentMilestone === 'FORGE_COMPLETE',
      detail: isM3Satisfied ? 'Certified' : 'Target',
    },
  ];

  return (
    <div className="w-full bg-[#101116]/80 backdrop-blur-md border border-white/10 rounded-xl p-3.5 shadow-xl">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2.5 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#FF6500] animate-pulse" />
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-white/90">
            Completion Governance Matrix
          </span>
        </div>

        <div className="flex items-center gap-2 text-[11px] font-mono">
          <span className="text-white/40">CURRENT:</span>
          <span className="px-2 py-0.5 rounded bg-white/10 text-[#FFA000] font-semibold border border-white/10">
            {currentMilestone ? String(currentMilestone).replace('_LOCK', '').replace('_', ' ') : 'M0 INITIAL'}
          </span>
          <span className="text-white/20">•</span>
          <span className="text-white/40">TARGET:</span>
          <span className="px-2 py-0.5 rounded bg-[#FF6500]/15 text-[#FF6500] font-semibold border border-[#FF6500]/30">
            {String(targetMilestone).replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* 4-Step Milestone Track */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
        {milestones.map((m) => {
          return (
            <div
              key={m.id}
              className={`p-2.5 rounded-lg border transition-all flex flex-col justify-between ${
                m.satisfied
                  ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-400'
                  : m.isCurrent
                  ? 'bg-[#FF6500]/10 border-[#FF6500]/50 text-amber-300 shadow-lg shadow-[#FF6500]/5'
                  : 'bg-white/[0.02] border-white/5 text-white/40'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-black/40 border border-white/10">
                  {m.id}
                </span>
                {m.satisfied ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : m.isCurrent ? (
                  <Clock className="w-4 h-4 text-amber-400 animate-spin" />
                ) : (
                  <Circle className="w-3.5 h-3.5 text-white/20" />
                )}
              </div>

              <div>
                <div className="text-xs font-bold uppercase tracking-tight text-white/90 truncate">
                  {m.name}
                </div>
                <div className="text-[11px] font-mono mt-0.5 opacity-80">
                  {m.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
