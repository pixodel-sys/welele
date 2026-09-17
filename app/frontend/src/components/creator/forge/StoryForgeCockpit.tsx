import React, { useState, useEffect } from 'react';
import { storyForgeApi } from '../../../services/storyForgeApi';
import {
  StoryState,
  CurrentAction,
  Dependency,
  ForgeCompletionAssessment,
  ChronologyEvent
} from '../../../types/storyForge';
import { CreatorStoryStudio } from './CreatorStoryStudio';
import { OperatorDiagnosticConsole } from './OperatorDiagnosticConsole';
import { ForgeCompletePackageModal } from './ForgeCompletePackageModal';
import { StoryIntakeScreen } from './StoryIntakeScreen';
import {
  Sparkles,
  ArrowLeft,
  RefreshCw,
  FileCheck,
  Terminal,
  Palette
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

  // View Mode: 'creator' (Default, human-centered) vs 'operator' (Diagnostic tooling)
  const [viewMode, setViewMode] = useState<'creator' | 'operator'>('creator');

  // Loading & Working States
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isWorkingThroughStory, setIsWorkingThroughStory] = useState<boolean>(false);
  const [workingStatusMessage, setWorkingStatusMessage] = useState<string>(
    'Working through your story… Checking how this answer affects the characters and story arc.'
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPackageModalOpen, setIsPackageModalOpen] = useState<boolean>(false);

  // Initialize or resume session
  const initializeSession = async (
    storyId: string,
    initialPremise?: string,
    creativeObjective?: string,
    productionObjective?: string
  ) => {
    setActiveStoryId(storyId);
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const sess = await storyForgeApi.startSession(storyId, {
        creator_id: 'creator_current',
        initial_premise: initialPremise,
        creative_objective: creativeObjective,
        production_objective: productionObjective,
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

  // Submit creator input with automatic transition collapsing
  const handleSubmitResponse = async (
    responseText: string,
    proposalAction?: 'ACCEPT' | 'REJECT' | 'MODIFY'
  ) => {
    if (!sessionId || !activeStoryId) return;

    setIsLoading(true);
    setIsWorkingThroughStory(true);
    setWorkingStatusMessage('Working through your story… Checking how this answer affects the characters and story arc.');
    setErrorMessage(null);

    try {
      const cycleResult = await storyForgeApi.submitInput(sessionId, {
        creator_response: responseText,
        proposal_action: proposalAction,
      });

      setStoryState(cycleResult.current_state);

      // Refresh current action & completion
      let actionData = await storyForgeApi.getCurrentAction(sessionId);
      let compData = await storyForgeApi.getCompletion(activeStoryId);
      setCurrentAction(actionData);
      setAssessment(compData);

      // Autonomous transition collapsing:
      // If the action does not require creator authority (e.g. INFER, RECORD_PRODUCTION_DECISION)
      // and has not reached terminal completion, advance automatically without disrupting creator.
      let safetyLoops = 0;
      while (
        safetyLoops < 8 &&
        compData.status !== 'FORGE_COMPLETE' &&
        actionData.action !== 'STOP' &&
        !actionData.requires_creator &&
        actionData.action !== 'ASK' &&
        actionData.action !== 'PROPOSE'
      ) {
        safetyLoops++;
        setWorkingStatusMessage('Synthesizing dramatic continuity and updating story arc…');
        await new Promise((resolve) => setTimeout(resolve, 400));

        const autoRes = await storyForgeApi.submitInput(sessionId, {});
        setStoryState(autoRes.current_state);

        actionData = await storyForgeApi.getCurrentAction(sessionId);
        compData = await storyForgeApi.getCompletion(activeStoryId);
        setCurrentAction(actionData);
        setAssessment(compData);
      }

      await refreshAllData(activeStoryId, sessionId);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Error processing story cycle.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
      setIsWorkingThroughStory(false);
    }
  };

  // Advance single autonomous step (manual trigger for operator console)
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
        onStoryCreated={(id, premise, creativeObj, prodObj) =>
          initializeSession(id, premise, creativeObj, prodObj)
        }
        onResumeStory={(id) => initializeSession(id)}
      />
    );
  }

  const isForgeComplete = assessment?.status === 'FORGE_COMPLETE';

  return (
    <div className="max-w-7xl mx-auto py-4 px-3 sm:px-5 space-y-5 font-sans text-white">
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
                Story Forge™
              </span>
              <span className="text-xs font-mono text-white/40">v{storyState.state_version}</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight font-sans">
              {storyState.title}
            </h1>
          </div>
        </div>

        {/* Center/Right: View Mode Toggle & Actions */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Creator vs Operator Console Toggle */}
          <div className="flex items-center p-1 rounded-xl bg-black/60 border border-white/10 text-xs font-mono">
            <button
              onClick={() => setViewMode('creator')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5 ${
                viewMode === 'creator'
                  ? 'bg-[#FF6500] text-black shadow-md shadow-[#FF6500]/25'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <Palette className="w-3.5 h-3.5" />
              <span>Creator Studio</span>
            </button>
            <button
              onClick={() => setViewMode('operator')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5 ${
                viewMode === 'operator'
                  ? 'bg-white/20 text-white shadow-md'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Operator Console</span>
            </button>
          </div>

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

      {/* Primary Experience Surface */}
      {viewMode === 'creator' ? (
        <CreatorStoryStudio
          sessionId={sessionId!}
          storyState={storyState}
          currentAction={currentAction}
          assessment={assessment}
          events={events}
          isLoading={isLoading}
          isWorkingThroughStory={isWorkingThroughStory}
          workingStatusMessage={workingStatusMessage}
          errorMessage={errorMessage}
          onSubmitResponse={handleSubmitResponse}
          onViewStoryPackage={() => setIsPackageModalOpen(true)}
          onOpenOperatorConsole={() => setViewMode('operator')}
        />
      ) : (
        <OperatorDiagnosticConsole
          activeStoryId={activeStoryId}
          storyState={storyState}
          currentAction={currentAction}
          dependencies={dependencies}
          events={events}
          assessment={assessment}
          isLoading={isLoading}
          errorMessage={errorMessage}
          onSubmitResponse={handleSubmitResponse}
          onAdvanceAutonomous={handleAdvanceAutonomous}
          onRetry={() => activeStoryId && refreshAllData(activeStoryId)}
        />
      )}

      {/* Certified Completion Modal */}
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
