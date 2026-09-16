import React, { useState, useEffect } from 'react';
import { storyForgeApi } from '../../../services/storyForgeApi';
import { IntelligenceProjection } from '../../../types/storyForge';
import {
  Brain,
  ShieldCheck,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Cpu,
  RefreshCw
} from 'lucide-react';

interface StoryIntelligencePanelProps {
  storyId: string;
}

export const StoryIntelligencePanel: React.FC<StoryIntelligencePanelProps> = ({ storyId }) => {
  const [intelligence, setIntelligence] = useState<IntelligenceProjection | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchIntelligence = async () => {
    if (!storyId) return;
    setIsLoading(true);
    try {
      const data = await storyForgeApi.getIntelligence(storyId);
      setIntelligence(data);
    } catch (e) {
      console.warn('Could not fetch story intelligence projection:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchIntelligence();
  }, [storyId]);

  if (isLoading && !intelligence) {
    return (
      <div className="p-8 text-center text-xs text-white/40 font-mono">
        <RefreshCw className="w-4 h-4 animate-spin mx-auto mb-2 text-[#FF6500]" />
        Projecting story intelligence...
      </div>
    );
  }

  if (!intelligence) {
    return (
      <div className="p-8 text-center text-xs text-white/40 font-mono">
        Intelligence projection unavailable.
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-[#12131C] border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
      {/* Top Header */}
      <div className="p-3.5 border-b border-white/5 bg-black/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-[#FF6500]" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
            Story Intelligence Projection
          </h3>
        </div>
        <button
          onClick={fetchIntelligence}
          disabled={isLoading}
          className="text-xs text-white/50 hover:text-white flex items-center gap-1"
        >
          <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
          <span className="text-[10px] font-mono">Update</span>
        </button>
      </div>

      <div className="flex-1 p-4 overflow-y-auto space-y-4 custom-scrollbar text-xs">
        {/* Core Understanding Summary */}
        <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-white/40 block">
            Core Grounded Narrative Understanding
          </span>
          <div className="space-y-1 text-white/80">
            <div>
              <span className="text-white/40 font-mono">Protagonist:</span>{' '}
              {intelligence.core_understanding.protagonists.join(', ') || 'Unresolved'}
            </div>
            <div>
              <span className="text-white/40 font-mono">Opposing Force:</span>{' '}
              {intelligence.core_understanding.antagonists.join(', ') || 'Unresolved'}
            </div>
            <div>
              <span className="text-white/40 font-mono">Spine Anchors:</span>{' '}
              {intelligence.core_understanding.chronology_anchors_count} of 6 committed
            </div>
          </div>
        </div>

        {/* Strengths */}
        <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-2">
          <div className="flex items-center gap-1.5 text-emerald-400 font-bold font-mono text-[11px] uppercase">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Established Canon Strengths ({intelligence.strengths.length})</span>
          </div>
          {intelligence.strengths.length > 0 ? (
            <ul className="space-y-1 text-white/80 list-disc list-inside text-[11px]">
              {intelligence.strengths.map((s, idx) => (
                <li key={idx} className="leading-relaxed">{s}</li>
              ))}
            </ul>
          ) : (
            <p className="text-white/40 text-[11px] font-mono">Establishing preliminary story pillars...</p>
          )}
        </div>

        {/* Unresolved Risks */}
        <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/30 space-y-2">
          <div className="flex items-center gap-1.5 text-amber-400 font-bold font-mono text-[11px] uppercase">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Unresolved Narrative Invariants ({intelligence.unresolved_risks.length})</span>
          </div>
          {intelligence.unresolved_risks.length > 0 ? (
            <ul className="space-y-1 text-white/80 list-disc list-inside text-[11px]">
              {intelligence.unresolved_risks.map((r, idx) => (
                <li key={idx} className="leading-relaxed">{r}</li>
              ))}
            </ul>
          ) : (
            <p className="text-emerald-400 text-[11px] font-mono">All primary invariants satisfied for current milestone.</p>
          )}
        </div>

        {/* Next Needed Decisions */}
        <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-white/40 block">
            Next Prioritized Forge Focus
          </span>
          <div className="space-y-1.5">
            {intelligence.next_needed_decisions.map((item, idx) => (
              <div key={idx} className="p-2 rounded-lg bg-black/60 border border-white/5 text-[11px]">
                <div className="flex items-center justify-between text-[#FFA000] font-mono font-bold">
                  <span>{item.key}</span>
                  <span className="text-white/40 text-[9px]">{item.suggested_skill}</span>
                </div>
                <p className="text-white/70 mt-0.5">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
