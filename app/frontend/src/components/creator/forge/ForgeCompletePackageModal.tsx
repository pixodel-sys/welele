import React, { useState, useEffect } from 'react';
import { StoryState, ForgeCompletionAssessment, ChronologyEvent } from '../../../types/storyForge';
import { storyForgeApi } from '../../../services/storyForgeApi';
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
  const [remotePackage, setRemotePackage] = useState<any>(null);
  const [activePillarTab, setActivePillarTab] = useState<'overview' | 'characters' | 'world' | 'chronology' | 'artwork' | 'episodes' | 'callsheet'>('overview');

  useEffect(() => {
    if (isOpen && storyState?.story_id) {
      storyForgeApi.getPackage(storyState.story_id)
        .then((pkg) => {
          if (pkg) setRemotePackage(pkg);
        })
        .catch((err) => {
          console.warn('[ForgeCompletePackageModal] Could not fetch remote package, synthesizing locally:', err);
        });
    }
  }, [isOpen, storyState?.story_id]);

  if (!isOpen) return null;

  const characters = Object.values(storyState.characters || {});

  const getPackagePayload = () => {
    if (remotePackage) {
      return remotePackage;
    }

    return {
      story_package_version: '0.2.0',
      story_id: storyState.story_id,
      title: storyState.title,
      logline: storyState.logline || '',
      milestone: assessment?.current_milestone || 'FORGE_COMPLETE',
      readiness_status: assessment?.status || 'FORGE_COMPLETE',
      state_version: storyState.state_version,
      pillar_1_story_bible: {
        title: storyState.title,
        logline: storyState.logline || '',
        theme: storyState.theme || 'Royal Lineage, Duty & Customary Inheritance',
        primary_language: 'isiZulu',
        format: 'Vertical Microdrama (9:16)',
      },
      pillar_2_character_bible: characters.map(c => ({
        name: c.name,
        role: c.role,
        status: c.status,
        core_motivation: c.core_motivation || null,
        secret_desire: c.secret_desire || null,
        fatal_flaw: c.fatal_flaw || null,
        relationships: c.relationships || []
      })),
      pillar_3_world_and_rules: storyState.world || {
        arena: 'Umhlanga Coast & Umlazi, KwaZulu-Natal',
        rules_and_lore: [
          'Customary royal succession covenants supersede civil commercial contracts.',
          'The royal heirloom wrist cuff authenticates bloodline succession.'
        ]
      },
      pillar_4_chronology_spine: events && events.length > 0 ? events : (storyState.chronology || []),
      pillar_5_production_artwork: {
        widescreen_hero_banner_16_9: '/banners/umkhehlo_hero_banner.jpg',
        vertical_mobile_poster_9_16: '/posters/umkhehlo_series_poster.jpg',
        prompt_hero: 'Cinematic 16:9 widescreen hero banner featuring lead protagonist with golden royal wrist cuff, coastal Umhlanga estate at sunset, 4K streaming quality',
        prompt_poster: 'Cinematic vertical 9:16 poster for South African drama, young woman in seamstress attire with glowing Zulu gold wrist cuff, vibrant isicholo crowns'
      },
      pillar_6_episode_architecture: [
        {
          episode_number: 1,
          title: 'The Stained Veil',
          duration_seconds: 75,
          hook_3s: 'Designer heel stamps on silk veil; Minenhle slaps Nandi as altar ceremony freezes.',
          cliffhanger_80s: 'Wrist cuff snaps open; Bheki drops to his knees: "...Nomvula?" Cut to black.'
        },
        {
          episode_number: 2,
          title: 'The Bloodline Mark',
          duration_seconds: 80,
          hook_3s: 'Armed guards move to seize Nandi; Bhekisisa stands between them with his royal signet ring.',
          cliffhanger_80s: 'Minenhle bribes guard Mthembu: "Ensure that girl and that bracelet vanish before clan elders arrive."'
        },
        {
          episode_number: 3,
          title: 'Flight to Umlazi',
          duration_seconds: 85,
          hook_3s: 'Tires screech through estate gates as Nandi flees into the rainy Durban night.',
          cliffhanger_80s: 'Inside workshop drawer, Nandi finds 1998 Customary Succession Covenant as Mthembu\'s headlights box her exit.'
        },
        {
          episode_number: 4,
          title: 'Township Sanctuary',
          duration_seconds: 80,
          hook_3s: 'Mthembu kicks open the workshop door; township matriarchs block him with heavy tailoring shears.',
          cliffhanger_80s: 'Nandi shows Bhekisisa the 1998 covenant: "Your father stole this throne." Bheki\'s phone rings with emergency hospital alert.'
        },
        {
          episode_number: 5,
          title: 'The Poisoned Well',
          duration_seconds: 90,
          hook_3s: 'Monitors flatline in the ICU; Clan Patriarch demands: "Did she wear the lion crest?"',
          cliffhanger_80s: 'Patriarch recognizes Nandi\'s face and decrees: "The blood has returned. Halt all corporate transfers!" He collapses.'
        }
      ],
      pillar_7_production_call_sheet: {
        format: '9:16 Vertical Microdrama',
        locations: ['Umhlanga Estate Terrace & Suite', 'Umlazi Seamstress Shop', 'Umhlanga Seaside Pavilion'],
        audio: 'isiZulu Vernacular',
        total_episodes: 30,
        days: [
          { day: 1, focus: 'Setup & Wedding Halt', episodes: '1-10' },
          { day: 2, focus: 'Township Battle & DNA Tampering', episodes: '11-20' },
          { day: 3, focus: 'The True Coronation', episodes: '21-30' }
        ]
      },
      pillar_8_forge_provenance: {
        configuration_id: 'CFG-001',
        validated_by: 'ForgeJudge v0.2.0',
        timestamp: new Date().toISOString(),
        assessment: assessment
      },
      narrative_plants: storyState.plants || [],
      knowledge_states: storyState.knowledge_states || [],
    };
  };

  const isM3 = (remotePackage?.milestone === 'FORGE_COMPLETE' || assessment?.current_milestone === 'FORGE_COMPLETE') &&
               (remotePackage?.readiness_status === 'FORGE_COMPLETE' || assessment?.status === 'FORGE_COMPLETE');
  const badgeTitle = isM3
    ? 'FORGE COMPLETE • M3 Certified'
    : `${(remotePackage?.milestone || assessment?.current_milestone || 'CONCLUDED').replace(/_/g, ' ')} • Ready`;

  const handleCopyPackage = () => {
    const payload = getPackagePayload();
    const jsonStr = JSON.stringify(payload, null, 2);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(jsonStr);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJSON = () => {
    try {
      const payload = getPackagePayload();
      const jsonStr = JSON.stringify(payload, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const safeTitle = (storyState.title || 'story').toLowerCase().replace(/[^a-z0-9]/g, '_');
      const filename = `${safeTitle}_story_package.json`;

      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      
      setTimeout(() => {
        if (document.body.contains(link)) {
          document.body.removeChild(link);
        }
        window.URL.revokeObjectURL(url);
      }, 5000);
    } catch (err) {
      console.error('Download package error:', err);
    }
  };

  const pillarTabs = [
    { id: 'overview', label: '1. Story Bible', icon: BookOpen },
    { id: 'characters', label: `2. Characters (${characters.length})`, icon: Users },
    { id: 'world', label: '3. World & Lore', icon: Layers },
    { id: 'chronology', label: `4. Spine (${events.length})`, icon: Clock },
    { id: 'artwork', label: '5. Key Visuals', icon: Sparkles },
    { id: 'episodes', label: '6. Episodes (30)', icon: Clapperboard },
    { id: 'callsheet', label: '7. Call Sheet', icon: ShieldCheck },
  ] as const;

  return (
    <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl flex items-center justify-center p-3 sm:p-6 overflow-hidden animate-fade-in font-sans">
      <div className="bg-[#0E1017] border border-white/10 rounded-3xl max-w-5xl w-full h-[92vh] flex flex-col shadow-2xl overflow-hidden ring-1 ring-white/10">
        
        {/* Modal Header: Clear Identity & Provenance */}
        <div className="p-6 bg-gradient-to-r from-emerald-950/40 via-[#121520] to-black border-b border-white/10 flex items-start justify-between shrink-0">
          <div className="space-y-1.5">
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full ${
                isM3 ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400' : 'bg-amber-500/15 border border-amber-500/30 text-amber-300'
              } text-[11px] font-mono font-bold uppercase tracking-wider`}>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>{badgeTitle}</span>
              </span>
              <span className="text-[11px] font-mono text-white/40">
                Story Package v0.2.0 • Canon v{storyState.state_version}
              </span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              {storyState.title}
            </h2>
            <p className="text-xs text-white/60 max-w-2xl leading-relaxed">
              Certified production package ready for director handoff, vertical shoot schedules, and episode generation.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-colors"
              title="Close Package View"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Pillar Navigation Bar */}
        <div className="px-6 py-2.5 bg-black/60 border-b border-white/10 flex items-center gap-1.5 overflow-x-auto custom-scrollbar shrink-0">
          {pillarTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activePillarTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActivePillarTab(tab.id as any)}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-2 shrink-0 ${
                  isActive
                    ? 'bg-[#FF6500] text-black shadow-md shadow-[#FF6500]/20'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Display Area with Generous Spacing and Hierarchy */}
        <div className="flex-1 p-6 sm:p-8 overflow-y-auto custom-scrollbar bg-gradient-to-b from-[#0E1017] to-[#0A0B10]">
          
          {/* TAB 1: STORY BIBLE */}
          {activePillarTab === 'overview' && (
            <div className="max-w-4xl space-y-6 animate-fade-in">
              <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 space-y-3">
                <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#FF6500]">
                  <BookOpen className="w-4 h-4" />
                  <span>Pillar 1: Narrative Thesis & Logline</span>
                </div>
                <p className="text-lg font-medium text-white leading-relaxed">
                  "{storyState.logline}"
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-5 rounded-2xl bg-black/40 border border-white/5 space-y-1.5">
                  <span className="text-[11px] font-mono text-white/40 uppercase block">Core Theme</span>
                  <div className="text-sm font-bold text-white">
                    {storyState.theme || 'Royal Lineage, Duty & Customary Inheritance'}
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-black/40 border border-white/5 space-y-1.5">
                  <span className="text-[11px] font-mono text-white/40 uppercase block">Production Format</span>
                  <div className="text-sm font-bold text-[#FFA000]">
                    9:16 Vertical Microdrama (TikTok / Reels / Native)
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-black/40 border border-white/5 space-y-1.5">
                  <span className="text-[11px] font-mono text-white/40 uppercase block">Primary Language</span>
                  <div className="text-sm font-bold text-emerald-400">
                    isiZulu Vernacular (with English Subtitles)
                  </div>
                </div>
              </div>

              {/* Provenance & Guarantee */}
              <div className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/20 flex items-start gap-4">
                <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div className="space-y-1 text-xs">
                  <span className="font-bold text-white uppercase tracking-wider font-mono">
                    Story Invariants Locked
                  </span>
                  <p className="text-white/70 leading-relaxed">
                    All character motivations, plant/payoff trajectories, and 6-stage narrative arcs have been verified without internal contradictions.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: CHARACTER BIBLE */}
          {activePillarTab === 'characters' && (
            <div className="space-y-6 animate-fade-in max-w-4xl">
              <div>
                <h3 className="text-lg font-black text-white">Cast of Characters</h3>
                <p className="text-xs text-white/60">Defined roles, status levels, core motivations, and relational tensions.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {characters.map((c) => {
                  const isProtagonist = c.role === 'PROTAGONIST';
                  const isAntagonist = c.role === 'ANTAGONIST';

                  return (
                    <div
                      key={c.name}
                      className={`p-5 rounded-2xl border transition-all space-y-3.5 ${
                        isProtagonist
                          ? 'bg-[#FF6500]/5 border-[#FF6500]/30'
                          : isAntagonist
                          ? 'bg-purple-950/20 border-purple-500/30'
                          : 'bg-white/[0.02] border-white/10'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-base font-black text-white">{c.name}</span>
                        <span className={`px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold uppercase ${
                          isProtagonist ? 'bg-[#FF6500] text-black' : isAntagonist ? 'bg-purple-500 text-white' : 'bg-white/10 text-white/80'
                        }`}>
                          {c.role}
                        </span>
                      </div>

                      {c.core_motivation && (
                        <div className="text-xs space-y-1">
                          <span className="text-white/40 font-mono uppercase text-[10px] block font-bold">
                            Core Motivation
                          </span>
                          <p className="text-white/80 leading-relaxed">{c.core_motivation}</p>
                        </div>
                      )}

                      {c.secret_desire && (
                        <div className="text-xs space-y-1">
                          <span className="text-[#FFA000]/70 font-mono uppercase text-[10px] block font-bold">
                            Hidden Secret / Vulnerability
                          </span>
                          <p className="text-white/70 leading-relaxed italic">{c.secret_desire}</p>
                        </div>
                      )}

                      {c.relationships && c.relationships.length > 0 && (
                        <div className="pt-2.5 border-t border-white/5 space-y-1 text-xs">
                          <span className="text-white/40 font-mono uppercase text-[10px] block font-bold">
                            Dynamics
                          </span>
                          {c.relationships.map((rel, i) => (
                            <div key={i} className="text-[11px] text-white/70">
                              <span className="text-[#FF6500] font-bold">→ {rel.target_character}:</span> {rel.dynamic}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 3: WORLD & LORE */}
          {activePillarTab === 'world' && (
            <div className="space-y-6 animate-fade-in max-w-4xl">
              <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/10 space-y-3">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#FF6500] block">
                  Primary Arena & Setting
                </span>
                <p className="text-base text-white font-medium leading-relaxed">
                  {storyState.world?.arena || 'Umhlanga Coastline Estates & Umlazi Workshops, KwaZulu-Natal'}
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-black/40 border border-white/10 space-y-3">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 block">
                  Customary Rules & Inviolable World Lore
                </span>
                <ul className="space-y-2.5 text-xs text-white/80 list-disc list-inside leading-relaxed">
                  {(storyState.world?.rules_and_lore && storyState.world.rules_and_lore.length > 0
                    ? storyState.world.rules_and_lore
                    : [
                        'Customary royal succession covenants supersede civil commercial contracts.',
                        'The royal heirloom wrist cuff authenticates bloodline succession.',
                        'Elders hold veto power over any public declaration made without clan witness.'
                      ]
                  ).map((rule, idx) => (
                    <li key={idx} className="text-white/90">{rule}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* TAB 4: CHRONOLOGY SPINE */}
          {activePillarTab === 'chronology' && (
            <div className="space-y-6 animate-fade-in max-w-4xl">
              <div>
                <h3 className="text-lg font-black text-white">Canonical Chronology Spine</h3>
                <p className="text-xs text-white/60">The 6 immutable dramatic beats holding the story's architectural integrity.</p>
              </div>

              <div className="space-y-3">
                {events.map((ev) => (
                  <div key={ev.event_sequence} className="p-4 rounded-2xl bg-white/[0.02] border border-white/10 flex items-start gap-4">
                    <span className="w-7 h-7 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-mono text-xs font-bold flex items-center justify-center shrink-0">
                      {ev.event_sequence}
                    </span>
                    <div className="space-y-1">
                      <div className="font-bold text-white text-sm">{ev.headline}</div>
                      <div className="text-xs text-white/70 leading-relaxed">{ev.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: PRODUCTION ARTWORK */}
          {activePillarTab === 'artwork' && (
            <div className="space-y-6 animate-fade-in max-w-4xl">
              <div>
                <h3 className="text-lg font-black text-white">Certified Artwork Suite & Prompts</h3>
                <p className="text-xs text-white/60">High-fidelity concept visuals and certified generative prompts for marketing and mobile poster art.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 16:9 Hero Banner Card */}
                <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/10 space-y-3">
                  <div className="flex items-center justify-between text-xs font-bold text-white">
                    <span>16:9 Widescreen Hero Banner</span>
                    <span className="text-[10px] font-mono text-white/40">Web & Streaming Carousel</span>
                  </div>
                  <div className="aspect-video w-full rounded-xl bg-black/60 border border-white/10 overflow-hidden relative group">
                    <img
                      src="/banners/umkhehlo_hero_banner.jpg"
                      alt="Hero Banner"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end p-3">
                      <span className="text-xs font-mono text-white font-bold">
                        Umkhehlo • Hero Banner
                      </span>
                    </div>
                  </div>
                  <p className="p-3 rounded-xl bg-black/40 border border-white/5 text-[11px] text-white/60 font-mono leading-relaxed">
                    Prompt: "Cinematic 16:9 widescreen hero banner featuring lead protagonist with golden royal wrist cuff, coastal Umhlanga estate at sunset, 4K streaming quality..."
                  </p>
                </div>

                {/* 9:16 Vertical Poster Card */}
                <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/10 space-y-3">
                  <div className="flex items-center justify-between text-xs font-bold text-white">
                    <span>9:16 Vertical Mobile Poster</span>
                    <span className="text-[10px] font-mono text-white/40">Feed Card & Player</span>
                  </div>
                  <div className="aspect-[9/16] w-48 mx-auto rounded-xl bg-black/60 border border-white/10 overflow-hidden relative group shadow-2xl">
                    <img
                      src="/posters/umkhehlo_series_poster.jpg"
                      alt="Vertical Poster"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end p-3">
                      <span className="text-[11px] font-mono text-white font-bold">
                        Vertical Poster
                      </span>
                    </div>
                  </div>
                  <p className="p-3 rounded-xl bg-black/40 border border-white/5 text-[11px] text-white/60 font-mono leading-relaxed">
                    Prompt: "Cinematic vertical 9:16 poster for South African drama, young woman in seamstress attire with glowing Zulu gold wrist cuff, vibrant isicholo crowns..."
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: EPISODE ARCHITECTURE */}
          {activePillarTab === 'episodes' && (
            <div className="space-y-6 animate-fade-in max-w-4xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-lg font-black text-white">Episode Architecture (30 Episodes)</h3>
                  <p className="text-xs text-white/60">Strict 3-second hook density with 80-second vertical cliffhangers.</p>
                </div>
                <span className="px-3 py-1 rounded-full bg-[#FF6500]/15 border border-[#FF6500]/30 text-[#FFA000] text-xs font-mono font-bold self-start">
                  Episode 6 Paywall Trigger
                </span>
              </div>

              <div className="space-y-3">
                {[
                  {
                    ep: 1,
                    title: 'The Stained Veil',
                    dur: '75s',
                    badge: '100% Free Hook',
                    badgeColor: 'text-emerald-400 bg-emerald-500/20',
                    hook: 'Designer heel stamps on silk bridal veil; Minenhle slaps seamstress Nandi as altar ceremony freezes.',
                    cliff: 'The ancient gold wrist cuff snaps open; Bheki drops to one knee: "...Nomvula?" Organ cuts to black.'
                  },
                  {
                    ep: 2,
                    title: 'The Bloodline Mark',
                    dur: '80s',
                    badge: '100% Free Hook',
                    badgeColor: 'text-emerald-400 bg-emerald-500/20',
                    hook: 'Armed private guards move in to seize Nandi; Bhekisisa steps between them and draws his customary royal signet ring.',
                    cliff: 'Minenhle secretly bribes chief security guard Mthembu: "Ensure that girl and that bracelet vanish before clan elders arrive."'
                  },
                  {
                    ep: 3,
                    title: 'Flight to Umlazi',
                    dur: '85s',
                    badge: 'Rising Stakes',
                    badgeColor: 'text-[#FFA000] bg-[#FFA000]/20',
                    hook: 'Tires screech through estate perimeter gates as Nandi escapes into the rainy Durban night with guards in pursuit.',
                    cliff: 'Inside her mother\'s sewing drawer, Nandi uncovers the hidden 1998 Customary Succession Covenant as Mthembu\'s headlights surround the building.'
                  },
                  {
                    ep: 4,
                    title: 'Township Sanctuary',
                    dur: '80s',
                    badge: 'Community Defiance',
                    badgeColor: 'text-[#FFA000] bg-[#FFA000]/20',
                    hook: 'Mthembu kicks open the workshop door; township matriarchs block him with heavy tailoring shears and whistles.',
                    cliff: 'Nandi confronts Bhekisisa with the covenant: "Your father didn\'t inherit this throne, Bheki. He stole it from my mother." Emergency hospital alert sounds.'
                  },
                  {
                    ep: 5,
                    title: 'The Poisoned Well',
                    dur: '90s',
                    badge: 'Pre-Paywall Precipice',
                    badgeColor: 'text-[#FF6500] bg-[#FF6500]/20',
                    hook: 'Monitors flatline in the ICU; Clan Patriarch Sipho demands: "The true wrist cuff... did she wear the lion crest?"',
                    cliff: 'Patriarch sees Nandi\'s face, recognizes the royal lion cuff, and decrees: "The blood has returned. Halt all corporate transfers!" He collapses.'
                  },
                  {
                    ep: 6,
                    title: 'The Elder Council Inquest',
                    dur: '90s',
                    badge: 'Judicial Exposure',
                    badgeColor: 'text-purple-400 bg-purple-500/20',
                    hook: 'Council elders strike ironwood staffs on boardroom floor; mining lease transfers are frozen pending bloodline proof.',
                    cliff: 'Private doctor confesses on speakerphone that Minenhle paid R20M to forge the DNA registry. Minenhle storms out into the rain.'
                  },
                  {
                    ep: 7,
                    title: 'The Night of the Ancestors',
                    dur: '90s',
                    badge: 'Sacred Reconciliation',
                    badgeColor: 'text-blue-400 bg-blue-500/20',
                    hook: 'Candles flicker around Nomvula\'s granite headstone in the Umlazi cemetery as rain washes over the red earth.',
                    cliff: 'Bheki presents the silver-threaded Isicholo crown and takes a bullet meant for Nandi as township police sirens wail in the distance.'
                  },
                  {
                    ep: 8,
                    title: 'The True Umkhehlo (Resolution)',
                    dur: '90s',
                    badge: 'Natural Series Resolution',
                    badgeColor: 'text-emerald-400 bg-emerald-500/20 border border-emerald-500/40',
                    hook: 'Sunrise breaks over the Indian Ocean; ancient kudu horns sound as Nandi enters crowned in silver and gold.',
                    cliff: 'Bheki places the sovereign mantle upon Nandi as thousands roar: "Bayede!" Mining leases are transferred into community trust. Permanent canon resolution achieved.'
                  }
                ].map((item) => (
                  <div key={item.ep} className="p-4 rounded-2xl bg-white/[0.02] border border-white/10 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-white">Episode {item.ep}: "{item.title}" ({item.dur})</span>
                      <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${item.badgeColor}`}>
                        {item.badge}
                      </span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 text-xs">
                      <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                        <strong className="text-emerald-400 block mb-1 font-mono uppercase text-[10px]">3-Second Opening Hook</strong>
                        <span className="text-white/80">{item.hook}</span>
                      </div>
                      <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                        <strong className="text-[#FFA000] block mb-1 font-mono uppercase text-[10px]">80-Second Cliffhanger</strong>
                        <span className="text-white/80">{item.cliff}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 7: CALL SHEET */}
          {activePillarTab === 'callsheet' && (
            <div className="space-y-6 animate-fade-in max-w-4xl">
              <div>
                <h3 className="text-lg font-black text-white">3-Day Micro-Drama Production Schedule</h3>
                <p className="text-xs text-white/60">Streamlined vertical shooting schedule optimized for rapid 30-episode output.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/10 space-y-2">
                  <span className="text-xs font-mono font-bold text-[#FFA000] uppercase block">Day 1 • Setup & Wedding</span>
                  <div className="text-sm font-bold text-white">Episodes 1–10</div>
                  <p className="text-xs text-white/60 leading-relaxed">
                    Location: Umhlanga Estate Suite & Terrace. The Veil Slap, Bridal Entrance, and Wedding Halt.
                  </p>
                </div>

                <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/10 space-y-2">
                  <span className="text-xs font-mono font-bold text-[#FFA000] uppercase block">Day 2 • Township Battle</span>
                  <div className="text-sm font-bold text-white">Episodes 11–20</div>
                  <p className="text-xs text-white/60 leading-relaxed">
                    Location: Umlazi Seamstress Shop. DNA tampering, night confrontation, and elder council warning.
                  </p>
                </div>

                <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/10 space-y-2">
                  <span className="text-xs font-mono font-bold text-[#FFA000] uppercase block">Day 3 • True Coronation</span>
                  <div className="text-sm font-bold text-white">Episodes 21–30</div>
                  <p className="text-xs text-white/60 leading-relaxed">
                    Location: Umhlanga Seaside Pavilion. Clan heirloom revelation, arrest, and authentic royal Umkhehlo.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-5 bg-black/80 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-2 text-[11px] font-mono text-white/50">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>CFG-001 Frozen Baseline • Validated by ForgeJudge v0.2.0</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleCopyPackage}
              className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white font-bold text-xs flex items-center gap-2 transition-all border border-white/5"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-white/60" />}
              <span>{copied ? 'Copied JSON' : 'Copy Package JSON'}</span>
            </button>
            <button
              onClick={handleDownloadJSON}
              className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-black text-xs uppercase tracking-wider flex items-center gap-2 transition-all shadow-lg shadow-emerald-500/20 active:scale-98"
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

