import React, { useState } from 'react';
import { AuthorityMode, SkillEnum, StateMutation } from '../../../types/storyForge';
import {
  HelpCircle,
  Sparkles,
  GitPullRequest,
  CheckCircle,
  FileCheck,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Cpu,
  Layers,
  Flame,
  Info
} from 'lucide-react';

interface ForgeDecisionCardProps {
  action: AuthorityMode;
  skill: SkillEnum;
  question?: string | null;
  proposal?: string | null;
  interpretation?: string | null;
  activeDependencyKey?: string | null;
  activeDependencyDescription?: string | null;
  confidence?: number;
  latencyMs?: number | null;
  mutations?: StateMutation[];
}

export const ForgeDecisionCard: React.FC<ForgeDecisionCardProps> = ({
  action,
  skill,
  question,
  proposal,
  interpretation,
  activeDependencyKey,
  activeDependencyDescription,
  confidence,
  latencyMs,
  mutations = [],
}) => {
  const [showDetails, setShowDetails] = useState(false);

  const getActionBadge = () => {
    switch (action) {
      case 'ASK':
        return {
          label: 'FORGE ASKS',
          sub: 'Creative authority decision required',
          color: 'bg-[#FF6500]/15 text-[#FF6500] border-[#FF6500]/40',
          icon: <HelpCircle className="w-4 h-4 text-[#FF6500]" />,
        };
      case 'PROPOSE':
        return {
          label: 'FORGE PROPOSES',
          sub: 'Candidate resolution awaiting creator sign-off',
          color: 'bg-purple-500/15 text-purple-300 border-purple-500/40',
          icon: <GitPullRequest className="w-4 h-4 text-purple-400" />,
        };
      case 'INFER':
        return {
          label: 'FORGE INFERRED',
          sub: 'Derived safely from confirmed canon',
          color: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
          icon: <CheckCircle className="w-4 h-4 text-emerald-400" />,
        };
      case 'RECORD_PRODUCTION_DECISION':
        return {
          label: 'PRODUCTION DECISION',
          sub: 'Physical staging constraint anchored',
          color: 'bg-blue-500/15 text-blue-300 border-blue-500/40',
          icon: <FileCheck className="w-4 h-4 text-blue-400" />,
        };
      case 'STOP':
        return {
          label: 'FORGE COMPLETE / STOP',
          sub: 'Judge-governed completion boundary',
          color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50',
          icon: <Sparkles className="w-4 h-4 text-emerald-400" />,
        };
      default:
        return {
          label: 'DECISION REQUIRED',
          sub: 'Story development cycle',
          color: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
        };
    }
  };

  const badge = getActionBadge();
  const mainDisplayText = question || proposal || (action === 'INFER' ? interpretation : 'Forge is analyzing narrative state...');

  return (
    <div className="relative rounded-2xl bg-gradient-to-b from-[#161822] to-[#0F1017] border border-white/10 p-5 md:p-6 shadow-2xl overflow-hidden transition-all">
      {/* Subtle glowing ambient backdrop */}
      <div className="absolute -top-24 -right-24 w-56 h-56 bg-[#FF6500]/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-56 h-56 bg-[#D8005A]/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Meta Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        {/* Authority Mode Badge */}
        <div className="flex items-center gap-2">
          <div className={`px-3 py-1 rounded-full border text-xs font-mono font-bold flex items-center gap-1.5 ${badge.color}`}>
            {badge.icon}
            <span>{badge.label}</span>
          </div>
          <span className="hidden sm:inline text-xs text-white/50 font-sans">{badge.sub}</span>
        </div>

        {/* Skill & Latency */}
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-0.5 rounded bg-white/5 border border-white/10 text-[11px] font-mono text-white/70 font-semibold flex items-center gap-1">
            <Cpu className="w-3 h-3 text-[#FF6500]" />
            {skill}
          </span>
          {latencyMs != null && (
            <span className="text-[10px] font-mono text-white/40">
              {Math.round(latencyMs)}ms
            </span>
          )}
        </div>
      </div>

      {/* Dominant Question / Proposal Element */}
      <div className="my-2">
        <h2 className="text-xl sm:text-2xl md:text-3xl font-black text-white tracking-tight leading-snug font-sans selection:bg-[#FF6500] selection:text-black">
          {mainDisplayText}
        </h2>
      </div>

      {/* Proposal Details if PROPOSE */}
      {action === 'PROPOSE' && proposal && question && (
        <div className="mt-3 p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/30 text-purple-200 text-sm">
          <div className="text-[11px] font-mono font-bold text-purple-400 uppercase tracking-wider mb-1">
            Candidate Direction:
          </div>
          <p className="leading-relaxed">{proposal}</p>
        </div>
      )}

      {/* State Changes Preview (for INFER / PROPOSE) */}
      {mutations.length > 0 && (
        <div className="mt-4 p-3 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
          <div className="text-[10px] font-mono uppercase tracking-wider text-white/40 font-semibold">
            Proposed Canonical Mutations ({mutations.length}):
          </div>
          {mutations.map((m, idx) => (
            <div key={idx} className="text-xs font-mono flex items-start gap-2 text-emerald-300/90">
              <span className="text-[#FF6500] font-bold">[{m.mutation_type}]</span>
              <span className="text-white/80">{m.target_path}</span>
              {m.rationale && <span className="text-white/40 italic">— {m.rationale}</span>}
            </div>
          ))}
        </div>
      )}

      {/* "Why Forge is Asking" Context Accordion */}
      <div className="mt-4 pt-3 border-t border-white/5">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center justify-between w-full text-left text-xs text-white/60 hover:text-white transition-colors"
        >
          <div className="flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-[#FF6500]" />
            <span className="font-semibold text-white/80">Why Forge needs this decision</span>
          </div>
          {showDetails ? (
            <ChevronUp className="w-4 h-4 text-white/40" />
          ) : (
            <ChevronDown className="w-4 h-4 text-white/40" />
          )}
        </button>

        {showDetails && (
          <div className="mt-3 p-3 rounded-xl bg-black/50 border border-white/5 space-y-2 text-xs text-white/70 animate-fade-in">
            {activeDependencyKey && (
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-bold text-white/40 uppercase">Active Dependency:</span>
                <span className="font-mono text-[#FFA000] font-semibold">{activeDependencyKey}</span>
              </div>
            )}
            {activeDependencyDescription && (
              <div>
                <span className="text-[10px] font-mono font-bold text-white/40 uppercase block mb-0.5">Deficiency Description:</span>
                <p className="leading-relaxed text-white/80">{activeDependencyDescription}</p>
              </div>
            )}
            {interpretation && (
              <div>
                <span className="text-[10px] font-mono font-bold text-white/40 uppercase block mb-0.5">Kernel Interpretation:</span>
                <p className="leading-relaxed text-white/80 italic">"{interpretation}"</p>
              </div>
            )}
            {confidence != null && (
              <div className="text-[10px] font-mono text-white/40 pt-1">
                Reasoning Confidence: {(confidence * 100).toFixed(0)}%
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
