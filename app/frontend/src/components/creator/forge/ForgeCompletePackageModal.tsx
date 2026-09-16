import React, { useState } from 'react';
import { StoryState, ForgeCompletionAssessment, ChronologyEvent } from '../../../types/storyForge';
import {
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Download,
  Copy,
  Check,
  X,
  Clapperboard,
  BookOpen,
  Users,
  Clock,
  Layers
} from 'lucide-react';

interface ForgeCompletePackageModalProps {
  isOpen: boolean;
  onClose: () => void;
  storyState: StoryState;
  assessment?: ForgeCompletionAssessment | null;
  events?: ChronologyEvent[];
}

export const ForgeCompletePackageModal: React.FC<ForgeCompletePackageModalProps> = ({
  isOpen,
  onClose,
  storyState,
  assessment,
  events = [],
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const characters = Object.values(storyState.characters || {});

  const handleCopyPackage = () => {
    const jsonStr = JSON.stringify(
      {
        story_package_version: '0.2.0',
        title: storyState.title,
        logline: storyState.logline,
        milestone: 'M3_FORGE_COMPLETE',
        characters: characters,
        world: storyState.world,
        chronology_spine: events,
        narrative_plants: storyState.plants,
        assessment: assessment,
      },
      null,
      2
    );
    navigator.clipboard.writeText(jsonStr);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJSON = () => {
    const jsonStr = JSON.stringify(
      {
        story_package_version: '0.2.0',
        title: storyState.title,
        logline: storyState.logline,
        characters: characters,
        world: storyState.world,
        chronology_spine: events,
        narrative_plants: storyState.plants,
        assessment: assessment,
      },
      null,
      2
    );
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${storyState.title.toLowerCase().replace(/[^a-z0-9]/g, '_')}_story_package.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto animate-fade-in">
      <div className="bg-[#12131C] border border-emerald-500/50 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-6 bg-gradient-to-r from-emerald-950/40 via-emerald-900/20 to-black border-b border-emerald-500/30 flex items-start justify-between">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-mono font-bold uppercase">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>🟢 FORGE COMPLETE (M3 Certified)</span>
            </div>
            <h2 className="text-2xl font-black text-white font-sans tracking-tight">
              {storyState.title}
            </h2>
            <p className="text-xs text-white/70">
              This Story Package has satisfied all canonical narrative, structural, and continuity invariants.
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/50 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6 text-xs text-white/80 custom-scrollbar font-sans">
          {/* PILLAR 1: STORY BIBLE */}
          <div className="p-4 rounded-xl bg-black/40 border border-white/10 space-y-1.5">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#FF6500] block flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5" />
              <span>1. Canonical Story Bible</span>
            </span>
            <p className="text-sm font-medium text-white leading-relaxed">{storyState.logline}</p>
          </div>

          {/* PILLAR 2: CHARACTER BIBLE */}
          <div className="space-y-2">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white/60 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-[#FF6500]" />
              <span>2. Cast & Character Bible ({characters.length} Roles)</span>
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {characters.map((c) => (
                <div key={c.name} className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm">{c.name}</span>
                    <span className="px-2 py-0.5 rounded bg-white/10 text-[10px] font-mono font-bold text-[#FFA000]">
                      {c.role}
                    </span>
                  </div>
                  {c.core_motivation && (
                    <p className="text-[11px] text-white/70">{c.core_motivation}</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* PILLAR 3: WORLD & RULES */}
          {storyState.world && (
            <div className="space-y-2">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white/60 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-[#FFA000]" />
                <span>3. World & Inviolable Invariants</span>
              </h4>
              <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1">
                <div className="font-bold text-white text-xs">{storyState.world.arena || 'Township / Urban South Africa'}</div>
                {storyState.world.rules_and_lore && storyState.world.rules_and_lore.length > 0 && (
                  <p className="text-[11px] text-white/70">{storyState.world.rules_and_lore.join(' • ')}</p>
                )}
              </div>
            </div>
          )}

          {/* PILLAR 4: CHRONOLOGY */}
          <div className="space-y-2">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white/60 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-emerald-400" />
              <span>4. Canonical Chronology Spine ({events.length} Anchors)</span>
            </h4>
            <div className="space-y-2">
              {events.map((ev) => (
                <div key={ev.event_sequence} className="p-3 rounded-xl bg-black/40 border border-white/5 flex items-start gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                    {ev.event_sequence}
                  </span>
                  <div>
                    <div className="font-bold text-white text-xs">{ev.headline}</div>
                    <div className="text-[11px] text-white/60 mt-0.5">{ev.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* PILLAR 5: EPISODE ARCHITECTURE */}
          <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#FF6500] block">
              5. Episode Architecture & Target Pacing
            </span>
            <p className="text-xs text-white/80">
              60–90s vertical microdrama episodic beats with cliffhanger paywall trigger points.
            </p>
          </div>

          {/* PILLAR 6: NARRATIVE PLANTS & PAYOFFS */}
          {storyState.plants && storyState.plants.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white/60 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#FFA000]" />
                <span>6. Narrative Plants & Payoffs ({storyState.plants.length})</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {storyState.plants.map((p, i) => (
                  <div key={i} className="p-2.5 rounded-xl bg-black/40 border border-white/5 flex items-center justify-between">
                    <span className="text-white font-bold text-xs">{p.plant_name || p.element_code}</span>
                    <span className="text-[10px] font-mono text-welele-gold">{p.payoff_status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* PILLAR 7: PRODUCTION CONSTRAINTS */}
          <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#FF6500] block">
              7. Production Constraints
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-white/70 font-mono pt-1">
              <div>Format: <strong className="text-white">9:16 Vertical</strong></div>
              <div>Locations: <strong className="text-white">2 Core Sets</strong></div>
              <div>Cast: <strong className="text-white">{characters.length} Roles</strong></div>
              <div>Audio: <strong className="text-white">African Vernacular</strong></div>
            </div>
          </div>

          {/* PILLAR 8: FORGE PROVENANCE */}
          <div className="p-3.5 rounded-xl bg-black/60 border border-[#FF6500]/30 space-y-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#FF6500] block flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>8. Forge Provenance & Cryptographic Lineage</span>
            </span>
            <div className="flex items-center justify-between text-xs font-mono text-white/70 pt-1">
              <span>Configuration: <strong className="text-[#FF6500]">CFG-001</strong> (Frozen Baseline)</span>
              <span className="text-emerald-400 font-bold">● Validated by ForgeJudge</span>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-black/60 border-t border-white/5 flex items-center justify-between">
          <div className="text-[11px] font-mono text-white/40">
            Validated by ForgeJudge v0.2.0
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyPackage}
              className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-white font-bold text-xs flex items-center gap-1.5 transition-all"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied JSON' : 'Copy Package JSON'}</span>
            </button>
            <button
              onClick={handleDownloadJSON}
              className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs flex items-center gap-1.5 transition-all shadow-lg shadow-emerald-500/20"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Package</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
