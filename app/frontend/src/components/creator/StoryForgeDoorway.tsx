import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { storyForgeApi, aiApi } from '../../services/api';
import { StoryBeat, DialogueLine, CharacterBibleItem, StoryForgeScript, AIStatus } from '../../types';
import {
  Sparkles,
  BookOpen,
  Send,
  Wand2,
  Flame,
  CheckCircle2,
  ArrowRight,
  Globe,
  Layers,
  Volume2,
  ShieldAlert,
  Zap,
  UserCheck,
  Languages,
  PlusCircle,
  Copy,
  ChevronRight,
  Activity,
  Cpu,
  Info,
  X,
  RefreshCw,
  Check
} from 'lucide-react';

interface StoryForgeDoorwayProps {
  onSendToProduction: (storyData: any) => void;
}

export const StoryForgeDoorway: React.FC<StoryForgeDoorwayProps> = ({ onSendToProduction }) => {
  const { stories } = useApp();
  const [activeSubTab, setActiveSubTab] = useState<'beats' | 'dialogue' | 'bible'>('beats');

  // AI Connection Status State
  const [aiStatus, setAiStatus] = useState<AIStatus>({
    mode: 'fallback',
    provider: 'Welele Offline Drama Engine',
    model: 'local-rule-matrix-v1',
    is_connected: false,
    has_api_key: false,
    latency_ms: 15,
    supported_dialects: ['isiZulu', 'Yoruba', 'Kiswahili', 'Nigerian Pidgin', 'isiXhosa', 'English']
  });
  const [isCheckingStatus, setIsCheckingStatus] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);

  // Input States
  const [selectedGenre, setSelectedGenre] = useState('Township Hustle & Revenge');
  const [durationSec, setDurationSec] = useState(90);
  const [promptHook, setPromptHook] = useState(
    'A disowned Sandton heiress discovers her late father secretly willed the entire taxi fleet empire to a mechanic in Alexandra.'
  );
  const [isForging, setIsForging] = useState(false);
  const [copiedNotification, setCopiedNotification] = useState<string | null>(null);

  // Translation States
  const [dialogueInput, setDialogueInput] = useState('You cannot sell this land. The ancestors are watching every coin you count.');
  const [selectedDialect, setSelectedDialect] = useState<'zu' | 'yo' | 'sw' | 'pcm' | 'xh' | 'en'>('zu');
  const [translationResult, setTranslationResult] = useState<{
    translated_text: string;
    phonetic_note: string;
    cultural_context: string;
    _engine?: string;
  }>({
    translated_text: 'Awukwazi ukudayisa lo mhlaba. Okhokho babheke yonke imali oyibalayo.',
    phonetic_note: 'Deep tonal delivery on "Okhokho" with steady breath control.',
    cultural_context: 'South African high-stakes familial land dispute vernacular.',
    _engine: 'local_fallback'
  });
  const [isTranslating, setIsTranslating] = useState(false);

  // Check AI Status on mount
  const checkStatus = async () => {
    setIsCheckingStatus(true);
    try {
      const status = await aiApi.getStatus();
      setAiStatus(status);
    } catch {
      // Handled in api client
    } finally {
      setIsCheckingStatus(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, []);

  // Active Story Forge Package
  const [storyPackage, setStoryPackage] = useState<StoryForgeScript>({
    id: 'sf_init_01',
    series_title: 'Alexandra: Blood & Coins',
    genre: 'Township Hustle & Revenge',
    target_duration_seconds: 90,
    logline: 'When an Alexandra mechanic inherits Johannesburg’s wealthiest taxi conglomerate, he must outwit rival warlords and a vengeful disowned heiress before the dawn shift.',
    created_at: new Date().toISOString(),
    cliffhanger_prompt: 'Will Sipho hand over the master ledger before the rival hit squad breaches the workshop?',
    characters: [
      {
        id: 'c1',
        name: 'Sipho Dlamini',
        role: 'protagonist',
        archetype: 'The Rightful Outcast',
        secret_motivation: 'Rebuild his family legacy without spilling blood in the township.',
        fatal_flaw: 'Refuses to arm his allies until it is almost too late.',
        signature_quote: 'The grease on my hands washes off; betrayal stays forever.',
        avatar_seed: 'sipho'
      },
      {
        id: 'c2',
        name: 'Lerato Khumalo',
        role: 'antagonist',
        archetype: 'The Ruthless Heiress',
        secret_motivation: 'Prove to the board that she alone has the iron will to lead.',
        fatal_flaw: 'Underestimates community loyalty in Alexandra.',
        signature_quote: 'In Sandton, contracts are signed in blood and gold.',
        avatar_seed: 'lerato'
      },
      {
        id: 'c3',
        name: 'Bra Oupa',
        role: 'confidant',
        archetype: 'The Veteran Marshall',
        secret_motivation: 'Prevent an all-out rank war between the two northern corridors.',
        fatal_flaw: 'Holds secrets about Sipho’s true birth mother.',
        signature_quote: 'The engine that makes the most noise burns out the quickest.',
        avatar_seed: 'oupa'
      }
    ],
    beats: [
      {
        timestamp_seconds: 0,
        label: 'Hook Opening (00:00 - 00:15)',
        intensity: 8,
        action_description: 'Sipho is fixing a minibus carburetor when two luxury black Maybachs blockade the garage alley.'
      },
      {
        timestamp_seconds: 25,
        label: 'Inciting Reveal (00:25 - 00:45)',
        intensity: 7,
        action_description: 'Lerato steps out in designer attire, waving the unsealed golden will stamped by the high court.'
      },
      {
        timestamp_seconds: 55,
        label: 'Turning Point & Stakes (00:55 - 00:75)',
        intensity: 9,
        action_description: 'Bra Oupa pulls Sipho aside, revealing the ledger contains the cartel coordinates of every fleet route.'
      },
      {
        timestamp_seconds: 88,
        label: 'Cliffhanger Paywall Lock (00:88 - 00:90)',
        intensity: 10,
        action_description: 'Red laser sights illuminate the garage wall. Sipho reaches into the toolbox as the screen freezes.',
        cliffhanger_trigger: true
      }
    ],
    dialogue: [
      {
        speaker: 'Lerato',
        original_text: 'You think grease and wrenches qualify you to sit at my father’s table?',
        dialect_code: 'en',
        dialect_label: 'English / High Society Slang',
        phonetic_note: 'Cold, sharp diction with clipped consonants.'
      },
      {
        speaker: 'Sipho',
        original_text: 'I earned every penny with honest sweat. You only know how to spend what others built.',
        dialect_code: 'zu',
        dialect_label: 'isiZulu (Nguni)',
        phonetic_note: 'Resonant chest voice with emphatic rhythm.'
      }
    ]
  });

  const handleForge = async () => {
    setIsForging(true);
    try {
      const generated = await storyForgeApi.generateScript({
        genre: selectedGenre,
        target_duration_seconds: durationSec,
        prompt: promptHook
      });
      setStoryPackage(generated);
      // Re-verify live status
      checkStatus();
    } catch {
      // Handled in api fallback
    } finally {
      setIsForging(false);
    }
  };

  const handleTranslateDialogue = async () => {
    if (!dialogueInput.trim()) return;
    setIsTranslating(true);
    try {
      const result = await storyForgeApi.translateDialogue(dialogueInput, selectedDialect);
      setTranslationResult(result);
    } finally {
      setIsTranslating(false);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedNotification(label);
    setTimeout(() => setCopiedNotification(null), 2500);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-24 animate-fade-in text-white">
      {/* Toast notification */}
      {copiedNotification && (
        <div className="fixed top-6 right-6 z-50 px-4 py-2.5 rounded-[7px] bg-emerald-500/90 text-white text-xs font-bold shadow-2xl flex items-center gap-2 backdrop-blur-md animate-bounce">
          <CheckCircle2 className="w-4 h-4" />
          <span>Copied {copiedNotification} to clipboard!</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="p-6 rounded-[7px] bg-gradient-to-r from-[#E6007A]/25 via-[#14151B] to-[#14151B] border border-pink-500/20 shadow-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-[7px] text-[10px] font-black uppercase tracking-wider bg-[#E6007A]/20 text-[#FF2A6D] border border-pink-500/30">
              STORY FORGE™ AI
            </span>
            <span className="text-xs text-welele-muted">African Microdrama Narrative Engine</span>

            {/* AI CONNECTIVITY STATUS BADGE */}
            <button
              onClick={() => setShowStatusModal(true)}
              className={`px-2.5 py-0.5 rounded-[7px] text-[10px] font-bold border flex items-center gap-1.5 transition-all hover:scale-105 ${
                aiStatus.is_connected
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                  : 'bg-amber-500/20 text-amber-400 border-amber-500/40'
              }`}
              title="Click to view AI Connection Details"
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  aiStatus.is_connected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
                }`}
              />
              <span>
                {aiStatus.is_connected
                  ? 'Live Gemini™ AI (Online)'
                  : 'Local Offline Engine (Fallback Active)'}
              </span>
              <Info className="w-3 h-3 ml-0.5 opacity-70" />
            </button>
          </div>

          <h1 className="text-2xl font-black text-white font-cinematic uppercase tracking-tight">
            Script, Character & Cliffhanger Forge
          </h1>
          <p className="text-xs text-welele-muted mt-1">
            Generate tight 60–90 second vertical episodic beats, African dialect dialogue, and character bibles with zero downtime.
          </p>
        </div>

        <button
          onClick={() => onSendToProduction(storyPackage)}
          className="px-5 py-2.5 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-bold text-xs shadow-lg shadow-pink-500/20 flex items-center gap-2 hover:brightness-110 active:scale-95 transition-all shrink-0"
        >
          <Send className="w-4 h-4" />
          <span>EXPORT TO EPISODE PIPELINE</span>
        </button>
      </div>

      {/* Generation Engine Top Bar */}
      <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
        <div className="md:col-span-3">
          <label className="text-[11px] font-bold text-welele-muted uppercase tracking-wider block mb-1.5">
            Genre & Archetype
          </label>
          <select
            value={selectedGenre}
            onChange={(e) => setSelectedGenre(e.target.value)}
            className="w-full bg-[#0B0C10] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-[#E6007A]"
          >
            <option value="Township Hustle & Revenge">Township Hustle & Revenge</option>
            <option value="Billionaire Dynasty & Betrayal">Billionaire Dynasty & Betrayal</option>
            <option value="Royal Secret & Forced Marriage">Royal Secret & Forced Marriage</option>
            <option value="Lagos Nollywood Thriller">Lagos Nollywood Thriller</option>
            <option value="Nairobi Tech & Syndicate">Nairobi Tech & Syndicate</option>
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="text-[11px] font-bold text-welele-muted uppercase tracking-wider block mb-1.5">
            Target Duration
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            <button
              type="button"
              onClick={() => setDurationSec(60)}
              className={`py-2 text-xs font-bold rounded-[7px] border transition-all ${
                durationSec === 60
                  ? 'bg-welele-gold text-black border-welele-gold shadow'
                  : 'bg-[#0B0C10] text-welele-muted border-white/10 hover:text-white'
              }`}
            >
              60s Fast
            </button>
            <button
              type="button"
              onClick={() => setDurationSec(90)}
              className={`py-2 text-xs font-bold rounded-[7px] border transition-all ${
                durationSec === 90
                  ? 'bg-welele-gold text-black border-welele-gold shadow'
                  : 'bg-[#0B0C10] text-welele-muted border-white/10 hover:text-white'
              }`}
            >
              90s Standard
            </button>
          </div>
        </div>

        <div className="md:col-span-5">
          <label className="text-[11px] font-bold text-welele-muted uppercase tracking-wider block mb-1.5">
            Logline Spark / Core Conflict
          </label>
          <input
            type="text"
            value={promptHook}
            onChange={(e) => setPromptHook(e.target.value)}
            placeholder="E.g. A young chef uncovers a counterfeit coin ring in her restaurant..."
            className="w-full bg-[#0B0C10] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white placeholder-white/20 focus:outline-none focus:border-[#E6007A]"
          />
        </div>

        <div className="md:col-span-2">
          <button
            type="button"
            onClick={handleForge}
            disabled={isForging}
            className="w-full py-2.5 rounded-[7px] bg-[#E6007A] hover:bg-[#FF2A6D] text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-pink-500/20 transition-all disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-welele-gold" />
            <span>{isForging ? 'Synthesizing...' : 'Forge Script'}</span>
          </button>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-3">
        <button
          onClick={() => setActiveSubTab('beats')}
          className={`px-4 py-2 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all ${
            activeSubTab === 'beats'
              ? 'bg-welele-gold text-black shadow'
              : 'bg-[#14151B] text-welele-muted hover:text-white border border-white/5'
          }`}
        >
          <Zap className="w-4 h-4" />
          <span>Episodic Beat Sheet ({storyPackage.beats.length} Beats)</span>
        </button>

        <button
          onClick={() => setActiveSubTab('dialogue')}
          className={`px-4 py-2 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all ${
            activeSubTab === 'dialogue'
              ? 'bg-welele-gold text-black shadow'
              : 'bg-[#14151B] text-welele-muted hover:text-white border border-white/5'
          }`}
        >
          <Languages className="w-4 h-4" />
          <span>African Dialect Adapter</span>
        </button>

        <button
          onClick={() => setActiveSubTab('bible')}
          className={`px-4 py-2 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all ${
            activeSubTab === 'bible'
              ? 'bg-welele-gold text-black shadow'
              : 'bg-[#14151B] text-welele-muted hover:text-white border border-white/5'
          }`}
        >
          <UserCheck className="w-4 h-4" />
          <span>Character Bible ({storyPackage.characters.length} Roles)</span>
        </button>
      </div>

      {/* TAB 1: BEAT SHEET */}
      {activeSubTab === 'beats' && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Main Beats Timeline */}
          <div className="md:col-span-8 space-y-4">
            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-welele-muted uppercase tracking-wider">
                    Script Logline
                  </span>
                  <span className="text-[10px] text-welele-muted font-mono">
                    ({storyPackage.genre})
                  </span>
                </div>
                <button
                  onClick={() => copyToClipboard(storyPackage.logline, 'Logline')}
                  className="p-1 rounded-[7px] hover:bg-white/10 text-welele-muted hover:text-white"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
              </div>
              <p className="text-xs text-white/90 italic p-3 rounded-[7px] bg-black/40 border border-white/5">
                "{storyPackage.logline}"
              </p>
            </div>

            <div className="space-y-3">
              {storyPackage.beats.map((beat, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-[7px] border transition-all ${
                    beat.cliffhanger_trigger
                      ? 'bg-gradient-to-r from-red-950/40 via-[#14151B] to-[#14151B] border-red-500/40 shadow-lg'
                      : 'bg-[#14151B] border-white/5 hover:border-white/15'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded-[7px] text-[10px] font-mono font-bold ${
                          beat.cliffhanger_trigger
                            ? 'bg-red-500 text-white animate-pulse'
                            : 'bg-white/10 text-welele-gold'
                        }`}
                      >
                        T+{beat.timestamp_seconds}s
                      </span>
                      <span className="text-xs font-bold text-white">{beat.label}</span>
                    </div>

                    <div className="flex items-center gap-1.5 text-[11px] text-welele-muted">
                      <span>Intensity:</span>
                      <span className="font-bold text-welele-gold">{beat.intensity}/10</span>
                    </div>
                  </div>

                  <p className="text-xs text-welele-muted leading-relaxed">
                    {beat.action_description}
                  </p>

                  {beat.cliffhanger_trigger && (
                    <div className="mt-3 pt-2.5 border-t border-red-500/20 flex items-center justify-between text-[11px]">
                      <div className="flex items-center gap-1.5 text-red-400 font-bold">
                        <Flame className="w-3.5 h-3.5" />
                        <span>Cliffhanger Paywall Trigger Point</span>
                      </div>
                      <span className="text-welele-muted">Recommended Free Cut @ 00:88</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Side Intensity & Telemetry preview */}
          <div className="md:col-span-4 space-y-4">
            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Flame className="w-4 h-4 text-welele-orange" />
                Pacing & Retention Forecast
              </h3>
              <p className="text-[11px] text-welele-muted">
                Vertical microdramas require an intensity rating ≥ 7 within the first 10 seconds to eliminate early drop-off.
              </p>

              <div className="space-y-2 pt-2">
                {storyPackage.beats.map((b, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between text-[10px] text-welele-muted font-mono">
                      <span>{b.label.split(' ')[0]}</span>
                      <span>{b.intensity * 10}% Intensity</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          b.intensity >= 9
                            ? 'bg-gradient-to-r from-welele-orange to-red-500'
                            : 'bg-welele-gold'
                        }`}
                        style={{ width: `${b.intensity * 10}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#FF2A6D]" />
                Cliffhanger Paywall Question
              </h3>
              <p className="text-xs text-white/90 p-3 rounded-[7px] bg-black/40 border border-white/5 italic">
                "{storyPackage.cliffhanger_prompt}"
              </p>
              <button
                onClick={() => onSendToProduction(storyPackage)}
                className="w-full py-2.5 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-bold text-xs flex items-center justify-center gap-2 shadow"
              >
                <span>Push to Production Draft</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DIALOGUE ADAPTER */}
      {activeSubTab === 'dialogue' && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-6 p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Languages className="w-4 h-4 text-welele-gold" />
              Dialogue Line & Target African Dialect
            </h3>

            <div>
              <label className="text-[11px] font-bold text-welele-muted uppercase tracking-wider block mb-1">
                English Line or Script Text
              </label>
              <textarea
                rows={4}
                value={dialogueInput}
                onChange={(e) => setDialogueInput(e.target.value)}
                placeholder="Enter character line to localize..."
                className="w-full bg-[#0B0C10] p-3 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-welele-gold"
              />
            </div>

            <div>
              <label className="text-[11px] font-bold text-welele-muted uppercase tracking-wider block mb-1">
                Target African Dialect & Market
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { code: 'zu', label: 'isiZulu (SA)' },
                  { code: 'yo', label: 'Yoruba (NG)' },
                  { code: 'sw', label: 'Swahili (KE/TZ)' },
                  { code: 'pcm', label: 'Pidgin (NG/GH)' },
                  { code: 'xh', label: 'isiXhosa (SA)' },
                  { code: 'en', label: 'Global Slang' }
                ].map((dial) => (
                  <button
                    key={dial.code}
                    type="button"
                    onClick={() => setSelectedDialect(dial.code as any)}
                    className={`py-2 px-2 text-[11px] font-bold rounded-[7px] border transition-all text-center ${
                      selectedDialect === dial.code
                        ? 'bg-[#E6007A] text-white border-pink-500'
                        : 'bg-[#0B0C10] text-welele-muted border-white/10 hover:text-white'
                    }`}
                  >
                    {dial.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleTranslateDialogue}
              disabled={isTranslating}
              className="w-full py-2.5 rounded-[7px] bg-welele-gold hover:bg-yellow-400 text-black font-bold text-xs flex items-center justify-center gap-2 shadow transition-all disabled:opacity-50"
            >
              <Globe className="w-4 h-4" />
              <span>{isTranslating ? 'Adapting Cultural Cadence...' : 'Localize Dialogue'}</span>
            </button>
          </div>

          <div className="md:col-span-6 p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-emerald-400" />
                Actor Performance Cue & Phonetics
              </h3>
              <button
                onClick={() => copyToClipboard(translationResult.translated_text, 'Translated Line')}
                className="text-[11px] text-welele-gold hover:underline flex items-center gap-1"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[10px] font-bold text-welele-muted uppercase tracking-wider block mb-1">
                  Localized Spoken Line:
                </span>
                <p className="p-3.5 rounded-[7px] bg-black/50 border border-emerald-500/30 text-emerald-300 font-medium text-sm">
                  "{translationResult.translated_text}"
                </p>
              </div>

              <div>
                <span className="text-[10px] font-bold text-welele-muted uppercase tracking-wider block mb-1">
                  Phonetic Delivery Guide for Actor:
                </span>
                <p className="p-3 rounded-[7px] bg-black/40 border border-white/10 text-white/90">
                  {translationResult.phonetic_note}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-bold text-welele-muted uppercase tracking-wider block mb-1">
                  Cultural Nuance / Subtext:
                </span>
                <p className="p-3 rounded-[7px] bg-black/40 border border-white/10 text-welele-muted">
                  {translationResult.cultural_context}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: CHARACTER BIBLE */}
      {activeSubTab === 'bible' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {storyPackage.characters.map((char) => (
              <div
                key={char.id}
                className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3 hover:border-white/20 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`px-2 py-0.5 rounded-[7px] text-[10px] font-bold uppercase tracking-wider ${
                        char.role === 'protagonist'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : char.role === 'antagonist'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : 'bg-welele-gold/20 text-welele-gold border border-amber-500/30'
                      }`}
                    >
                      {char.role}
                    </span>
                    <span className="text-[10px] text-welele-muted font-mono">{char.archetype}</span>
                  </div>

                  <h4 className="text-base font-black text-white font-cinematic">{char.name}</h4>

                  <div className="mt-3 space-y-2 text-xs">
                    <div>
                      <span className="text-[10px] font-bold text-welele-muted uppercase block">
                        Secret Motivation:
                      </span>
                      <p className="text-white/80">{char.secret_motivation}</p>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-welele-muted uppercase block">
                        Fatal Flaw:
                      </span>
                      <p className="text-red-300/80">{char.fatal_flaw}</p>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-white/10 text-[11px] italic text-welele-gold">
                  "{char.signature_quote}"
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI ENGINE CONNECTIVITY MODAL */}
      {showStatusModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-[7px] bg-[#14151B] border border-white/20 shadow-2xl p-6 space-y-5 text-white animate-scale-up">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-welele-gold" />
                <h3 className="text-base font-black uppercase tracking-wider font-cinematic">
                  Welele AI™ Engine Status
                </h3>
              </div>
              <button
                onClick={() => setShowStatusModal(false)}
                className="p-1 rounded-[7px] hover:bg-white/10 text-welele-muted hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-[7px] bg-black/40 border border-white/10 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-welele-muted">Operating Mode:</span>
                  <span
                    className={`font-bold px-2 py-0.5 rounded-[7px] text-[10px] uppercase font-mono ${
                      aiStatus.is_connected
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {aiStatus.is_connected ? 'Live AI Streaming' : 'Offline Simulation Fallback'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-welele-muted">Active Model:</span>
                  <span className="font-mono text-white font-bold">{aiStatus.model}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-welele-muted">API Provider:</span>
                  <span className="text-white">{aiStatus.provider}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-welele-muted">Inference Latency:</span>
                  <span className="text-welele-gold font-mono font-bold">~{aiStatus.latency_ms} ms</span>
                </div>
              </div>

              <div className="p-3 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-2 text-[11px] text-welele-muted">
                <span className="text-white font-bold block">How Fallback Mode Works:</span>
                <p>
                  When offline or if no API key is supplied, Welele automatically uses the built-in African narrative rules matrix so you never experience generation pauses or broken modals.
                </p>
                <p className="text-[10px] text-welele-gold">
                  To activate Live Gemini calls, add <code>GEMINI_API_KEY="AIza..."</code> to your <code>app/.env</code> file.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={checkStatus}
                disabled={isCheckingStatus}
                className="flex-1 py-2 rounded-[7px] bg-white/10 hover:bg-white/15 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-all"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isCheckingStatus ? 'animate-spin' : ''}`} />
                <span>{isCheckingStatus ? 'Checking Connection...' : 'Refresh Status'}</span>
              </button>
              <button
                onClick={() => setShowStatusModal(false)}
                className="px-4 py-2 rounded-[7px] bg-welele-gold text-black font-bold text-xs"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
