import React, { useState, useEffect } from 'react';
import { AuthorityMode } from '../../../types/storyForge';
import {
  Send,
  Check,
  X,
  Edit3,
  HelpCircle,
  RefreshCw,
  AlertCircle,
  Clock,
  Sparkles,
  ArrowRight
} from 'lucide-react';

interface CreatorResponsePanelProps {
  action: AuthorityMode;
  isLoading: boolean;
  errorMessage?: string | null;
  onSubmitResponse: (response: string, proposalAction?: 'ACCEPT' | 'REJECT' | 'MODIFY') => void;
  onAdvanceAutonomous: () => void;
  onRetry: () => void;
  lastCommittedVersion?: number;
}

export const CreatorResponsePanel: React.FC<CreatorResponsePanelProps> = ({
  action,
  isLoading,
  errorMessage,
  onSubmitResponse,
  onAdvanceAutonomous,
  onRetry,
  lastCommittedVersion,
}) => {
  const [responseText, setResponseText] = useState('');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Timer while loading
  useEffect(() => {
    let timer: any = null;
    if (isLoading) {
      setElapsedSeconds(0);
      timer = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isLoading]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!responseText.trim() && action === 'ASK') return;
    onSubmitResponse(responseText.trim());
    setResponseText('');
  };

  const handleProposalDecision = (decision: 'ACCEPT' | 'REJECT' | 'MODIFY') => {
    if (decision === 'ACCEPT') {
      onSubmitResponse(responseText.trim() || 'Accepted by creator.', 'ACCEPT');
    } else if (decision === 'REJECT') {
      onSubmitResponse(responseText.trim() || 'Proposal rejected by creator.', 'REJECT');
    } else {
      // MODIFY requires text
      if (!responseText.trim()) return;
      onSubmitResponse(responseText.trim(), 'MODIFY');
    }
    setResponseText('');
  };

  const handleMarkUnknown = () => {
    onSubmitResponse('DELIBERATELY_UNKNOWN: Creator explicitly leaves this unresolved for now.');
    setResponseText('');
  };

  return (
    <div className="w-full bg-[#12131C] border border-white/10 rounded-2xl p-4 md:p-5 shadow-2xl space-y-4">
      {/* 3 Status States: FORGE WORKING vs DECISION REQUIRED vs STATE COMMITTED */}
      <div className="flex items-center justify-between pb-3 border-b border-white/5 text-xs font-mono">
        <div className="flex items-center gap-2">
          {isLoading ? (
            <div className="flex items-center gap-2 text-[#FFA000]">
              <span className="w-2.5 h-2.5 rounded-full bg-[#FF6500] animate-ping" />
              <span className="font-bold tracking-wider uppercase">FORGE WORKING</span>
              <span className="text-white/40">• Analysing your response ({elapsedSeconds}s)</span>
            </div>
          ) : action === 'ASK' || action === 'PROPOSE' ? (
            <div className="flex items-center gap-2 text-[#FF6500]">
              <span className="w-2 h-2 rounded-full bg-[#FF6500]" />
              <span className="font-bold tracking-wider uppercase">DECISION REQUIRED</span>
              <span className="text-white/40">• Forge needs your input</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="font-bold tracking-wider uppercase">STATE COMMITTED</span>
              {lastCommittedVersion && (
                <span className="text-white/40">• Canon updated to v{lastCommittedVersion}</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Error Recovery Banner */}
      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-200 text-xs flex items-start justify-between gap-3 animate-fade-in">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <div className="font-bold text-rose-300 uppercase tracking-wider">Engine Connection Error</div>
              <p className="mt-0.5 text-white/80">{errorMessage}</p>
            </div>
          </div>
          <button
            onClick={onRetry}
            className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 font-mono text-xs font-bold border border-rose-500/30 flex items-center gap-1.5 transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
        </div>
      )}

      {/* Proposal Controls if action === 'PROPOSE' */}
      {action === 'PROPOSE' && !isLoading && (
        <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/30 space-y-3">
          <div className="text-xs text-purple-300 font-medium">
            How would you like to handle Forge's candidate proposal?
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => handleProposalDecision('ACCEPT')}
              className="px-4 py-2 rounded-xl bg-emerald-500 text-black font-bold text-xs hover:bg-emerald-400 transition-all flex items-center gap-1.5 shadow-lg shadow-emerald-500/20"
            >
              <Check className="w-4 h-4" />
              Accept Proposal
            </button>
            <button
              onClick={() => handleProposalDecision('REJECT')}
              className="px-4 py-2 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 font-bold text-xs hover:bg-rose-500/30 transition-all flex items-center gap-1.5"
            >
              <X className="w-4 h-4" />
              Reject Proposal
            </button>
            <span className="text-xs text-white/40 font-mono">or modify below:</span>
          </div>
        </div>
      )}

      {/* Writing / Input Box */}
      {(action === 'ASK' || action === 'PROPOSE') && (
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="relative">
            <textarea
              value={responseText}
              onChange={(e) => setResponseText(e.target.value)}
              disabled={isLoading}
              rows={3}
              placeholder={
                action === 'PROPOSE'
                  ? 'Optionally provide your refined direction or modifications...'
                  : 'Write your story decision naturally...'
              }
              className="w-full px-4 py-3 rounded-xl bg-black/60 border border-white/15 focus:border-[#FF6500] focus:ring-1 focus:ring-[#FF6500] text-white text-sm placeholder-white/30 resize-none transition-all outline-none font-sans"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleMarkUnknown}
                disabled={isLoading}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/50 hover:text-white/80 text-xs font-mono transition-all border border-white/5 flex items-center gap-1.5"
                title="Mark this requirement as intentionally unknown at this stage"
              >
                <HelpCircle className="w-3.5 h-3.5" />
                Leave Unknown
              </button>
            </div>

            <div className="flex items-center gap-2">
              {action === 'PROPOSE' && responseText.trim() && (
                <button
                  type="button"
                  onClick={() => handleProposalDecision('MODIFY')}
                  disabled={isLoading}
                  className="px-4 py-2 rounded-xl bg-purple-500 hover:bg-purple-400 text-black font-bold text-xs transition-all flex items-center gap-1.5"
                >
                  <Edit3 className="w-4 h-4" />
                  Submit Modified Direction
                </button>
              )}

              {action === 'ASK' && (
                <button
                  type="submit"
                  disabled={isLoading || !responseText.trim()}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#FF6500] to-[#FF8500] hover:from-[#FF7500] hover:to-[#FF9500] disabled:opacity-40 disabled:pointer-events-none text-black font-black text-xs uppercase tracking-wider transition-all flex items-center gap-2 shadow-lg shadow-[#FF6500]/25 active:scale-98"
                >
                  <span>Submit Decision</span>
                  <Send className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        </form>
      )}

      {/* Autonomous Advance when Action is INFER or RECORD_PRODUCTION_DECISION */}
      {(action === 'INFER' || action === 'RECORD_PRODUCTION_DECISION' || action === 'STOP') && (
        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-white/60">
            {action === 'STOP' ? 'Judge assessment complete.' : 'State committed. Ready for next cycle.'}
          </div>
          <button
            onClick={onAdvanceAutonomous}
            disabled={isLoading}
            className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-bold text-xs transition-all border border-white/15 flex items-center gap-2"
          >
            <span>Advance Next Step</span>
            <ArrowRight className="w-3.5 h-3.5 text-[#FF6500]" />
          </button>
        </div>
      )}
    </div>
  );
};
