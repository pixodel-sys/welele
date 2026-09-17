import React, { useState } from 'react';
import {
  StoryState,
  CurrentAction,
  Dependency,
  ForgeCompletionAssessment,
  ChronologyEvent
} from '../../../types/storyForge';
import { MilestoneProgressBar } from './MilestoneProgressBar';
import { ForgeDecisionCard } from './ForgeDecisionCard';
import { CreatorResponsePanel } from './CreatorResponsePanel';
import { StoryStatePanel } from './StoryStatePanel';
import { DependenciesPanel } from './DependenciesPanel';
import { StoryIntelligencePanel } from './StoryIntelligencePanel';
import { ForgeTraceInspector } from './ForgeTraceInspector';
import { Layers, ListFilter, Brain, Activity } from 'lucide-react';

interface OperatorDiagnosticConsoleProps {
  activeStoryId: string;
  storyState: StoryState;
  currentAction: CurrentAction | null;
  dependencies: Dependency[];
  events: ChronologyEvent[];
  assessment: ForgeCompletionAssessment | null;
  isLoading: boolean;
  errorMessage: string | null;
  onSubmitResponse: (responseText: string, proposalAction?: 'ACCEPT' | 'REJECT' | 'MODIFY') => void;
  onAdvanceAutonomous: () => void;
  onRetry: () => void;
}

export const OperatorDiagnosticConsole: React.FC<OperatorDiagnosticConsoleProps> = ({
  activeStoryId,
  storyState,
  currentAction,
  dependencies,
  events,
  assessment,
  isLoading,
  errorMessage,
  onSubmitResponse,
  onAdvanceAutonomous,
  onRetry,
}) => {
  const [activeRightTab, setActiveRightTab] = useState<'state' | 'dependencies' | 'intelligence' | 'trace'>('state');

  return (
    <div className="space-y-4 font-sans text-white">
      {/* Internal Operator Banner */}
      <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between text-xs font-mono text-amber-300">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <span className="font-bold uppercase tracking-wider">Operator Diagnostic Console</span>
          <span className="text-white/40">• Forensic Inspection & Engine State</span>
        </div>
        <span className="text-[11px] text-white/50">State v{storyState.state_version}</span>
      </div>

      {/* Completion Governance Matrix Bar */}
      <MilestoneProgressBar
        currentMilestone={assessment?.current_milestone}
        targetMilestone={assessment?.target_milestone}
        satisfiedMilestones={assessment?.satisfied_milestones}
        readinessStatus={assessment?.status}
        chronologyAnchorsCount={events.length}
      />

      {/* Main 2-Column Cockpit Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-[580px]">
        {/* LEFT COLUMN: Dominant Decision & Creator Response Panel (7 Cols) */}
        <div className="lg:col-span-7 space-y-4 flex flex-col">
          <ForgeDecisionCard
            action={currentAction?.action || 'ASK'}
            skill={currentAction?.skill || 'EXCAVATOR'}
            question={currentAction?.question}
            proposal={currentAction?.proposal}
            activeDependencyKey={currentAction?.active_dependency_key}
            activeDependencyDescription={currentAction?.active_dependency_description}
            mutations={[]}
          />

          <div className="flex-1">
            <CreatorResponsePanel
              action={currentAction?.action || 'ASK'}
              isLoading={isLoading}
              errorMessage={errorMessage}
              onSubmitResponse={onSubmitResponse}
              onAdvanceAutonomous={onAdvanceAutonomous}
              onRetry={onRetry}
              lastCommittedVersion={storyState.state_version}
            />
          </div>
        </div>

        {/* RIGHT COLUMN: Story State, Dependencies, Intelligence & Trace (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col space-y-3">
          <div className="flex items-center gap-1 p-1 rounded-xl bg-black/50 border border-white/10 text-[11px] font-mono font-bold">
            <button
              onClick={() => setActiveRightTab('state')}
              className={`flex-1 py-1.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                activeRightTab === 'state'
                  ? 'bg-[#FF6500] text-black shadow'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>State</span>
            </button>
            <button
              onClick={() => setActiveRightTab('dependencies')}
              className={`flex-1 py-1.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                activeRightTab === 'dependencies'
                  ? 'bg-[#FF6500] text-black shadow'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <ListFilter className="w-3.5 h-3.5" />
              <span>Queue ({dependencies.filter((d) => !['RESOLVED', 'DELIBERATELY_UNKNOWN', 'DEFERRED'].includes(d.status)).length})</span>
            </button>
            <button
              onClick={() => setActiveRightTab('intelligence')}
              className={`flex-1 py-1.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                activeRightTab === 'intelligence'
                  ? 'bg-[#FF6500] text-black shadow'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <Brain className="w-3.5 h-3.5" />
              <span>Insights</span>
            </button>
            <button
              onClick={() => setActiveRightTab('trace')}
              className={`flex-1 py-1.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                activeRightTab === 'trace'
                  ? 'bg-[#FF6500] text-black shadow'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Trace</span>
            </button>
          </div>

          <div className="flex-1 min-h-[480px]">
            {activeRightTab === 'state' && <StoryStatePanel storyState={storyState} events={events} />}
            {activeRightTab === 'dependencies' && <DependenciesPanel dependencies={dependencies} />}
            {activeRightTab === 'intelligence' && <StoryIntelligencePanel storyId={activeStoryId} />}
            {activeRightTab === 'trace' && <ForgeTraceInspector storyId={activeStoryId} />}
          </div>
        </div>
      </div>
    </div>
  );
};
