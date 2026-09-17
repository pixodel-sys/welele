import React from 'react';
import { StoryState, ForgeCompletionAssessment, ChronologyEvent } from '../../../types/storyForge';
import {
  Sparkles,
  CheckCircle2,
  FileCheck,
  ArrowRight,
  Clapperboard,
  BookOpen,
  Users,
  Film,
  Terminal,
  Layers
} from 'lucide-react';

interface ForgeCompleteScreenProps {
  storyState: StoryState;
  assessment: ForgeCompletionAssessment | null;
  events: ChronologyEvent[];
  onViewStoryPackage: () => void;
  onContinueToEpisodePlanning?: () => void;
  onOpenOperatorConsole?: () => void;
}

export const ForgeCompleteScreen: React.FC<ForgeCompleteScreenProps> = ({
  storyState,
  assessment,
  events,
  onViewStoryPackage,
  onContinueToEpisodePlanning,
  onOpenOperatorConsole,
}) => {
  const charactersList = Object.values(storyState.characters);
  const protagonists = charactersList.filter((c) => c.role === 'PROTAGONIST');
  const antagonists = charactersList.filter((c) => c.role === 'ANTAGONIST');
  const supporting = charactersList.filter((c) => c.role !== 'PROTAGONIST' && c.role !== 'ANTAGONIST');

  const completionChecklist = [
    { label: 'Story foundation', detail: 'Premise, genre, and arena locked' },
    { label: 'Characters', detail: `${charactersList.length} cast members with core motivations` },
    { label: 'Core conflict', detail: 'Central dilemma and opposing force anchored' },
    { label: 'Dramatic engine', detail: 'Protagonist-counterforce tension active' },
    { label: 'Story arc', detail: `${events.length || 6} canonical chronology turning points` },
    { label: 'Continuity', detail: 'Knowledge states and narrative plants tracked' },
    { label: 'Required production context', detail: 'Format staging and camera parameters aligned' },
  ];

  return (
    <div className="relative rounded-3xl bg-gradient-to-b from-[#121A24] via-[#0D121B] to-[#0A0D14] border-2 border-emerald-500/40 p-6 sm:p-10 shadow-2xl overflow-hidden animate-fade-in text-white">
      {/* Radiant celebratory glow */}
      <div className="absolute -top-40 -right-40 w-96 h-96 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-[#FF6500]/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Badge */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-mono text-xs font-bold uppercase tracking-wider">
          <Sparkles className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span>M3 Certified • Story Forge Complete</span>
        </div>

        <span className="text-xs font-mono text-emerald-400/80 bg-emerald-950/40 px-3 py-1 rounded-lg border border-emerald-500/30">
          v{storyState.state_version} Canon
        </span>
      </div>

      {/* Main Celebration Headline */}
      <div className="space-y-3 mb-8">
        <h1 className="text-3xl sm:text-5xl font-black tracking-tight font-sans text-white">
          STORY FORGED
        </h1>
        <p className="text-base sm:text-lg text-emerald-200/90 font-medium max-w-2xl leading-relaxed">
          Your story has been developed into a structured, production-ready Story Package.
        </p>
      </div>

      {/* Story Summary Capsule */}
      <div className="mb-8 p-5 sm:p-6 rounded-2xl bg-black/40 border border-white/10 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <span className="text-[11px] font-mono text-white/40 uppercase block mb-1">Story Title</span>
          <h3 className="text-lg font-bold text-white tracking-tight">{storyState.title}</h3>
        </div>
        <div className="md:col-span-2">
          <span className="text-[11px] font-mono text-white/40 uppercase block mb-1">Established Logline</span>
          <p className="text-xs sm:text-sm text-white/80 leading-relaxed italic">"{storyState.logline}"</p>
        </div>
      </div>

      {/* Concise Completion Summary Checklist */}
      <div className="mb-10">
        <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 mb-4 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>Story Package Certification Summary</span>
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {completionChecklist.map((item, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/20 flex items-start gap-3"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <span className="text-sm font-bold text-white block">{item.label}</span>
                <span className="text-xs text-white/50">{item.detail}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Primary Action Buttons */}
      <div className="pt-6 border-t border-white/10 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onViewStoryPackage}
            className="px-6 py-3.5 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-black font-black text-xs uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-xl shadow-emerald-500/25 active:scale-98"
          >
            <FileCheck className="w-4 h-4" />
            <span>View Story Package</span>
          </button>

          {onContinueToEpisodePlanning && (
            <button
              onClick={onContinueToEpisodePlanning}
              className="px-6 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-black text-xs uppercase tracking-wider transition-all flex items-center justify-center gap-2 border border-white/15"
            >
              <span>Continue to Episode Planning</span>
              <ArrowRight className="w-4 h-4 text-emerald-400" />
            </button>
          )}
        </div>

        {onOpenOperatorConsole && (
          <button
            onClick={onOpenOperatorConsole}
            className="text-xs font-mono text-white/40 hover:text-white/80 transition-colors flex items-center gap-1.5 self-center sm:self-auto"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Open Diagnostic Console</span>
          </button>
        )}
      </div>
    </div>
  );
};
