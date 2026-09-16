import React, { useState, useEffect, useCallback } from 'react';
import { storyForgeApi } from '../../../services/storyForgeApi';
import {
  StoryState,
  CurrentAction,
  Dependency,
  ForgeTransition,
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
import { ForgeCompletePackageModal } from './ForgeCompletePackageModal';
import { StoryIntakeScreen } from './StoryIntakeScreen';
import {
  Sparkles,
  Layers,
  Activity,
  Brain,
  ListFilter,
  CheckCircle2,
  ArrowLeft,
  RefreshCw,
  AlertCircle,
  FileCheck
} from 'lucide-react';

export const StoryForgeCockpit: React.FC = () => {
  // Session & Story State
  const [activeStoryId, setActiveStoryId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [storyState, setStoryState] = useState<StoryState | null>(null);
  const [currentAction, setCurrentAction] = useState<CurrentAction | null>(null);
  const [dependencies, setDependencies] = useState<Dependency[]>([]);
  const [events, setEvents] = useState<ChronologyEvent[]>([]);
  const [assessment, setAssessment] = useState<ForgeCompletionAssessment | null>(null);

  // UI / Drawer States
  const [activeRightTab, setActiveRightTab] = useState<'state' | 'dependencies' | 'intelligence' | 'trace'>('state');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPackageModalOpen, setIsPackageModalOpen] = useState<boolean>(false);

  // Initialize or resume session
  const initializeSession = async (storyId: string, initialPremise?: string) => {
    setActiveStoryId(storyId);
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const sess = await storyForgeApi.startSession(storyId, {
        creator_id: 'creator_current',
        initial_premise: initialPremise,
      });

      setSessionId(sess.id);
      await refreshAllData(storyId, sess.id);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to start Forge session.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshAllData = async (storyId: string, sId?: string) => {
    try {
      const [stateData, depsData, compData] = await Promise.all([
        storyForgeApi.getStoryState(storyId),
        storyForgeApi.getDependencies(storyId),
        storyForgeApi.getCompletion(storyId),
      ]);

      setStoryState(stateData);
      setDependencies(depsData);
      setAssessment(compData);

      const targetSessionId = sId || sessionId;
      if (targetSessionId) {
        const actionData = await storyForgeApi.getCurrentAction(targetSessionId);
        setCurrentAction(actionData);
      }
    } catch (err: any) {
      console.warn('Could not refresh full story forge state:', err);
    }
  };

  // Submit creator input / answer to question
  const handleSubmitResponse = async (
    responseText: string,
    proposalAction?: 'ACCEPT' | 'REJECT' | 'MODIFY'
  ) => {
    if (!sessionId || !activeStoryId) return;

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const cycleResult = await storyForgeApi.submitInput(sessionId, {
        creator_response: responseText,
        proposal_action: proposalAction,
      });

      setStoryState(cycleResult.current_state);

      // Refresh current action and dependencies
      await refreshAllData(activeStoryId, sessionId);

      // If Judge certified FORGE_COMPLETE
      if (cycleResult.action === 'STOP' && assessment?.status === 'FORGE_COMPLETE') {
        setIsPackageModalOpen(true);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Error processing story cycle.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // Advance autonomous step (for INFER or RECORD_PRODUCTION_DECISION)
  const handleAdvanceAutonomous = async () => {
    if (!sessionId || !activeStoryId) return;
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const cycleResult = await storyForgeApi.submitInput(sessionId, {});
      setStoryState(cycleResult.current_state);
      await refreshAllData(activeStoryId, sessionId);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Error advancing story cycle.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // If no story active, show Story Intake
  if (!activeStoryId || !storyState) {
    return (
      <StoryIntakeScreen
        onStoryCreated={(id, premise) => initializeSession(id, premise)}
        onResumeStory={(id) => initializeSession(id)}
      />
    );
  }

  const isForgeComplete = assessment?.status === 'FORGE_COMPLETE';

  return (
    <div className="max-w-7xl mx-auto py-4 px-3 sm:px-5 space-y-4 font-sans text-white">
      {/* Top Cockpit Command Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pb-3 border-b border-white/10">
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setActiveStoryId(null);
              setSessionId(null);
            }}
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/50 hover:text-white transition-colors flex items-center gap-1 text-xs font-mono"
            title="Return to Story Intake"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Intake</span>
          </button>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#FF6500]/20 text-[#FF6500] border border-[#FF6500]/30 uppercase">
                Story Forge™ v0.2
              </span>
              <span className="text-xs font-mono text-white/40">v{storyState.state_version}</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight font-sans">
              {storyState.title}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {isForgeComplete && (
            <button
              onClick={() => setIsPackageModalOpen(true)}
              className="px-4 py-2 rounded-xl bg-emerald-500 text-black font-black text-xs uppercase tracking-wider flex items-center gap-1.5 shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 transition-all"
            >
              <FileCheck className="w-4 h-4" />
              <span>View Story Package</span>
            </button>
          )}
          <button
            onClick={() => activeStoryId && refreshAllData(activeStoryId)}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/5 text-xs font-mono transition-colors"
            title="Refresh All State"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-[#FF6500]' : ''}`} />
          </button>
        </div>
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
          {/* Dominant Decision Card */}
          <ForgeDecisionCard
            action={currentAction?.action || 'ASK'}
            skill={currentAction?.skill || 'EXCAVATOR'}
            question={currentAction?.question}
            proposal={currentAction?.proposal}
            activeDependencyKey={currentAction?.active_dependency_key}
            activeDependencyDescription={currentAction?.active_dependency_description}
            mutations={[]}
          />

          {/* Response & Writing Panel */}
          <div className="flex-1">
            <CreatorResponsePanel
              action={currentAction?.action || 'ASK'}
              isLoading={isLoading}
              errorMessage={errorMessage}
              onSubmitResponse={handleSubmitResponse}
              onAdvanceAutonomous={handleAdvanceAutonomous}
              onRetry={() => activeStoryId && refreshAllData(activeStoryId)}
              lastCommittedVersion={storyState.state_version}
            />
          </div>
        </div>

        {/* RIGHT COLUMN: Story State, Dependencies, Intelligence & Trace (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col space-y-3">
          {/* Right Secondary Drawer Nav */}
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
              <span>Queue ({dependencies.filter(d => !['RESOLVED', 'DELIBERATELY_UNKNOWN', 'DEFERRED'].includes(d.status)).length})</span>
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

          {/* Right Viewport Content */}
          <div className="flex-1 min-h-[480px]">
            {activeRightTab === 'state' && (
              <StoryStatePanel storyState={storyState} events={events} />
            )}
            {activeRightTab === 'dependencies' && (
              <DependenciesPanel dependencies={dependencies} />
            )}
            {activeRightTab === 'intelligence' && (
              <StoryIntelligencePanel storyId={activeStoryId} />
            )}
            {activeRightTab === 'trace' && (
              <ForgeTraceInspector storyId={activeStoryId} />
            )}
          </div>
        </div>
      </div>

      {/* Completion Modal */}
      {storyState && (
        <ForgeCompletePackageModal
          isOpen={isPackageModalOpen}
          onClose={() => setIsPackageModalOpen(false)}
          storyState={storyState}
          assessment={assessment}
          events={events}
        />
      )}
    </div>
  );
};
