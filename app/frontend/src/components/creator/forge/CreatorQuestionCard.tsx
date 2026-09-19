import React, { useState, useEffect } from 'react';
import { CurrentAction, StoryState } from '../../../types/storyForge';
import { translateCreatorQuestion } from '../../../utils/creatorVocabulary';
import {
  Sparkles,
  ArrowRight,
  HelpCircle,
  Lightbulb,
  Info,
  ChevronDown,
  ChevronUp,
  Check,
  Edit3,
  Compass
} from 'lucide-react';

interface CreatorQuestionCardProps {
  currentAction: CurrentAction | null;
  storyState: StoryState | null;
  isLoading: boolean;
  errorMessage: string | null;
  onSubmit: (response: string, proposalAction?: 'ACCEPT' | 'REJECT' | 'MODIFY') => void;
}

export const CreatorQuestionCard: React.FC<CreatorQuestionCardProps> = ({
  currentAction,
  storyState,
  isLoading,
  errorMessage,
  onSubmit,
}) => {
  const [answer, setAnswer] = useState('');
  const [showCraftDetails, setShowCraftDetails] = useState(false);
  const [selectedProposalAction, setSelectedProposalAction] = useState<'ACCEPT' | 'MODIFY' | null>(null);
  const [isLocallySubmitting, setIsLocallySubmitting] = useState(false);
  const lastQuestionKeyRef = React.useRef<string | null>(null);

  const isLocked = isLoading || isLocallySubmitting;

  const translated = translateCreatorQuestion(currentAction, storyState);
  const isProposal = currentAction?.action === 'PROPOSE' && !!currentAction.proposal;

  useEffect(() => {
    if (!isLoading) {
      setIsLocallySubmitting(false);
    }
  }, [isLoading]);

  useEffect(() => {
    // Only reset local answer draft when the active question key genuinely changes to a different question
    const currentKey = currentAction?.active_dependency_key || currentAction?.question || null;
    if (currentKey && lastQuestionKeyRef.current !== null && lastQuestionKeyRef.current !== currentKey) {
      setAnswer('');
      setSelectedProposalAction(null);
    }
    if (currentKey) {
      lastQuestionKeyRef.current = currentKey;
    }
  }, [currentAction?.active_dependency_key, currentAction?.question]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (isLocked) return;

    if (isProposal && selectedProposalAction === 'ACCEPT') {
      setIsLocallySubmitting(true);
      onSubmit(answer.trim() || (currentAction?.proposal || 'Accepted candidate direction'), 'ACCEPT');
      return;
    }

    if (!answer.trim() && !isProposal) return;
    setIsLocallySubmitting(true);
    onSubmit(answer.trim(), selectedProposalAction || undefined);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };


  return (
    <div className="relative rounded-3xl bg-gradient-to-b from-[#161824] to-[#0D0E15] border border-white/10 p-6 sm:p-8 shadow-2xl overflow-hidden transition-all">
      {/* Ambient background glows */}
      <div className="absolute -top-32 -right-32 w-72 h-72 bg-[#FF6500]/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 -left-32 w-72 h-72 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Synopsis Understanding & Category pill */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#FFA000]">
            <Compass className="w-3.5 h-3.5 text-[#FF6500]" />
            <span>{translated.category}</span>
          </div>
          {storyState?.title && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
              <Sparkles className="w-3 h-3" />
              <span>Premise Understood</span>
            </div>
          )}
        </div>

        <span className="text-[11px] font-mono text-white/40">
          Press <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-white/70">Ctrl + Enter</kbd> to continue
        </span>
      </div>

      {/* Dominant Creator Question Headline */}
      <div className="space-y-2 mb-6">
        <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight leading-snug font-sans">
          {translated.headline}
        </h2>
        <p className="text-sm sm:text-base text-white/70 leading-relaxed max-w-3xl">
          {translated.context}
        </p>
      </div>

      {/* Why This Matters Context Card */}
      <div className="mb-6 p-4 rounded-2xl bg-white/[0.03] border border-white/5 flex items-start gap-3 text-xs text-white/80 leading-relaxed">
        <Lightbulb className="w-4 h-4 text-[#FFA000] shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-white block mb-0.5">Why this matters:</span>
          <span>{translated.whyItMatters}</span>
        </div>
      </div>

      {/* Candidate Proposal UI if in PROPOSE Mode */}
      {isProposal && (
        <div className="mb-6 p-5 rounded-2xl bg-purple-950/20 border border-purple-500/30 space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-purple-300 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>Story Forge Suggestion</span>
          </div>
          <p className="text-sm text-purple-100/90 leading-relaxed italic">
            "{currentAction.proposal}"
          </p>

          <div className="flex flex-wrap items-center gap-2 pt-2">
            <button
              type="button"
              disabled={isLocked}
              onClick={() => setSelectedProposalAction('ACCEPT')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                isLocked ? 'opacity-40 cursor-not-allowed pointer-events-none' : ''
              } ${
                selectedProposalAction === 'ACCEPT'
                  ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/25'
                  : 'bg-white/5 hover:bg-white/10 text-white/80'
              }`}
            >
              <Check className="w-3.5 h-3.5" />
              <span>Accept Direction</span>
            </button>
            <button
              type="button"
              disabled={isLocked}
              onClick={() => setSelectedProposalAction('MODIFY')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                isLocked ? 'opacity-40 cursor-not-allowed pointer-events-none' : ''
              } ${
                selectedProposalAction === 'MODIFY'
                  ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/25'
                  : 'bg-white/5 hover:bg-white/10 text-white/80'
              }`}
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>Modify or Elaborate Below</span>
            </button>
          </div>
        </div>
      )}

      {/* Creator Input Form */}
      <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
        <div>
          <textarea
            id="creator-story-response-input"
            name="creatorStoryResponse"
            value={answer}
            onChange={(e) => {
              setAnswer(e.target.value);
            }}
            onKeyDown={handleKeyDown}
            rows={4}
            disabled={isLocked}
            autoFocus={!isLocked}
            spellCheck={true}
            placeholder={
              isLocked
                ? 'Forge is processing your answer…'
                : isProposal && selectedProposalAction === 'ACCEPT'
                ? 'Using accepted direction (or add fine details)...'
                : translated.inputPlaceholder
            }
            className={`w-full px-5 py-4 rounded-2xl bg-black/60 border border-white/20 text-white text-sm sm:text-base placeholder-white/30 outline-none transition-all resize-none leading-relaxed relative z-20 ${
              isLocked
                ? 'opacity-50 cursor-not-allowed bg-black/40 border-white/10'
                : 'focus:border-[#FF6500] focus:ring-2 focus:ring-[#FF6500]/30 cursor-text pointer-events-auto'
            }`}
          />
        </div>


        {errorMessage && (
          <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-200 text-xs">
            {errorMessage}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
          {/* Subtle collapsible craft info */}
          <button
            type="button"
            onClick={() => setShowCraftDetails(!showCraftDetails)}
            className="inline-flex items-center gap-1.5 text-xs text-white/40 hover:text-white/70 transition-colors"
          >
            <Info className="w-3.5 h-3.5" />
            <span>Story craft details</span>
            {showCraftDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {/* Primary Continue Button */}
          <button
            type="submit"
            disabled={isLocked || (!answer.trim() && !(isProposal && selectedProposalAction === 'ACCEPT'))}
            className="px-7 py-3 rounded-2xl bg-gradient-to-r from-[#FF6500] to-[#FF8500] hover:from-[#FF7500] hover:to-[#FF9500] disabled:opacity-35 disabled:cursor-not-allowed text-black font-black text-xs uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-xl shadow-[#FF6500]/20 active:scale-98"
          >
            <span>{isLocked ? 'Processing…' : 'Continue'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>

      {/* Optional Collapsed Craft Details Accordion */}
      {showCraftDetails && (
        <div className="mt-4 pt-4 border-t border-white/5 space-y-2 text-xs text-white/60 font-sans">
          <div className="flex items-center gap-2">
            <span className="font-mono text-white/40 uppercase text-[10px]">What we're shaping:</span>
            <span className="text-white/80">{translated.behindTheScenes.narrativeAspect}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-white/40 uppercase text-[10px]">Creative Focus:</span>
            <span className="px-2 py-0.5 rounded bg-white/5 text-[#FFA000] font-mono text-[11px]">
              {translated.behindTheScenes.skill}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
