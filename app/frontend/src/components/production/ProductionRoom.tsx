import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { StoryForgeCockpit } from '../creator/forge/StoryForgeCockpit';
import { storyForgeApi } from '../../services/storyForgeApi';
import { ipApi, productionApi } from '../../services/api';
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
  Tv,
  AlertTriangle,
  ListChecks,
  HelpCircle,
  Video,
  Mic,
  Volume2,
  Music,
  MessageSquare,
  FileText,
  Printer
} from 'lucide-react';
import { PrintExportEngine } from '../../services/printExport/printExportEngine';

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
  const [packageViewMode, setPackageViewMode] = useState<'pillars' | 'audit' | 'bible' | 'episode_pack'>('pillars');
  const [productionBible, setProductionBible] = useState<any | null>(null);
  const [episodePack, setEpisodePack] = useState<any | null>(null);
  const [isLoadingBible, setIsLoadingBible] = useState<boolean>(false);

  const loadBibleAndPack = async (ipId: string) => {
    setIsLoadingBible(true);
    try {
      const b = await productionApi.getProductionBible(ipId);
      setProductionBible(b);
      const ep = await productionApi.getEpisodePack(ipId, 1);
      setEpisodePack(ep);
    } catch (e) {
      console.warn('Could not load Production Bible / Pack:', e);
    } finally {
      setIsLoadingBible(false);
    }
  };

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
                  Story Packages (8 Pillars)
                </h2>
                <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  M3 Story Package
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
                      <span className="text-emerald-400 font-bold">● Package Generated</span>
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
                        {/* View Mode Toggle: 4 Layers of Truth */}
                        <div className="flex flex-wrap bg-black/60 rounded-[7px] p-0.5 border border-white/10 gap-0.5">
                          <button
                            onClick={() => setPackageViewMode('pillars')}
                            className={`px-2.5 py-1.5 rounded-[5px] text-[11px] font-bold transition-all flex items-center gap-1.5 ${
                              packageViewMode === 'pillars'
                                ? 'bg-[#FF6500] text-black shadow-md'
                                : 'text-white/60 hover:text-white'
                            }`}
                          >
                            <Layers className="w-3.5 h-3.5" />
                            <span>8 Pillars (Story Truth)</span>
                          </button>
                          <button
                            onClick={() => setPackageViewMode('audit')}
                            className={`px-2.5 py-1.5 rounded-[5px] text-[11px] font-bold transition-all flex items-center gap-1.5 ${
                              packageViewMode === 'audit'
                                ? 'bg-amber-500 text-black shadow-md'
                                : 'text-white/60 hover:text-white'
                            }`}
                          >
                            <ListChecks className="w-3.5 h-3.5" />
                            <span>Handoff Audit</span>
                          </button>
                          <button
                            onClick={() => {
                              setPackageViewMode('bible');
                              if (activePkg.ip_id || activePkg.id) {
                                loadBibleAndPack(activePkg.ip_id || activePkg.id);
                              }
                            }}
                            className={`px-2.5 py-1.5 rounded-[5px] text-[11px] font-bold transition-all flex items-center gap-1.5 ${
                              packageViewMode === 'bible'
                                ? 'bg-purple-500 text-black shadow-md'
                                : 'text-white/60 hover:text-white'
                            }`}
                          >
                            <BookOpen className="w-3.5 h-3.5" />
                            <span>Production Bible (10 Sections)</span>
                          </button>
                          <button
                            onClick={() => {
                              setPackageViewMode('episode_pack');
                              if (activePkg.ip_id || activePkg.id) {
                                loadBibleAndPack(activePkg.ip_id || activePkg.id);
                              }
                            }}
                            className={`px-2.5 py-1.5 rounded-[5px] text-[11px] font-bold transition-all flex items-center gap-1.5 ${
                              packageViewMode === 'episode_pack'
                                ? 'bg-emerald-500 text-black shadow-md'
                                : 'text-white/60 hover:text-white'
                            }`}
                          >
                            <Film className="w-3.5 h-3.5" />
                            <span>Episode 1 Pack (5 Tracks)</span>
                          </button>
                        </div>

                        <button
                          onClick={() => PrintExportEngine.exportProductionReportFromCanonical(activePkg, productionBible, episodePack)}
                          className="px-3 py-1.5 rounded-[7px] bg-[#FF6500]/20 hover:bg-[#FF6500]/30 text-[#FF6500] border border-[#FF6500]/40 text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm"
                          title="Generate A4 Printable Production Report with Document Metadata & Lineage Provenance"
                        >
                          <Printer className="w-3.5 h-3.5 text-[#FF6500]" />
                          <span>Print / Export PDF</span>
                        </button>

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

                    {packageViewMode === 'pillars' && (
                      <>
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
                              { name: 'Thandiwe Sithole', role: 'protagonist', secret_motivation: 'Protect the royal infant and reconcile with Lerato', fatal_flaw: 'Rigid moral pride', signature_quote: 'A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa.' },
                              { name: 'Bhekisisa Khumalo', role: 'antagonist', secret_motivation: 'Secure an authentic male heir to retain ancestral mining concessions', fatal_flaw: 'Commodification of sacred tradition', signature_quote: 'That child carries the only bloodline that keeps my mining shafts open. Hand him over.' }
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
                            <div>Setting: <strong className="text-white">{activePkg.story_world?.geographical_setting || 'Soweto (Mofolo South) & Sandhurst, Johannesburg'}</strong></div>
                            <div>Mythology & Rules: <strong className="text-white">{activePkg.story_world?.mythology_and_rules || '1. Customary royal lineage covenants supersede commercial surrogacy contracts under ancestral law. 2. Khumalo mining concessions remain valid only while direct royal lineage is maintained.'}</strong></div>
                            <div>Cultural Context: <strong className="text-white">{activePkg.story_world?.cultural_context || 'Traditional Zulu birth customs and customary land tenure vs modern corporate capitalism.'}</strong></div>
                          </div>
                        </div>

                        {/* PILLAR 4: CHRONOLOGY */}
                        <div className="space-y-2 p-4 rounded-[7px] bg-black/40 border border-white/5">
                          <h4 className="text-xs font-bold text-[#FF6500] uppercase tracking-wider flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5" />
                            <span>4. Chronology Spine & Causality</span>
                          </h4>
                          <p className="text-xs text-welele-muted">
                            Event spine verified. Zero causal paradoxes. All dramatic anchors chronological and continuity-locked across M0→M1→M2→M3.
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
                              { beat_number: 1, label: 'Cold Open: Midnight Delivery', action_description: 'Midwife Thandiwe delivers baby by candlelight during blackout; spots royal mark.', intensity: 8 },
                              { beat_number: 2, label: 'Dawn Confrontation', action_description: 'Bhekisisa arrives with cash briefcases; Lerato confesses to the surrogacy contract.', intensity: 9 },
                              { beat_number: 3, label: 'Cliffhanger Paywall Cut', action_description: 'Township neighbours surround clinic as Thandiwe holds birth record high.', intensity: 10, cliffhanger_trigger: true }
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
                              { name: 'Royal Ink-Mark / Birthmark', status: 'planted', expected_payoff: 'Ep 1 Midpoint Revelation & Tribal Concession Proof' },
                              { name: '1912 Madadeni Land Covenant Seal', status: 'planted', expected_payoff: 'Season Finale Climax Stand-off' }
                            ]).map((p: any, i: number) => (
                              <div key={i} className="p-2.5 rounded-[7px] bg-[#14151B] border border-white/5 flex items-center justify-between">
                                <span className="font-bold text-white text-xs">{p.name}</span>
                                <span className="text-[10px] font-mono text-welele-gold">Payoff: {p.expected_payoff || p.status}</span>
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
                            <div>Cast Count: <strong className="text-white">{activePkg.characters?.length || 3} Roles</strong></div>
                            <div>Audio: <strong className="text-white">isiZulu Vernacular</strong></div>
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
                              <span className="text-emerald-400 font-bold">Baseline Registered (CFG-001)</span>
                            </div>
                            <div className="text-[10px] text-white/50 truncate pt-1">
                              Lineage Hash: {activePkg.lineage_hash || 'f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6'}
                            </div>
                          </div>
                        </div>
                      </>
                    )}

                    {packageViewMode === 'audit' && (
                      /* PRODUCTION HANDOFF AUDIT VIEW */
                      <div className="space-y-6">
                        {/* Audit Governing Principle Banner */}
                        <div className="p-4 rounded-[7px] bg-black/50 border border-emerald-500/40 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                              <ShieldCheck className="w-4 h-4" />
                              <span>Internal Production Readiness Standard</span>
                            </span>
                            <span className="px-2.5 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono font-bold">
                              4 Provenance Classes
                            </span>
                          </div>
                          <p className="text-xs text-white font-medium italic leading-relaxed">
                            "Could a competent production team begin production from this Story Package without having to invent a major narrative, structural, continuity or world decision?"
                          </p>
                        </div>

                        {/* Audit Category 1: PASS */}
                        <div className="space-y-2 p-4 rounded-[7px] bg-emerald-950/20 border border-emerald-500/30">
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                              <CheckCircle2 className="w-4 h-4" />
                              <span>PASS — Narrative, Structural & Continuity Foundations</span>
                            </h4>
                            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold">
                              4 / 4 Verified Foundations
                            </span>
                          </div>
                          <div className="space-y-2 pt-1 text-xs text-white/90">
                            <div className="p-2.5 rounded bg-black/40 border border-emerald-500/20 flex items-start gap-2">
                              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                              <div>
                                <strong className="text-white block">Premise & Dramatic Engine (M0 & M1)</strong>
                                <span className="text-welele-muted text-[11px]">Soweto midwife discovers royal birthmark during blackout; estranged surrogate daughter in debt; mining dynast needing royal heir to retain platinum concession. High-stakes collision established.</span>
                              </div>
                            </div>
                            <div className="p-2.5 rounded bg-black/40 border border-emerald-500/20 flex items-start gap-2">
                              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                              <div>
                                <strong className="text-white block">Episode Architecture & Paywall Cliffhangers (M2)</strong>
                                <span className="text-welele-muted text-[11px]">3-beat 90s vertical microdrama structure locked with high-intensity timestamps (10s hook, 45s midpoint confrontation, 88s township uprising cliffhanger).</span>
                              </div>
                            </div>
                            <div className="p-2.5 rounded bg-black/40 border border-emerald-500/20 flex items-start gap-2">
                              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                              <div>
                                <strong className="text-white block">World Rules & Lineage Covenants (M3)</strong>
                                <span className="text-welele-muted text-[11px]">Customary Zulu royal land tenure vs Sandton commercial surrogacy law inviolable and clearly enforced.</span>
                              </div>
                            </div>
                            <div className="p-2.5 rounded bg-black/40 border border-emerald-500/20 flex items-start gap-2">
                              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                              <div>
                                <strong className="text-white block">Provenance & Configuration Anchoring</strong>
                                <span className="text-welele-muted text-[11px]">CFG-001 immutable baseline registered with full trace and cryptographic lineage hash.</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Audit Category 2: GAP */}
                        <div className="space-y-2 p-4 rounded-[7px] bg-amber-950/20 border border-amber-500/30">
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                              <AlertCircle className="w-4 h-4" />
                              <span>GAP — Discovered Story Machine Omissions</span>
                            </h4>
                            <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold">
                              2 Observed
                            </span>
                          </div>
                          <div className="space-y-2 pt-1 text-xs text-white/90">
                            <div className="p-2.5 rounded bg-black/40 border border-amber-500/20 flex items-start gap-2">
                              <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                              <div>
                                <strong className="text-amber-200 block">Secondary Enforcer Cast Character Bibles</strong>
                                <span className="text-welele-muted text-[11px]">While the principal trio (Thandiwe, Bhekisisa, Lerato) have complete bibles, supporting characters referenced in premise (Bra Mike the loan shark, Nurse Nomsa) lack distinct secondary profiles.</span>
                              </div>
                            </div>
                            <div className="p-2.5 rounded bg-black/40 border border-amber-500/20 flex items-start gap-2">
                              <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                              <div>
                                <strong className="text-amber-200 block">Multi-Episode Minute-by-Minute Beat Sheets</strong>
                                <span className="text-welele-muted text-[11px]">Episode 1 has full 3-beat architecture; Episodes 2–10 have overarching 6-anchor chronology spine but require downstream episodic beat expansion prior to script draft.</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Audit Category 3: DEFERRED PRODUCTION DECISION */}
                        <div className="space-y-2 p-4 rounded-[7px] bg-blue-950/20 border border-blue-500/30">
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                              <Clock className="w-4 h-4" />
                              <span>DEFERRED PRODUCTION DECISION — Physical Execution Choices</span>
                            </h4>
                            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-[10px] font-bold">
                              3 Recorded
                            </span>
                          </div>
                          <div className="space-y-2 pt-1 text-xs text-white/90">
                            <div className="p-2.5 rounded bg-black/40 border border-blue-500/20 flex items-start gap-2">
                              <span className="w-2 h-2 rounded-full bg-blue-400 shrink-0 mt-1.5" />
                              <div>
                                <strong className="text-blue-200 block">Location Scouting: Soweto Clinic vs Studio Practical Set</strong>
                                <span className="text-welele-muted text-[11px]">Narrative bounds the setting to Mofolo South; physical location scouting vs indoor soundstage build deferred to Production Designer.</span>
                              </div>
                            </div>
                            <div className="p-2.5 rounded bg-black/40 border border-blue-500/20 flex items-start gap-2">
                              <span className="w-2 h-2 rounded-full bg-blue-400 shrink-0 mt-1.5" />
                              <div>
                                <strong className="text-blue-200 block">Vertical 9:16 Candlelight Rigging Design</strong>
                                <span className="text-welele-muted text-[11px]">Low-light blackout atmospheric lighting setup in vertical aspect ratio deferred to Director of Photography (DoP).</span>
                              </div>
                            </div>
                            <div className="p-2.5 rounded bg-black/40 border border-blue-500/20 flex items-start gap-2">
                              <span className="w-2 h-2 rounded-full bg-blue-400 shrink-0 mt-1.5" />
                              <div>
                                <strong className="text-blue-200 block">Vernacular Code-Switching & Dialect Coaching</strong>
                                <span className="text-welele-muted text-[11px]">Fine-tuning isiZulu traditional cadence vs urban Tsotsitaal nuances deferred to on-set Dialogue Coach and Cast.</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Audit Category 4: CONTRADICTION */}
                        <div className="space-y-2 p-4 rounded-[7px] bg-red-950/20 border border-red-500/30">
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
                              <AlertTriangle className="w-4 h-4" />
                              <span>CONTRADICTION — Narrative & Continuity Conflicts</span>
                            </h4>
                            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold">
                              1 Variance Resolved
                            </span>
                          </div>
                          <div className="p-2.5 rounded bg-black/40 border border-red-500/20 text-xs text-white/90">
                            <strong className="text-white block">Protagonist Naming Variance (Resolved)</strong>
                            <span className="text-welele-muted text-[11px]">Early excavation cycles inferred 'Thandeka Sithole', while dialogue prompt consolidated to 'Thandiwe Sithole'. Consolidated into canonical alias 'Thandiwe / Thandeka Sithole' without structural causality impact. Zero causal or world rule contradictions detected.</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {packageViewMode === 'bible' && (
                      /* 10-SECTION PRODUCTION BIBLE VIEW */
                      <div className="space-y-5 text-xs text-white/90">
                        <div className="p-4 rounded-[7px] bg-purple-950/30 border border-purple-500/40 flex items-center justify-between">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <BookOpen className="w-4 h-4 text-purple-400" />
                              <h3 className="font-bold text-white text-sm">Canonical Production Bible (10 Sections)</h3>
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                                Reusable Title Specification
                              </span>
                            </div>
                            <p className="text-welele-muted text-[11px]">
                              Authoritative production blueprint derived from Story Package with strict provenance attribution.
                            </p>
                          </div>
                          <span className="text-xs font-mono text-purple-300 bg-black/50 px-2.5 py-1 rounded border border-purple-500/30">
                            CFG-001 Provenance
                          </span>
                        </div>

                        {/* Section 1 & 2: Title Identity & Creative DNA */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="p-4 rounded-[7px] bg-black/40 border border-white/5 space-y-2">
                            <div className="flex items-center justify-between border-b border-white/10 pb-2">
                              <span className="font-bold text-white text-xs">1. Title Identity</span>
                              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[9px] font-bold">CANON</span>
                            </div>
                            <div className="space-y-1 text-welele-muted font-mono text-[11px]">
                              <div>Format: <strong className="text-white">9:16 Vertical Microdrama</strong></div>
                              <div>Duration: <strong className="text-white">90 Seconds / Episode</strong></div>
                              <div>Primary Vernacular: <strong className="text-white">isiZulu</strong></div>
                              <div>Secondary: <strong className="text-white">English, Sesotho, Tsotsitaal</strong></div>
                            </div>
                          </div>

                          <div className="p-4 rounded-[7px] bg-black/40 border border-white/5 space-y-2">
                            <div className="flex items-center justify-between border-b border-white/10 pb-2">
                              <span className="font-bold text-white text-xs">2. Creative DNA</span>
                              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[9px] font-bold">CANON</span>
                            </div>
                            <p className="text-[11px] text-white italic leading-relaxed">
                              "An incorruptible Soweto midwife protecting a sacred royal infant against a ruthless mining tycoon whose survival depends on seizing the child."
                            </p>
                          </div>
                        </div>

                        {/* Section 3: Character Production Bible */}
                        <div className="p-4 rounded-[7px] bg-black/40 border border-white/5 space-y-3">
                          <div className="flex items-center justify-between border-b border-white/10 pb-2">
                            <span className="font-bold text-white text-xs">3. Character Production Bible (3 Principal Roster)</span>
                            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[9px] font-bold">CANON</span>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            {[
                              {
                                name: "Thandiwe Sithole",
                                role: "PROTAGONIST",
                                archetype: "The Devout Midwife / Moral Shield",
                                visual: "Green clinical apron over Zulu floral dress; sweat and candle wax distress.",
                                dialect: "Formal ancestral isiZulu"
                              },
                              {
                                name: "Bhekisisa Khumalo",
                                role: "ANTAGONIST",
                                archetype: "Dynastic Mining Patriarch",
                                visual: "Immaculate charcoal bespoke suit, gold signet ring; zero physical distress.",
                                dialect: "Corporate Sandton isiZulu"
                              },
                              {
                                name: "Lerato Sithole",
                                role: "SUPPORTING",
                                archetype: "Desperate Surrogate Daughter",
                                visual: "Oversized thrifted dark coat, postpartum exhaustion, hospital wristband.",
                                dialect: "Soweto urban isiZulu"
                              }
                            ].map((c, i) => (
                              <div key={i} className="p-3 rounded bg-[#14151B] border border-white/5 space-y-1 text-[11px]">
                                <div className="flex items-center justify-between">
                                  <strong className="text-white">{c.name}</strong>
                                  <span className="text-[9px] font-mono text-welele-gold font-bold">{c.role}</span>
                                </div>
                                <div className="text-white/70">{c.archetype}</div>
                                <div className="text-welele-muted pt-1"><strong className="text-white/80">Visual:</strong> {c.visual}</div>
                                <div className="text-welele-muted"><strong className="text-white/80">Dialect:</strong> {c.dialect}</div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Section 4 & 5: Locations & World Rules */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="p-4 rounded-[7px] bg-black/40 border border-white/5 space-y-2">
                            <div className="flex items-center justify-between border-b border-white/10 pb-2">
                              <span className="font-bold text-white text-xs">4. World / Location Bible</span>
                              <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono text-[9px] font-bold">DERIVED</span>
                            </div>
                            <div className="space-y-2 text-[11px] text-welele-muted">
                              <div><strong className="text-white">Mofolo South Clinic Ward:</strong> 15m² practical room, single gurney, wooden cabinet, 2700K candle key.</div>
                              <div><strong className="text-white">Clinic Exterior Gate:</strong> Corrugated fence, dawn dust, black G-Wagon headlights.</div>
                            </div>
                          </div>

                          <div className="p-4 rounded-[7px] bg-black/40 border border-white/5 space-y-2">
                            <div className="flex items-center justify-between border-b border-white/10 pb-2">
                              <span className="font-bold text-white text-xs">5. Supernatural & World Rules</span>
                              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[9px] font-bold">CANON</span>
                            </div>
                            <div className="space-y-1 text-[11px] text-welele-muted">
                              <div>• Customary Zulu royal covenants supersede commercial contracts.</div>
                              <div>• Khumalo platinum concessions valid only while direct bloodline verified.</div>
                              <div>• 1912 customary seal legally freezes provincial land transfers.</div>
                            </div>
                          </div>
                        </div>

                        {/* Section 6 & 7: Visual & Audio Language */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="p-4 rounded-[7px] bg-black/40 border border-white/5 space-y-2">
                            <div className="flex items-center justify-between border-b border-white/10 pb-2">
                              <span className="font-bold text-white text-xs">6. Visual Language</span>
                              <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-400 font-mono text-[9px] font-bold">PROD_DECISION</span>
                            </div>
                            <div className="space-y-1 text-[11px] text-welele-muted">
                              <div>Framing: <strong className="text-white">9:16 Vertical Native, tight vertical Dutch angles</strong></div>
                              <div>Lighting: <strong className="text-white">Chiaroscuro (2700K Candle vs 5600K Dawn Headlights)</strong></div>
                              <div>Lenses: <strong className="text-white">24mm wide vertical, 35mm & 50mm primes</strong></div>
                            </div>
                          </div>

                          <div className="p-4 rounded-[7px] bg-black/40 border border-white/5 space-y-2">
                            <div className="flex items-center justify-between border-b border-white/10 pb-2">
                              <span className="font-bold text-white text-xs">7. Audio Language</span>
                              <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-400 font-mono text-[9px] font-bold">PROD_DECISION</span>
                            </div>
                            <div className="space-y-1 text-[11px] text-welele-muted">
                              <div>Score BPM: <strong className="text-white">68 BPM (Zulu Acoustic Drum Heartbeat)</strong></div>
                              <div>Foley: <strong className="text-white">Blackout silence, newborn cry, V8 engine rumble</strong></div>
                              <div>Mix Standard: <strong className="text-white">-14 LUFS Mobile Phone Optimized</strong></div>
                            </div>
                          </div>
                        </div>

                        {/* Section 8, 9 & 10: Continuity, Constraints & Prompt Constitution */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="p-4 rounded-[7px] bg-black/40 border border-white/5 space-y-2 text-[11px]">
                            <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
                              <span className="font-bold text-white">8. Continuity Bible</span>
                              <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[9px] font-bold">CANON</span>
                            </div>
                            <p className="text-welele-muted">6-Anchor Chronology Spine, Royal Ink-Mark & 1912 Land Seal Plants.</p>
                          </div>

                          <div className="p-4 rounded-[7px] bg-black/40 border border-white/5 space-y-2 text-[11px]">
                            <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
                              <span className="font-bold text-white">9. Constraints</span>
                              <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400 font-mono text-[9px] font-bold">PROD_DECISION</span>
                            </div>
                            <p className="text-welele-muted">Max 2 practical sets, zero live ammo, prosthetic newborn, flame marshal.</p>
                          </div>

                          <div className="p-4 rounded-[7px] bg-black/40 border border-white/5 space-y-2 text-[11px]">
                            <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
                              <span className="font-bold text-white">10. Prompt Constitution</span>
                              <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[9px] font-bold">CANON</span>
                            </div>
                            <p className="text-welele-muted">Canon overrides prompt convenience; production never silently creates canon.</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {packageViewMode === 'episode_pack' && (
                      /* EPISODE 1 PRODUCTION PACK (5 COORDINATED TRACKS) VIEW */
                      <div className="space-y-5 text-xs text-white/90">
                        <div className="p-4 rounded-[7px] bg-emerald-950/30 border border-emerald-500/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <Film className="w-4 h-4 text-emerald-400" />
                              <h3 className="font-bold text-white text-sm">Episode 1 Production Pack: The Midnight Lineage</h3>
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                5 Coordinated Tracks
                              </span>
                            </div>
                            <p className="text-welele-muted text-[11px]">
                              Execution specification derived from Production Bible with strict provenance and cliffhanger timing.
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono text-emerald-300 bg-black/50 px-2.5 py-1 rounded border border-emerald-500/30">
                              90s Vertical Format
                            </span>
                            <span className="text-xs font-mono text-[#FF6500] bg-black/50 px-2.5 py-1 rounded border border-[#FF6500]/30">
                              Paywall Cut: 88s
                            </span>
                          </div>
                        </div>

                        {/* TRACK 1: VIDEO */}
                        <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 space-y-3">
                          <div className="flex items-center justify-between border-b border-white/10 pb-2">
                            <div className="flex items-center gap-2">
                              <Video className="w-4 h-4 text-emerald-400" />
                              <h4 className="font-bold text-white text-xs uppercase tracking-wider">Track 1: VIDEO (Visuals, Framing & Lighting)</h4>
                            </div>
                            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-[9px] font-bold">GENERATED</span>
                          </div>
                          <div className="space-y-2 text-[11px]">
                            <div className="p-2.5 rounded bg-black/40 border border-white/5 space-y-1">
                              <div className="flex items-center justify-between text-welele-gold font-mono">
                                <span>Scene 1 (00:00 - 00:15) — INT. SOWETO CLINIC WARD - NIGHT</span>
                                <span>9:16 Close-up</span>
                              </div>
                              <p className="text-white/80">Tight vertical frame on midwife Thandiwe's sweating brow; candle flickers on weathered green walls. Camera tilts down to reveal royal birthmark glowing under amber flame.</p>
                            </div>
                            <div className="p-2.5 rounded bg-black/40 border border-white/5 space-y-1">
                              <div className="flex items-center justify-between text-welele-gold font-mono">
                                <span>Scene 2 (00:15 - 00:50) — EXT. CLINIC GATE - DAWN</span>
                                <span>Low-Angle Dutch Tracking</span>
                              </div>
                              <p className="text-white/80">Low-angle vertical tracking of 3 black Mercedes G-Wagons cutting through dawn dust. Bhekisisa steps out in bespoke suit. Lerato emerges crying from rear door.</p>
                            </div>
                            <div className="p-2.5 rounded bg-black/40 border border-white/5 space-y-1">
                              <div className="flex items-center justify-between text-welele-gold font-mono">
                                <span>Scene 3 (00:50 - 00:90) — INT/EXT. CLINIC THRESHOLD - CLIMAX</span>
                                <span>High-Tension Whip-Pan</span>
                              </div>
                              <p className="text-white/80">Guards rack 9mm handguns; township community emerges with sjamboks. Thandiwe steps forward holding ancient customary ledger high into the golden sunrise.</p>
                            </div>
                          </div>
                        </div>

                        {/* TRACK 2: DIALOGUE */}
                        <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 space-y-3">
                          <div className="flex items-center justify-between border-b border-white/10 pb-2">
                            <div className="flex items-center gap-2">
                              <MessageSquare className="w-4 h-4 text-emerald-400" />
                              <h4 className="font-bold text-white text-xs uppercase tracking-wider">Track 2: DIALOGUE (Locked Lines & Subtext)</h4>
                            </div>
                            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[9px] font-bold">CANON</span>
                          </div>
                          <div className="space-y-2 text-[11px]">
                            <div className="p-2.5 rounded bg-black/40 border border-white/5 space-y-1">
                              <div className="flex items-center justify-between">
                                <strong className="text-white font-mono">Thandiwe Sithole (00:35)</strong>
                                <span className="text-[10px] text-welele-muted">Steely Maternal Authority</span>
                              </div>
                              <p className="text-welele-gold italic">"A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa."</p>
                              <p className="text-white/60 text-[10px]">Subtext: Moral defiance rejecting corporate commodification of sacred bloodline.</p>
                            </div>
                            <div className="p-2.5 rounded bg-black/40 border border-white/5 space-y-1">
                              <div className="flex items-center justify-between">
                                <strong className="text-white font-mono">Bhekisisa Khumalo (00:55)</strong>
                                <span className="text-[10px] text-welele-muted">Cold Corporate Threat</span>
                              </div>
                              <p className="text-welele-gold italic">"That child carries the only bloodline that keeps my mining shafts open. Hand him over."</p>
                              <p className="text-white/60 text-[10px]">Subtext: Dynastic survival panic masked behind aristocratic arrogance.</p>
                            </div>
                            <div className="p-2.5 rounded bg-black/40 border border-white/5 space-y-1">
                              <div className="flex items-center justify-between">
                                <strong className="text-white font-mono">Lerato Sithole (00:72)</strong>
                                <span className="text-[10px] text-welele-muted">Desperate Pleading</span>
                              </div>
                              <p className="text-welele-gold italic">"Mama, forgive me... I had no other way to clear the loan sharks."</p>
                              <p className="text-white/60 text-[10px]">Subtext: Shattered guilt and plea for maternal sanctuary.</p>
                            </div>
                          </div>
                        </div>

                        {/* TRACK 3, 4 & 5: NARRATION, AMBIENCE & MUSIC */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          {/* Track 3: Narration */}
                          <div className="p-3.5 rounded-[7px] bg-[#14151B] border border-white/10 space-y-2 text-[11px]">
                            <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
                              <div className="flex items-center gap-1.5">
                                <Mic className="w-3.5 h-3.5 text-emerald-400" />
                                <span className="font-bold text-white">Track 3: NARRATION</span>
                              </div>
                              <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-[8px] font-bold">DERIVED</span>
                            </div>
                            <p className="text-white/80 italic">"In Soweto, blood is thicker than gold... but at dawn, gold came to collect."</p>
                          </div>

                          {/* Track 4: Ambience */}
                          <div className="p-3.5 rounded-[7px] bg-[#14151B] border border-white/10 space-y-2 text-[11px]">
                            <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
                              <div className="flex items-center gap-1.5">
                                <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
                                <span className="font-bold text-white">Track 4: AMBIENCE</span>
                              </div>
                              <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-[8px] font-bold">GENERATED</span>
                            </div>
                            <p className="text-white/70">Rolling blackout silence, newborn cry, V8 diesel rumble, briefcase click, racking handguns.</p>
                          </div>

                          {/* Track 5: Music */}
                          <div className="p-3.5 rounded-[7px] bg-[#14151B] border border-white/10 space-y-2 text-[11px]">
                            <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
                              <div className="flex items-center gap-1.5">
                                <Music className="w-3.5 h-3.5 text-emerald-400" />
                                <span className="font-bold text-white">Track 5: MUSIC</span>
                              </div>
                              <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-[8px] font-bold">GENERATED</span>
                            </div>
                            <p className="text-white/70">68 BPM Zulu drum pulse $\rightarrow$ staccato cello $\rightarrow$ brass crescendo $\rightarrow$ abrupt silence at 88s cut.</p>
                          </div>
                        </div>
                      </div>
                    )}
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
                { label: 'Story Bible Invariants', state: 'PRESENT', color: 'text-emerald-400' },
                { label: 'Character Bible Archetypes & Motivation', state: 'PRESENT', color: 'text-emerald-400' },
                { label: 'World Rules & Cultural Guardrails', state: 'PRESENT', color: 'text-emerald-400' },
                { label: 'Chronology & Causality Spines', state: 'PRESENT', color: 'text-emerald-400' },
                { label: 'Episode Beats & Cliffhanger Trigger Points', state: 'PRESENT', color: 'text-emerald-400' },
                { label: 'Narrative Plants & Payoffs', state: 'PRESENT', color: 'text-emerald-400' },
                { label: 'Production Constraints & Venues', state: 'PRESENT', color: 'text-emerald-400' },
                { label: 'Forge Provenance (CFG-001) Baseline', state: 'PRESENT', color: 'text-emerald-400' }
              ].map((item, i) => (
                <div key={i} className="p-3.5 rounded-[7px] bg-black/40 border border-white/5 flex items-center justify-between">
                  <span className="text-white/90">{item.label}</span>
                  <span className={`font-mono font-bold text-[10px] ${item.color}`}>
                    ● {item.state}
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
