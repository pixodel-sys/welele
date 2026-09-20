import React, { useState } from 'react';
import { StoryState, ChronologyEvent } from '../../../types/storyForge';
import {
  Users,
  Globe,
  Clock,
  Sparkles,
  Shield,
  Layers,
  CheckCircle2,
  Circle,
  HelpCircle,
  Zap,
  ArrowRight
} from 'lucide-react';

interface StoryStatePanelProps {
  storyState: StoryState | null;
  events?: ChronologyEvent[];
}

export const StoryStatePanel: React.FC<StoryStatePanelProps> = ({
  storyState,
  events = [],
}) => {
  const [activeTab, setActiveTab] = useState<'characters' | 'world' | 'chronology' | 'plants'>('characters');

  if (!storyState) {
    return (
      <div className="p-8 text-center text-xs text-white/40 font-mono">
        No active Story State loaded.
      </div>
    );
  }

  const charactersList = Object.values(storyState.characters || {});
  const plantsList = storyState.plants || [];

  const canonicalAnchors = [
    { num: 1, name: 'Inciting Disruption', desc: 'The initial disruption or discovery that upsets ordinary life.' },
    { num: 2, name: 'Point of No Return', desc: 'Protagonist commits to the conflict and enters the dangerous arena.' },
    { num: 3, name: 'Midpoint Revelation', desc: 'A major truth or escalating stakes invert the protagonist\'s understanding.' },
    { num: 4, name: 'Dark Night / Low Point', desc: 'The darkest crisis where defeat seems inevitable and cost is highest.' },
    { num: 5, name: 'Climax', desc: 'The decisive confrontation between protagonist and counterforce.' },
    { num: 6, name: 'Resolution / Final Cost', desc: 'Consequences settled, cost paid, and new state established.' },
  ];

  return (
    <div className="h-full flex flex-col bg-[#12131C] border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
      {/* Top Header & Tabs */}
      <div className="p-3.5 border-b border-white/5 bg-black/40">
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              Live Canonical State
            </h3>
          </div>
          <span className="px-2 py-0.5 rounded bg-white/10 text-white/80 font-mono text-[11px] font-bold">
            v{storyState.state_version}
          </span>
        </div>

        {/* Tab Buttons */}
        <div className="grid grid-cols-4 gap-1 p-1 rounded-xl bg-black/60 border border-white/5">
          <button
            onClick={() => setActiveTab('characters')}
            className={`py-1.5 px-2 rounded-lg text-[11px] font-bold transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'characters'
                ? 'bg-[#FF6500] text-black shadow'
                : 'text-white/60 hover:text-white'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>Cast ({charactersList.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('world')}
            className={`py-1.5 px-2 rounded-lg text-[11px] font-bold transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'world'
                ? 'bg-[#FF6500] text-black shadow'
                : 'text-white/60 hover:text-white'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>World</span>
          </button>
          <button
            onClick={() => setActiveTab('chronology')}
            className={`py-1.5 px-2 rounded-lg text-[11px] font-bold transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'chronology'
                ? 'bg-[#FF6500] text-black shadow'
                : 'text-white/60 hover:text-white'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Spine ({events.length}/6)</span>
          </button>
          <button
            onClick={() => setActiveTab('plants')}
            className={`py-1.5 px-2 rounded-lg text-[11px] font-bold transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'plants'
                ? 'bg-[#FF6500] text-black shadow'
                : 'text-white/60 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Plants ({plantsList.length})</span>
          </button>
        </div>
      </div>

      {/* Tab Content Viewport */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 custom-scrollbar">
        {/* TAB 1: CHARACTERS */}
        {activeTab === 'characters' && (
          <div className="space-y-3">
            {charactersList.length === 0 ? (
              <div className="py-8 text-center text-xs text-white/40 font-mono">
                No characters committed in canon yet.
              </div>
            ) : (
              charactersList.map((char) => {
                const isProtagonist = char.role === 'PROTAGONIST';
                const isAntagonist = char.role === 'ANTAGONIST';

                return (
                  <div
                    key={char.name}
                    className={`p-3.5 rounded-xl border transition-all space-y-2 ${
                      isProtagonist
                        ? 'bg-[#FF6500]/10 border-[#FF6500]/30'
                        : isAntagonist
                        ? 'bg-purple-950/20 border-purple-500/30'
                        : 'bg-black/40 border-white/5'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-black text-white font-sans">{char.name}</h4>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                            isProtagonist
                              ? 'bg-[#FF6500] text-black'
                              : isAntagonist
                              ? 'bg-purple-500 text-black'
                              : 'bg-white/10 text-white/70'
                          }`}
                        >
                          {char.role}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-white/40">{char.status}</span>
                    </div>

                    {char.core_motivation && (
                      <div className="text-xs text-white/80 leading-relaxed">
                        <span className="text-white/40 font-mono font-semibold text-[10px] uppercase block">
                          Core Motivation:
                        </span>
                        {char.core_motivation}
                      </div>
                    )}

                    {char.relationships && char.relationships.length > 0 && (
                      <div className="pt-2 border-t border-white/5 space-y-1">
                        <span className="text-white/40 font-mono font-semibold text-[10px] uppercase block">
                          Relationships:
                        </span>
                        {char.relationships.map((rel, idx) => (
                          <div key={idx} className="text-xs font-mono text-white/70 flex items-center gap-1.5">
                            <span className="text-[#FF6500]">→ {rel.target_character}:</span>
                            <span className="text-white/50">{rel.dynamic}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* TAB 2: WORLD & ARENA */}
        {activeTab === 'world' && (
          <div className="space-y-3">
            <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
              <span className="text-white/40 font-mono font-bold text-[10px] uppercase block">
                Primary Arena / Setting
              </span>
              <p className="text-xs text-white/90 leading-relaxed">
                {storyState.world?.arena || 'Arena details will be anchored as the narrative develops.'}
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <span className="text-white/40 font-mono font-bold text-[10px] uppercase block">
                World Rules & Lore ({storyState.world?.rules_and_lore?.length || 0})
              </span>
              {storyState.world?.rules_and_lore?.length > 0 ? (
                <ul className="space-y-1.5 text-xs text-white/80 list-disc list-inside">
                  {storyState.world.rules_and_lore.map((rule, idx) => (
                    <li key={idx} className="leading-relaxed">{rule}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-white/40 font-mono">
                  No explicit supernatural or arena rules registered yet.
                </p>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: 6 CANONICAL CHRONOLOGY ANCHORS */}
        {activeTab === 'chronology' && (
          <div className="space-y-2.5">
            <div className="text-[11px] font-mono text-white/50 mb-1">
              Milestone 2 requires all 6 canonical structural anchors:
            </div>
            {canonicalAnchors.map((anchor) => {
              const matchingEvent = events[anchor.num - 1];
              const isSequenced = Boolean(matchingEvent);

              return (
                <div
                  key={anchor.num}
                  className={`p-3 rounded-xl border transition-all ${
                    isSequenced
                      ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                      : 'bg-black/30 border-white/5 text-white/40'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-black/60 border border-white/10 text-[10px] font-mono font-bold flex items-center justify-center">
                        {anchor.num}
                      </span>
                      <h5 className="text-xs font-bold text-white/90">{anchor.name}</h5>
                    </div>
                    {isSequenced ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <Circle className="w-3.5 h-3.5 text-white/20" />
                    )}
                  </div>

                  <p className="text-[11px] text-white/60 pl-7 leading-relaxed">
                    {matchingEvent ? (
                      <span className="text-white font-medium">{matchingEvent.headline} — {matchingEvent.description}</span>
                    ) : (
                      anchor.desc
                    )}
                  </p>
                </div>
              );
            })}
          </div>
        )}

        {/* TAB 4: NARRATIVE PLANTS */}
        {activeTab === 'plants' && (
          <div className="space-y-3">
            {plantsList.length === 0 ? (
              <div className="py-8 text-center text-xs text-white/40 font-mono">
                No physical props or secrets planted in state yet.
              </div>
            ) : (
              plantsList.map((plant, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-[#FFA000]">
                      {plant.plant_name || plant.element_code}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-white/10 text-[10px] font-mono text-emerald-400 font-bold">
                      {plant.payoff_status}
                    </span>
                  </div>
                  <p className="text-xs text-white/80">{plant.description}</p>
                  {plant.intended_payoff && (
                    <div className="text-[11px] font-mono text-white/50 pt-1 border-t border-white/5">
                      Intended Payoff: {plant.intended_payoff}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
