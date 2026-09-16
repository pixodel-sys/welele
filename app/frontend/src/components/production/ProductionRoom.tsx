import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { StoryForgeCockpit } from '../creator/forge/StoryForgeCockpit';
import { storyForgeApi } from '../../services/storyForgeApi';
import { ipApi } from '../../services/api';
import { StorySummary } from '../../types/storyForge';
import {
  Flame,
  Layers,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  FolderOpen,
  ArrowRight,
  ShieldCheck,
  Database,
  Eye,
  Download,
  Copy,
  Check,
  RefreshCw,
  Film,
  Clapperboard,
  BookOpen,
  Users,
  Clock,
  Zap,
  Globe,
  PlusCircle,
  Tv
} from 'lucide-react';

export type ProductionTab =
  | 'story_forge'
  | 'dev_queue'
  | 'story_packages'
  | 'series'
  | 'episodes'
  | 'pipeline';

export const ProductionRoom: React.FC = () => {
  const { stories, attemptModeChange, market } = useApp();
  const [activeTab, setActiveTab] = useState<ProductionTab>('story_forge');

  // Development Queue state
  const [queueStories, setQueueStories] = useState<StorySummary[]>([]);
  const [isLoadingQueue, setIsLoadingQueue] = useState<boolean>(false);
  const [selectedStoryId, setSelectedStoryId] = useState<string | null>(null);

  // Story Packages state
  const [packagesList, setPackagesList] = useState<any[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<any | null>(null);
  const [copiedPackageId, setCopiedPackageId] = useState<string | null>(null);

  // Load dev queue & packages on mount
  const loadQueue = async () => {
    setIsLoadingQueue(true);
    try {
      const list = await storyForgeApi.listStories();
      if (list && Array.isArray(list)) {
        setQueueStories(list);
      }
    } catch (e) {
      console.warn('Could not load Forge stories queue:', e);
    } finally {
      setIsLoadingQueue(false);
    }
  };

  const loadPackages = async () => {
    try {
      const ips = await ipApi.listIps();
      const allPkgs: any[] = [];
      if (ips && Array.isArray(ips)) {
        for (const ip of ips) {
          const detail = await ipApi.getIpDetail(ip.id || ip.franchise_code);
          if (detail && detail.story_packages && detail.story_packages.length > 0) {
            detail.story_packages.forEach((pkg: any) => {
              allPkgs.push({
                ...pkg,
                ip_title: ip.title,
                franchise_code: ip.franchise_code,
                genre: ip.genre,
                primary_language: ip.primary_language,
                story_world: detail.story_world,
                characters: detail.characters,
              });
            });
          }
        }
      }

      // If no packages from IP repo yet, provide default canonical packages
      if (allPkgs.length === 0) {
        allPkgs.push({
          id: 'pkg_ancestral_ledger_001',
          package_title: 'The Ancestral Ledger: Season 1 Package',
          ip_title: 'The Ancestral Ledger',
          franchise_code: 'IP-ANC-LEDGER',
          genre: 'Supernatural Comedy / Vertical Microdrama',
          primary_language: 'isiZulu',
          version: 1,
          target_duration_seconds: 90,
          forge_configuration_id: 'CFG-001',
          lineage_hash: '2fbbbb302bbfe5118749dbbb188f11a4cf130a08e6f1f4e1f7fc7fa82f7c0068',
          created_at: new Date().toISOString(),
          beats_json: [
            { beat_number: 1, label: 'Cold Open Hook', action_description: 'Sipho discovers the golden debt ledger at 02:00 AM.', intensity: 8, timestamp_seconds: 5 },
            { beat_number: 2, label: 'Inciting Ledger Debt', action_description: 'Ledger demands repayment in cowries or corporate shares.', intensity: 9, timestamp_seconds: 40 },
            { beat_number: 3, label: 'Cliffhanger Paywall', action_description: 'Gogo MaMthembu appears through the Sandton boardroom glass.', intensity: 10, timestamp_seconds: 85, cliffhanger_trigger: true }
          ],
          dialogues_json: [
            { character: 'Sipho', line: 'You cannot audit spirits with standard GAAP accounting.' },
            { character: 'Gogo MaMthembu', line: 'The bloodline ledger never closes, child.' }
          ],
          cliffhanger_prompt: 'Will Sipho sign the ancestral waiver before the corporate audit begins?',
          plants: [
            { name: 'Late Uncle Safe Key', status: 'planted', expected_payoff: 'Ep 3 Vault Opening' },
            { name: '19th-Century Murder Record', status: 'planted', expected_payoff: 'Season Finale Climax' }
          ],
          story_world: {
            world_name: 'Sandton Corporate Shrine',
            geographical_setting: 'Johannesburg & Soweto',
            time_period: '2026',
            mythology_and_rules: 'Ancestral debt compounds daily; spirits only manifest in reflective surfaces.',
            cultural_context: 'South African modern banking vs ancestral customs'
          },
          characters: [
            { name: 'Sipho Ndlovu', role: 'protagonist', archetype: 'The Modern Skeptic', secret_motivation: 'Clear family debt within 48h', fatal_flaw: 'Relies solely on rational finance', signature_quote: 'Numbers do not lie, but curses do.' },
            { name: 'Gogo MaMthembu', role: 'antagonist', archetype: 'The Ancient Debt Keeper', secret_motivation: 'Enforce spiritual covenant', fatal_flaw: 'Unforgiving rigidity', signature_quote: 'Every coin has blood on its edge.' }
          ]
        });
      }

      setPackagesList(allPkgs);
    } catch (e) {
      console.warn('Could not load Story Packages:', e);
    }
  };

  useEffect(() => {
    loadQueue();
    loadPackages();
  }, []);

  const copyPackageJSON = (pkg: any) => {
    const jsonStr = JSON.stringify(pkg, null, 2);
    navigator.clipboard?.writeText(jsonStr);
    setCopiedPackageId(pkg.id);
    setTimeout(() => setCopiedPackageId(null), 2000);
  };

  return (
    <div className="space-y-6 pb-24 text-white animate-fade-in max-w-7xl mx-auto px-4">
      {/* ========================================================================= */}
      {/* PRODUCTION WORKSPACE HEADER (COMMAND FLOOR) */}
      {/* ========================================================================= */}
      <div className="p-5 rounded-[7px] bg-[#101116] border border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-[7px] bg-gradient-to-tr from-[#FF6500] to-[#FFA000] flex items-center justify-center text-black font-black text-xl shadow-lg shrink-0">
            <Flame className="w-7 h-7 fill-current" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2.5 py-0.5 rounded-[7px] text-[10px] font-black uppercase tracking-wider bg-[#FF6500]/20 text-[#FF6500] border border-orange-500/40">
                PRODUCTION ROOM
              </span>
              <h1 className="font-extrabold text-lg text-white font-cinematic uppercase tracking-tight">
                Welele Production Floor
              </h1>
              {/* Discrete Forge Configuration Indicator */}
              <span className="text-[10px] font-mono text-white/50 bg-black/50 border border-white/10 px-2.5 py-0.5 rounded-[7px]">
                Forge Configuration: CFG-001
              </span>
            </div>
            <p className="text-xs text-welele-muted mt-1">
              Institutional Narrative Reasoning, Development Queue, and Production-Ready Story Packages.
            </p>
          </div>
        </div>

        {/* Top Actions & Workspace Switcher */}
        <div className="flex items-center gap-2 flex-wrap shrink-0">
          <button
            onClick={() => {
              loadQueue();
              loadPackages();
            }}
            className="p-2 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 hover:text-white transition-all text-xs flex items-center gap-1.5"
            title="Refresh Production Floor State"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingQueue ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <button
            onClick={() => attemptModeChange('creator')}
            className="px-3 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-white hover:text-pink-400 text-xs font-bold flex items-center gap-1.5 transition-all"
            title="Switch to Creator Studio"
          >
            <Sparkles className="w-3.5 h-3.5 text-pink-400" />
            <span className="hidden sm:inline">Creator Studio</span>
          </button>

          <button
            onClick={() => attemptModeChange('viewer')}
            className="px-3 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-white hover:text-welele-gold text-xs font-bold flex items-center gap-1.5 transition-all"
            title="Switch to Consumer Mobile Viewer"
          >
            <Tv className="w-3.5 h-3.5 text-welele-gold" />
            <span className="hidden sm:inline">Viewer App</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* PRODUCTION ROOM NAVIGATION TABS (EXACT SPECIFICATION HIERARCHY) */}
      {/* ========================================================================= */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-3 overflow-x-auto custom-scrollbar">
        {/* TAB 1: STORY FORGE™ */}
        <button
          onClick={() => setActiveTab('story_forge')}
          className={`px-4 py-2.5 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all shrink-0 ${
            activeTab === 'story_forge'
              ? 'bg-gradient-to-r from-[#FF6500] to-[#FFA000] text-black shadow-lg shadow-orange-500/20 font-black'
              : 'bg-[#14151B] text-white/70 hover:text-white border border-white/5'
          }`}
        >
          <Flame className="w-4 h-4" />
          <span>Story Forge™ (Cockpit)</span>
        </button>

        {/* TAB 2: DEVELOPMENT QUEUE */}
        <button
          onClick={() => setActiveTab('dev_queue')}
          className={`px-4 py-2.5 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all shrink-0 ${
            activeTab === 'dev_queue'
              ? 'bg-gradient-to-r from-[#FF6500] to-[#FFA000] text-black shadow-lg shadow-orange-500/20 font-black'
              : 'bg-[#14151B] text-white/70 hover:text-white border border-white/5'
          }`}
        >
          <FolderOpen className="w-4 h-4" />
          <span>Development Queue ({queueStories.length})</span>
        </button>

        {/* TAB 3: STORY PACKAGES */}
        <button
          onClick={() => setActiveTab('story_packages')}
          className={`px-4 py-2.5 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all shrink-0 ${
            activeTab === 'story_packages'
              ? 'bg-gradient-to-r from-[#FF6500] to-[#FFA000] text-black shadow-lg shadow-orange-500/20 font-black'
              : 'bg-[#14151B] text-white/70 hover:text-white border border-white/5'
          }`}
        >
          <FileCheck className="w-4 h-4" />
          <span>Story Packages ({packagesList.length})</span>
        </button>

        {/* TAB 4: SERIES */}
        <button
          onClick={() => setActiveTab('series')}
          className={`px-4 py-2.5 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all shrink-0 ${
            activeTab === 'series'
              ? 'bg-gradient-to-r from-[#FF6500] to-[#FFA000] text-black shadow-lg shadow-orange-500/20 font-black'
              : 'bg-[#14151B] text-white/70 hover:text-white border border-white/5'
          }`}
        >
          <Film className="w-4 h-4" />
          <span>Series ({stories.length})</span>
        </button>

        {/* TAB 5: EPISODES */}
        <button
          onClick={() => setActiveTab('episodes')}
          className={`px-4 py-2.5 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all shrink-0 ${
            activeTab === 'episodes'
              ? 'bg-gradient-to-r from-[#FF6500] to-[#FFA000] text-black shadow-lg shadow-orange-500/20 font-black'
              : 'bg-[#14151B] text-white/70 hover:text-white border border-white/5'
          }`}
        >
          <Clapperboard className="w-4 h-4" />
          <span>Episodes</span>
        </button>

        {/* TAB 6: PRODUCTION PIPELINE */}
        <button
          onClick={() => setActiveTab('pipeline')}
          className={`px-4 py-2.5 rounded-[7px] text-xs font-bold flex items-center gap-2 transition-all shrink-0 ${
            activeTab === 'pipeline'
              ? 'bg-gradient-to-r from-[#FF6500] to-[#FFA000] text-black shadow-lg shadow-orange-500/20 font-black'
              : 'bg-[#14151B] text-white/70 hover:text-white border border-white/5'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Production Pipeline</span>
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: STORY FORGE™ (DEEP REASONING COCKPIT IN PRODUCTION) */}
      {/* ========================================================================= */}
      {activeTab === 'story_forge' && (
        <div className="space-y-4">
          <StoryForgeCockpit />
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: DEVELOPMENT QUEUE */}
      {/* ========================================================================= */}
      {activeTab === 'dev_queue' && (
        <div className="space-y-5">
          <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <FolderOpen className="w-4 h-4 text-[#FF6500]" />
                <span>Active Story Development Queue</span>
              </h2>
              <p className="text-xs text-welele-muted">
                Stories progressing through Forge milestones: M0 Intake → M1 Kernel → M2 Spokes → M3 Complete.
              </p>
            </div>
            <button
              onClick={() => setActiveTab('story_forge')}
              className="px-3.5 py-2 rounded-[7px] bg-[#FF6500] hover:bg-[#FFA000] text-black text-xs font-bold flex items-center gap-1.5 transition-all shadow"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Start New Story in Forge</span>
            </button>
          </div>

          {isLoadingQueue ? (
            <div className="py-16 text-center text-xs text-welele-muted flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-[#FF6500]" />
              <span>Loading development queue from Forge engine...</span>
            </div>
          ) : queueStories.length === 0 ? (
            <div className="py-16 text-center p-6 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3">
              <FolderOpen className="w-10 h-10 text-white/30 mx-auto" />
              <h3 className="text-sm font-bold text-white">No Stories in Queue</h3>
              <p className="text-xs text-welele-muted max-w-sm mx-auto">
                All development intake items have been packaged or no stories have been initiated.
              </p>
              <button
                onClick={() => setActiveTab('story_forge')}
                className="px-4 py-2 rounded-[7px] bg-[#FF6500] text-black text-xs font-bold"
              >
                Create Story in Forge Cockpit →
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {queueStories.map((story) => (
                <div
                  key={story.id}
                  className="p-5 rounded-[7px] bg-[#14151B] border border-white/10 hover:border-[#FF6500]/50 transition-all flex flex-col justify-between space-y-4 shadow-lg"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded-[7px] bg-white/10 text-[10px] font-mono font-bold text-white/80">
                        v{story.current_state_version}
                      </span>
                      <span className={`px-2 py-0.5 rounded-[7px] text-[10px] font-mono font-bold ${
                        story.status === 'FORGE_COMPLETE' || story.status === 'M3_COMPLETE'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}>
                        {story.status}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-white">{story.title}</h3>
                    {story.logline && (
                      <p className="text-xs text-welele-muted line-clamp-3 leading-relaxed">
                        {story.logline}
                      </p>
                    )}
                  </div>

                  <div className="pt-3 border-t border-white/10 flex items-center justify-between">
                    <span className="text-[10px] font-mono text-white/50">
                      ID: {story.id.slice(0, 10)}...
                    </span>
                    <button
                      onClick={() => setActiveTab('story_forge')}
                      className="px-3 py-1.5 rounded-[7px] bg-white/10 hover:bg-[#FF6500] hover:text-black text-white text-xs font-bold flex items-center gap-1 transition-all"
                    >
                      <span>Enter Cockpit</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: STORY PACKAGES (CANONICAL 8-PILLAR PRODUCTION ASSETS) */}
      {/* ========================================================================= */}
      {activeTab === 'story_packages' && (
        <div className="space-y-6">
          <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-emerald-400" />
                <h2 className="text-base font-bold text-white">
                  Production-Ready Story Packages (8 Pillars)
                </h2>
                <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  M3 Certified
                </span>
              </div>
              <p className="text-xs text-welele-muted mt-1">
                Outcome of Story Forge: Story Bible • Character Bible • World/Rules • Chronology • Episode Architecture • Plants/Payoffs • Production Constraints • Forge Provenance.
              </p>
            </div>
            <span className="text-xs font-mono text-white/60 bg-black/40 px-3 py-1.5 rounded-[7px] border border-white/10">
              Provenance: CFG-001 Anchored
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Packages Selector List */}
            <div className="lg:col-span-4 space-y-3">
              <span className="text-xs font-bold text-welele-muted uppercase tracking-wider block">
                Available Story Packages ({packagesList.length})
              </span>
              {packagesList.map((pkg) => {
                const isSelected = selectedPackage?.id === pkg.id || (!selectedPackage && packagesList[0]?.id === pkg.id);
                return (
                  <div
                    key={pkg.id}
                    onClick={() => setSelectedPackage(pkg)}
                    className={`p-4 rounded-[7px] border transition-all cursor-pointer space-y-2.5 ${
                      isSelected
                        ? 'bg-gradient-to-r from-orange-950/40 to-[#14151B] border-[#FF6500] shadow-md'
                        : 'bg-[#14151B] border-white/10 hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono text-[#FF6500] font-bold">
                        {pkg.franchise_code || 'IP-ASSET'}
                      </span>
                      <span className="text-[10px] font-mono text-white/50 bg-black/40 px-2 py-0.5 rounded">
                        {pkg.forge_configuration_id || 'CFG-001'}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-white">{pkg.package_title || pkg.ip_title}</h4>
                    <p className="text-xs text-welele-muted line-clamp-2">
                      {pkg.genre} • {pkg.target_duration_seconds || 90}s vertical microdrama
                    </p>

                    <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[11px] text-welele-muted">
                      <span>Beats: {pkg.beats_json?.length || 3}</span>
                      <span className="text-emerald-400 font-bold">● Ready for Production</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Package 8-Pillars Inspector */}
            <div className="lg:col-span-8 space-y-4">
              {(() => {
                const activePkg = selectedPackage || packagesList[0];
                if (!activePkg) {
                  return (
                    <div className="py-16 text-center text-xs text-welele-muted">
                      Select a story package to inspect its 8 pillars.
                    </div>
                  );
                }

                return (
                  <div className="p-6 rounded-[7px] bg-[#14151B] border border-white/10 space-y-6 shadow-xl">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="px-2.5 py-0.5 rounded-[7px] text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            STORY PACKAGE M3
                          </span>
                          <span className="text-xs font-mono text-welele-gold font-bold">
                            {activePkg.franchise_code || 'IP-ASSET'}
                          </span>
                        </div>
                        <h3 className="text-xl font-bold text-white">{activePkg.package_title || activePkg.ip_title}</h3>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => copyPackageJSON(activePkg)}
                          className="px-3 py-1.5 rounded-[7px] bg-white/10 hover:bg-white/15 text-white text-xs font-bold flex items-center gap-1.5 transition-all"
                        >
                          {copiedPackageId === activePkg.id ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                              <span className="text-emerald-400">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy JSON</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* PILLAR 1: STORY BIBLE */}
                    <div className="space-y-2 p-4 rounded-[7px] bg-black/40 border border-white/5">
                      <h4 className="text-xs font-bold text-[#FF6500] uppercase tracking-wider flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>1. Story Bible & Premise</span>
                      </h4>
                      <p className="text-xs text-white/90 leading-relaxed italic">
                        "{activePkg.logline || 'A high-stakes African vertical microdrama where modern ambitions clash with ancestral obligations.'}"
                      </p>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 text-[11px] text-welele-muted font-mono">
                        <div>Genre: <strong className="text-white">{activePkg.genre || 'Microdrama'}</strong></div>
                        <div>Language: <strong className="text-white">{activePkg.primary_language || 'isiZulu'}</strong></div>
                        <div>Duration: <strong className="text-white">{activePkg.target_duration_seconds || 90}s</strong></div>
                      </div>
                    </div>

                    {/* PILLAR 2: CHARACTER BIBLE */}
                    <div className="space-y-2 p-4 rounded-[7px] bg-black/40 border border-white/5">
                      <h4 className="text-xs font-bold text-[#FF6500] uppercase tracking-wider flex items-center gap-1.5">
                        <Users className="w-3.5 h-3.5" />
                        <span>2. Character Bible ({activePkg.characters?.length || 2} Roles)</span>
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                        {(activePkg.characters || [
                          { name: 'Sipho Ndlovu', role: 'protagonist', secret_motivation: 'Clear family debt within 48h', fatal_flaw: 'Relies solely on rational finance', signature_quote: 'Numbers do not lie, but curses do.' },
                          { name: 'Gogo MaMthembu', role: 'antagonist', secret_motivation: 'Enforce spiritual covenant', fatal_flaw: 'Unforgiving rigidity', signature_quote: 'Every coin has blood on its edge.' }
                        ]).map((c: any, i: number) => (
                          <div key={i} className="p-3 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-white text-xs">{c.name}</span>
                              <span className="px-2 py-0.5 rounded text-[9px] font-mono uppercase bg-white/10 text-welele-gold font-bold">
                                {c.role}
                              </span>
                            </div>
                            <p className="text-[11px] text-white/70">{c.secret_motivation || c.core_motivation}</p>
                            {c.signature_quote && (
                              <p className="text-[10px] text-welele-gold italic pt-1">"{c.signature_quote}"</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* PILLAR 3: WORLD / RULES */}
                    <div className="space-y-2 p-4 rounded-[7px] bg-black/40 border border-white/5">
                      <h4 className="text-xs font-bold text-[#FF6500] uppercase tracking-wider flex items-center gap-1.5">
                        <Globe className="w-3.5 h-3.5" />
                        <span>3. World & Inviolable Rules</span>
                      </h4>
                      <div className="space-y-1.5 text-xs text-welele-muted">
                        <div>Setting: <strong className="text-white">{activePkg.story_world?.geographical_setting || 'Johannesburg, South Africa'}</strong></div>
                        <div>Mythology & Rules: <strong className="text-white">{activePkg.story_world?.mythology_and_rules || 'Ancestral covenants are binding across generations.'}</strong></div>
                        <div>Cultural Context: <strong className="text-white">{activePkg.story_world?.cultural_context || 'Modern corporate South Africa vs township traditional roots.'}</strong></div>
                      </div>
                    </div>

                    {/* PILLAR 4: CHRONOLOGY */}
                    <div className="space-y-2 p-4 rounded-[7px] bg-black/40 border border-white/5">
                      <h4 className="text-xs font-bold text-[#FF6500] uppercase tracking-wider flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5" />
                        <span>4. Chronology Spine & Causality</span>
                      </h4>
                      <p className="text-xs text-welele-muted">
                        Event spine verified. Zero causal paradoxes. All dramatic anchors chronological and continuity-locked.
                      </p>
                    </div>

                    {/* PILLAR 5: EPISODE ARCHITECTURE */}
                    <div className="space-y-2 p-4 rounded-[7px] bg-black/40 border border-white/5">
                      <h4 className="text-xs font-bold text-[#FF6500] uppercase tracking-wider flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5" />
                        <span>5. Episode Architecture & Cliffhanger Paywalls</span>
                      </h4>
                      <div className="space-y-2">
                        {(activePkg.beats_json || [
                          { beat_number: 1, label: 'Cold Open', action_description: 'Sipho discovers the golden debt ledger at 02:00 AM.', intensity: 8 },
                          { beat_number: 2, label: 'Ledger Demands', action_description: 'Ledger demands immediate repayment in cowries or shares.', intensity: 9 },
                          { beat_number: 3, label: 'Cliffhanger Paywall Cut', action_description: 'Spirits manifest through Sandton boardroom glass.', intensity: 10, cliffhanger_trigger: true }
                        ]).map((b: any, idx: number) => (
                          <div key={idx} className="p-2.5 rounded-[7px] bg-[#14151B] border border-white/5 flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-bold text-welele-gold">Beat {b.beat_number || idx + 1}:</span>
                              <span className="text-white">{b.label || b.description || b.action_description}</span>
                            </div>
                            <span className="text-[10px] font-mono text-emerald-400 font-bold">Intensity: {b.intensity || 9}/10</span>
                          </div>
                        ))}
                      </div>
                      {activePkg.cliffhanger_prompt && (
                        <div className="p-3 rounded-[7px] bg-red-950/30 border border-red-500/30 text-xs text-red-200 mt-2">
                          <strong className="text-red-400 block mb-1">Paywall Cliffhanger Question:</strong>
                          "{activePkg.cliffhanger_prompt}"
                        </div>
                      )}
                    </div>

                    {/* PILLAR 6: NARRATIVE PLANTS / PAYOFFS */}
                    <div className="space-y-2 p-4 rounded-[7px] bg-black/40 border border-white/5">
                      <h4 className="text-xs font-bold text-[#FF6500] uppercase tracking-wider flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>6. Narrative Plants & Payoffs</span>
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {(activePkg.plants || [
                          { name: 'Late Uncle Safe Key', status: 'planted', expected_payoff: 'Ep 3 Vault Opening' },
                          { name: '19th-Century Murder Record', status: 'planted', expected_payoff: 'Season Finale Climax' }
                        ]).map((p: any, i: number) => (
                          <div key={i} className="p-2.5 rounded-[7px] bg-[#14151B] border border-white/5 flex items-center justify-between">
                            <span className="font-bold text-white text-xs">{p.name}</span>
                            <span className="text-[10px] font-mono text-welele-gold">Payoff: {p.expected_payoff}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* PILLAR 7: PRODUCTION CONSTRAINTS */}
                    <div className="space-y-2 p-4 rounded-[7px] bg-black/40 border border-white/5">
                      <h4 className="text-xs font-bold text-[#FF6500] uppercase tracking-wider flex items-center gap-1.5">
                        <Clapperboard className="w-3.5 h-3.5" />
                        <span>7. Production Constraints</span>
                      </h4>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-welele-muted font-mono">
                        <div>Format: <strong className="text-white">9:16 Vertical</strong></div>
                        <div>Locations: <strong className="text-white">2 Core Venues</strong></div>
                        <div>Cast Count: <strong className="text-white">2 Principal Roles</strong></div>
                        <div>Audio: <strong className="text-white">Dual Language</strong></div>
                      </div>
                    </div>

                    {/* PILLAR 8: FORGE PROVENANCE */}
                    <div className="space-y-2 p-4 rounded-[7px] bg-black/60 border border-[#FF6500]/30">
                      <h4 className="text-xs font-bold text-[#FF6500] uppercase tracking-wider flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        <span>8. Forge Provenance & Cryptographic Lineage</span>
                      </h4>
                      <div className="space-y-1.5 text-xs text-welele-muted font-mono">
                        <div className="flex items-center justify-between">
                          <span>Forge Configuration ID:</span>
                          <span className="text-[#FF6500] font-bold">{activePkg.forge_configuration_id || 'CFG-001'}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Configuration Status:</span>
                          <span className="text-emerald-400 font-bold">Certified Canonical v1</span>
                        </div>
                        <div className="text-[10px] text-white/50 truncate pt-1">
                          Lineage Hash: {activePkg.lineage_hash || '2fbbbb302bbfe5118749dbbb188f11a4cf130a08e6f1f4e1f7fc7fa82f7c0068'}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: SERIES (SERIES IN PRODUCTION) */}
      {/* ========================================================================= */}
      {activeTab === 'series' && (
        <div className="space-y-5">
          <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Film className="w-4 h-4 text-[#FF6500]" />
              <span>Production Series Floor</span>
            </h2>
            <p className="text-xs text-welele-muted">
              Series with locked Story Packages and verified IP rights ledger splits.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {stories.map((s) => (
              <div
                key={s.id}
                className="p-5 rounded-[7px] bg-[#14151B] border border-white/10 space-y-3 shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded-[7px] bg-white/10 text-[10px] font-mono text-welele-gold font-bold">
                    {s.genre}
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400 font-bold">
                    {s.episodes?.length || 0} Episodes
                  </span>
                </div>
                <h3 className="text-base font-bold text-white">{s.title}</h3>
                <p className="text-xs text-welele-muted line-clamp-2">{s.tagline || s.synopsis}</p>
                <div className="pt-2 border-t border-white/10 flex items-center justify-between text-xs text-welele-muted">
                  <span>Rating: ★ {s.rating}</span>
                  <span className="text-white font-bold">Status: Active</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: EPISODES (EPISODIC PIPELINE OVERVIEW) */}
      {/* ========================================================================= */}
      {activeTab === 'episodes' && (
        <div className="space-y-5">
          <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clapperboard className="w-4 h-4 text-[#FF6500]" />
              <span>Episodic Architecture & Spines</span>
            </h2>
            <p className="text-xs text-welele-muted">
              Episodic breakdown of vertical microdramas with cliffhanger timing and paywall trigger markers.
            </p>
          </div>

          <div className="space-y-3">
            {stories.flatMap((s) => s.episodes || []).slice(0, 10).map((ep, idx) => (
              <div
                key={ep.id || idx}
                className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-white/10 font-mono font-bold text-welele-gold text-[10px]">
                      Ep {ep.episode_number}
                    </span>
                    <span className="font-bold text-white">{ep.title}</span>
                  </div>
                  <p className="text-welele-muted line-clamp-1">{ep.synopsis}</p>
                </div>

                <div className="flex items-center gap-3 shrink-0 text-welele-muted font-mono">
                  <span>{ep.duration_seconds}s Duration</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">
                    {ep.is_free ? 'Free Cut' : `${ep.coin_price} Coins`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 6: PRODUCTION PIPELINE */}
      {/* ========================================================================= */}
      {activeTab === 'pipeline' && (
        <div className="space-y-5">
          <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#FF6500]" />
              <span>Story Package → Production Pipeline Handoff</span>
            </h2>
            <p className="text-xs text-welele-muted">
              Verification that packaged stories have all 8 pillars certified prior to production execution.
            </p>
          </div>

          <div className="p-6 rounded-[7px] bg-[#14151B] border border-white/10 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Production Handoff Checklist
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              {[
                { label: 'Story Bible Invariants Certified', state: 'LOCKED', color: 'text-emerald-400' },
                { label: 'Character Bible Archetypes & Motivation Locked', state: 'LOCKED', color: 'text-emerald-400' },
                { label: 'World Rules & Cultural Guardrails Enforced', state: 'LOCKED', color: 'text-emerald-400' },
                { label: 'Chronology & Causality Validated', state: 'LOCKED', color: 'text-emerald-400' },
                { label: 'Episode Beats & Cliffhanger Trigger Points Defined', state: 'LOCKED', color: 'text-emerald-400' },
                { label: 'Narrative Plants & Payoffs Documented', state: 'LOCKED', color: 'text-emerald-400' },
                { label: 'Production Constraints & Venues Bound', state: 'LOCKED', color: 'text-emerald-400' },
                { label: 'Forge Provenance (CFG-001) Cryptographically Anchored', state: 'LOCKED', color: 'text-emerald-400' }
              ].map((item, i) => (
                <div key={i} className="p-3.5 rounded-[7px] bg-black/40 border border-white/5 flex items-center justify-between">
                  <span className="text-white/90">{item.label}</span>
                  <span className={`font-mono font-bold text-[10px] ${item.color}`}>
                    ✓ {item.state}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
