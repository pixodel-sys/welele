import React from 'react';
import { StoryReviewDiagnostic as DiagnosticType } from '../../../types/storyReview';
import {
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Lightbulb,
  ShieldCheck,
  Film,
  User,
  Zap,
  MapPin,
  RotateCcw
} from 'lucide-react';

interface StoryReviewDiagnosticProps {
  diagnostic: DiagnosticType;
  onEditDraft: () => void;
  onRerunDiagnostic: () => void;
  onSubmitForGreenlight: () => void;
  isDiagnosing: boolean;
}

export const StoryReviewDiagnostic: React.FC<StoryReviewDiagnosticProps> = ({
  diagnostic,
  onEditDraft,
  onRerunDiagnostic,
  onSubmitForGreenlight,
  isDiagnosing,
}) => {
  const {
    readiness_score,
    readiness_tier,
    premise_and_hook,
    character_tension,
    episodic_structure,
    production_feasibility,
    actionable_tips,
    submission_checklist,
    pitch_summary,
  } = diagnostic;

  const getTierBadge = () => {
    switch (readiness_tier) {
      case 'READY_FOR_SUBMISSION':
        return {
          label: 'Ready for Greenlight Submission',
          className: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
          dot: 'bg-emerald-400',
        };
      case 'SOLID_FOUNDATION':
        return {
          label: 'Solid Foundation — Minor Polish Recommended',
          className: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
          dot: 'bg-amber-400',
        };
      default:
        return {
          label: 'Needs Revision Before Submission',
          className: 'bg-red-500/20 text-red-300 border-red-500/30',
          dot: 'bg-red-400',
        };
    }
  };

  const tierInfo = getTierBadge();

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Overview Hero: Readiness Score & Pitch Summary */}
      <div className="p-6 rounded-[7px] bg-gradient-to-r from-welele-surface-2 via-[#181922] to-welele-surface border border-white/10 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-5 w-full md:w-auto">
          {/* Circular / Gauge Score */}
          <div className="relative w-24 h-24 rounded-full bg-black/60 border-4 border-white/10 flex flex-col items-center justify-center shrink-0 shadow-inner">
            <span className="text-3xl font-black text-white font-mono">{readiness_score}%</span>
            <span className="text-[9px] uppercase tracking-wider text-welele-muted font-bold">Readiness</span>
            <div
              className={`absolute -bottom-1 w-3 h-3 rounded-full ${tierInfo.dot} border-2 border-black animate-pulse`}
            />
          </div>

          <div className="space-y-1.5 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`px-2.5 py-0.5 rounded-[7px] text-[11px] font-extrabold border ${tierInfo.className}`}>
                {tierInfo.label}
              </span>
              {diagnostic.evaluation_mode === 'AI_ASSISTED' ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-[7px] text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                  AI-assisted assessment
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-[7px] text-[10px] font-bold bg-zinc-500/20 text-zinc-300 border border-zinc-500/30 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-zinc-400"></span>
                  Baseline assessment
                </span>
              )}
              <span className="text-[11px] text-welele-muted">
                Evaluated: {new Date(diagnostic.evaluated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <h2 className="text-lg font-black text-white">Story Review™ Diagnostic Report</h2>
            <p className="text-xs text-zinc-300 max-w-2xl leading-relaxed">
              {pitch_summary || 'Your story draft has been evaluated across editorial, character, pacing, and production dimensions.'}
            </p>
          </div>
        </div>

        {/* Primary Action Buttons */}
        <div className="flex items-center gap-2.5 w-full md:w-auto justify-end shrink-0">
          <button
            onClick={onEditDraft}
            className="px-3.5 py-2.5 rounded-[7px] bg-white/10 hover:bg-white/15 border border-white/15 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
          >
            Edit Draft
          </button>
          <button
            onClick={onRerunDiagnostic}
            disabled={isDiagnosing}
            className="px-3.5 py-2.5 rounded-[7px] bg-white/10 hover:bg-white/15 border border-white/15 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
            title="Re-run diagnostic analysis on latest draft"
          >
            <RotateCcw className={`w-3.5 h-3.5 text-welele-gold ${isDiagnosing ? 'animate-spin' : ''}`} />
            <span>Re-Analyze</span>
          </button>
          <button
            onClick={onSubmitForGreenlight}
            className="px-4 py-2.5 rounded-[7px] bg-gradient-to-r from-emerald-500 to-teal-400 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-500/20 hover:opacity-95 transition-all cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4 font-bold" />
            <span>Submit for Greenlight</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 4 Diagnostic Dimensions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Dimension 1: Premise & Hook */}
        <div className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Film className="w-4 h-4 text-welele-orange" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Premise & Hook</h3>
            </div>
            <span className="text-xs font-mono font-bold text-welele-orange">{premise_and_hook.score}/100</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
            <div className="h-full bg-welele-orange rounded-full" style={{ width: `${premise_and_hook.score}%` }} />
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed">{premise_and_hook.critique}</p>
          {premise_and_hook.strengths.length > 0 && (
            <div className="space-y-1 pt-1 border-t border-white/5">
              {premise_and_hook.strengths.map((s, i) => (
                <div key={i} className="text-[11px] text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3 h-3 shrink-0" />
                  <span>{s}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Dimension 2: Character Tension */}
        <div className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Character Tension</h3>
            </div>
            <span className="text-xs font-mono font-bold text-amber-400">{character_tension.score}/100</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
            <div className="h-full bg-amber-400 rounded-full" style={{ width: `${character_tension.score}%` }} />
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed">{character_tension.critique}</p>
          {character_tension.strengths.length > 0 && (
            <div className="space-y-1 pt-1 border-t border-white/5">
              {character_tension.strengths.map((s, i) => (
                <div key={i} className="text-[11px] text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3 h-3 shrink-0" />
                  <span>{s}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Dimension 3: Episodic Structure */}
        <div className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-pink-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Episodic Structure</h3>
            </div>
            <span className="text-xs font-mono font-bold text-pink-400">{episodic_structure.score}/100</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
            <div className="h-full bg-pink-400 rounded-full" style={{ width: `${episodic_structure.score}%` }} />
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed">{episodic_structure.critique}</p>
          {episodic_structure.strengths.length > 0 && (
            <div className="space-y-1 pt-1 border-t border-white/5">
              {episodic_structure.strengths.map((s, i) => (
                <div key={i} className="text-[11px] text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3 h-3 shrink-0" />
                  <span>{s}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Dimension 4: Production Feasibility */}
        <div className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-sky-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Production Feasibility</h3>
            </div>
            <span className="text-xs font-mono font-bold text-sky-400">{production_feasibility.score}/100</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
            <div className="h-full bg-sky-400 rounded-full" style={{ width: `${production_feasibility.score}%` }} />
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed">{production_feasibility.critique}</p>
          {production_feasibility.strengths.length > 0 && (
            <div className="space-y-1 pt-1 border-t border-white/5">
              {production_feasibility.strengths.map((s, i) => (
                <div key={i} className="text-[11px] text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3 h-3 shrink-0" />
                  <span>{s}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Actionable Tips & Submission Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Actionable Tips */}
        <div className="lg:col-span-6 space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 text-welele-gold">
            <Lightbulb className="w-3.5 h-3.5" /> Editorial Coaching & Guidance
          </h3>

          <div className="space-y-3">
            {actionable_tips.map((tip, idx) => (
              <div key={idx} className="p-3.5 rounded-[7px] bg-[#14151C] border border-white/10 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{tip.title}</span>
                  <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-bold bg-white/5 text-welele-muted border border-white/10">
                    {tip.impact_area}
                  </span>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed">{tip.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Submission Checklist */}
        <div className="lg:col-span-6 space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 text-emerald-400">
            <CheckCircle2 className="w-3.5 h-3.5" /> Submission Readiness Checklist
          </h3>

          <div className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 space-y-3">
            {submission_checklist.map((item, idx) => (
              <div key={idx} className="flex items-start gap-2.5 pb-2.5 border-b border-white/5 last:border-0 last:pb-0">
                {item.passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                )}
                <div className="space-y-0.5">
                  <span className={`text-xs font-bold ${item.passed ? 'text-white' : 'text-amber-200'}`}>
                    {item.item}
                  </span>
                  <p className="text-[11px] text-zinc-400">{item.recommendation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
