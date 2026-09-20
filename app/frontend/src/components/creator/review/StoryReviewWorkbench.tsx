import React, { useState, useEffect } from 'react';
import { useApp } from '../../../context/AppContext';
import { storyReviewApi } from '../../../services/storyReviewApi';
import { StoryDraft, StoryReviewDiagnostic as DiagnosticType, CreatorSubmission } from '../../../types/storyReview';
import { StoryReviewIntake } from './StoryReviewIntake';
import { StoryReviewDiagnostic } from './StoryReviewDiagnostic';
import { GreenlightSubmitModal } from './GreenlightSubmitModal';
import {
  Sparkles,
  BookOpen,
  Send,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Plus,
  RotateCcw,
  FileText,
  Layers,
  ArrowRight,
  TrendingUp,
  AlertCircle
} from 'lucide-react';

const DEFAULT_DRAFT: StoryDraft = {
  title: 'The Ancestral Ledger',
  logline: 'When a modern Johannesburg accountant discovers an ancient spiritual ledger detailing unpayable ancestral debts, he must outwit both township loan sharks and ancestral spirits before his family name is erased.',
  target_format: 'VERTICAL_MICRODRAMA',
  tone: 'Supernatural Comedy / High Stakes Thriller',
  themes: ['Ancestral Duty', 'Modern Finance', 'Family Honor'],
  protagonist_name: 'Sipho Ndlovu',
  protagonist_want: 'Clear his family debt within 48 hours to secure a major corporate promotion.',
  protagonist_need: 'Accept his ancestral heritage and reconcile with his estranged grandmother.',
  counterforce_or_antagonist: 'Gogo MaMthembu (ancestral debt keeper) and Bra Mike (ruthless cash loan boss)',
  world_setting: 'Modern Sandton corporate offices juxtaposed against an ancient ancestral shrine in Soweto',
  episode_hooks: [
    'Ep 1 Hook: Sipho receives a gold ledger stamped with his late grandfather blood print.',
    'Ep 2 Hook: Bra Mike henchmen corner Sipho, only for the lights to shatter as spirits intervene.',
    'Ep 3 Hook: Sipho discovers the debt requires a living sacrifice—or solving a 19th-century murder.'
  ],
  full_draft_text: 'ACT I: Sipho is on the verge of making partner at a Sandton accounting firm. His estranged uncle passes away, leaving him a mysterious locked safe deposit box. Inside is a glowing, leather-bound ledger written in isiZulu and high financial accounting notation.',
  version: 1,
};

export const StoryReviewWorkbench: React.FC = () => {
  const { user } = useApp();
  const creatorId = user?.id || 'creator_zola';
  const creatorName = user?.name || 'Zola Dlamini';

  // Sub-tabs
  const [activeTab, setActiveTab] = useState<'draft' | 'diagnostic' | 'submissions'>('draft');

  // State
  const [drafts, setDrafts] = useState<StoryDraft[]>([]);
  const [activeDraft, setActiveDraft] = useState<StoryDraft>(DEFAULT_DRAFT);
  const [diagnostic, setDiagnostic] = useState<DiagnosticType | null>(null);
  const [submissions, setSubmissions] = useState<CreatorSubmission[]>([]);

  // Loading flags
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isDiagnosing, setIsDiagnosing] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState<boolean>(false);
  const [feedbackNotice, setFeedbackNotice] = useState<{ message: string; type: 'success' | 'info' } | null>(null);

  // Load existing drafts & submissions on mount
  useEffect(() => {
    loadDrafts();
    loadSubmissions();
  }, [creatorId]);

  const loadDrafts = async () => {
    try {
      const list = await storyReviewApi.getDrafts(creatorId);
      if (list && list.length > 0) {
        setDrafts(list);
        setActiveDraft(list[0]);
      } else {
        // Save initial default draft if empty
        const created = await storyReviewApi.saveDraft({ ...DEFAULT_DRAFT, creator_id: creatorId, creator_name: creatorName });
        if (created && created.draft) {
          setDrafts([created.draft]);
          setActiveDraft(created.draft);
        }
      }
    } catch (e) {
      console.warn('Could not load drafts:', e);
    }
  };

  const loadSubmissions = async () => {
    try {
      const subs = await storyReviewApi.getSubmissions(creatorId);
      if (subs) {
        setSubmissions(subs);
      }
    } catch (e) {
      console.warn('Could not load submissions:', e);
    }
  };

  const showNotification = (msg: string, type: 'success' | 'info' = 'success') => {
    setFeedbackNotice({ message: msg, type });
    setTimeout(() => setFeedbackNotice(null), 4000);
  };

  const handleSaveDraft = async () => {
    setIsSaving(true);
    try {
      const res = await storyReviewApi.saveDraft({
        ...activeDraft,
        creator_id: creatorId,
        creator_name: creatorName,
      });
      if (res && res.draft) {
        setActiveDraft(res.draft);
        // update drafts list
        setDrafts((prev) => {
          const idx = prev.findIndex((d) => d.id === res.draft.id);
          if (idx >= 0) {
            const copy = [...prev];
            copy[idx] = res.draft;
            return copy;
          }
          return [res.draft, ...prev];
        });
        showNotification('Story draft saved successfully.');
      }
    } catch (e) {
      console.error('Save draft error:', e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRunDiagnostic = async () => {
    setIsDiagnosing(true);
    try {
      // Auto-save first
      await storyReviewApi.saveDraft({
        ...activeDraft,
        creator_id: creatorId,
        creator_name: creatorName,
      });

      const diag = await storyReviewApi.diagnoseStory(activeDraft);
      setDiagnostic(diag);
      setActiveTab('diagnostic');
      showNotification('Story Review™ diagnostic analysis complete!');
    } catch (e) {
      console.error('Diagnostic error:', e);
    } finally {
      setIsDiagnosing(false);
    }
  };

  const handleCreateNewDraft = () => {
    const newDraft: StoryDraft = {
      title: 'Untitled Vertical Story',
      logline: '',
      target_format: 'VERTICAL_MICRODRAMA',
      tone: 'Drama',
      themes: [],
      protagonist_name: '',
      protagonist_want: '',
      protagonist_need: '',
      counterforce_or_antagonist: '',
      world_setting: '',
      episode_hooks: [],
      full_draft_text: '',
      version: 1,
      creator_id: creatorId,
      creator_name: creatorName,
    };
    setActiveDraft(newDraft);
    setDiagnostic(null);
    setActiveTab('draft');
  };

  const handleConfirmSubmitForGreenlight = async (creatorNotes: string) => {
    setIsSubmitting(true);
    try {
      const sub = await storyReviewApi.submitPitch({
        draft_id: activeDraft.id || activeDraft.draft_id,
        creator_id: creatorId,
        creator_name: creatorName,
        title: activeDraft.title,
        logline: activeDraft.logline,
        target_format: activeDraft.target_format,
        diagnostic_score: diagnostic?.readiness_score || 70,
        creator_notes: creatorNotes,
        pitch_package: {
          synopsis: activeDraft.logline,
          target_audience: 'African mobile-first 9:16 audience',
          primary_locations: activeDraft.world_setting,
          estimated_episodes: (activeDraft.episode_hooks?.length || 0) > 0 ? activeDraft.episode_hooks.length : 6,
          key_characters: [
            {
              name: activeDraft.protagonist_name || 'Protagonist',
              role: 'Protagonist',
              arc: `Want: ${activeDraft.protagonist_want} | Need: ${activeDraft.protagonist_need}`
            }
          ]
        }
      });

      if (sub && sub.submission_id) {
        setIsSubmitModalOpen(false);
        setSubmissions((prev) => [sub, ...prev]);
        setActiveTab('submissions');
        showNotification(`🎉 Submitted "${activeDraft.title}" to the Welele IP Pipeline! Status: SUBMITTED_FOR_REVIEW`);
      }
    } catch (e) {
      console.error('Submit pitch error:', e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 pb-24 text-white animate-fade-in max-w-7xl mx-auto">
      {/* ========================================================================= */}
      {/* HEADER BANNER: STORY REVIEW™ CREATOR ASSISTANT & GREENLIGHT GATEWAY */}
      {/* ========================================================================= */}
      <div className="p-5 rounded-[7px] bg-gradient-to-r from-[#181924] via-[#101116] to-[#181924] border border-white/10 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-[7px] bg-gradient-to-tr from-welele-orange to-amber-500 flex items-center justify-center text-black font-black text-xl shadow-lg shrink-0">
            <Sparkles className="w-6 h-6 fill-black" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-black text-white font-cinematic">Story Review™</h1>
              <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                CREATOR ASSISTANT
              </span>
              <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-white/5 text-welele-muted border border-white/10">
                IP PIPELINE GATEWAY
              </span>
            </div>
            <p className="text-xs text-welele-muted mt-0.5">
              Diagnose, strengthen, structure and prepare your original stories for Welele Greenlight review.
            </p>
          </div>
        </div>

        {/* Global Action Tools */}
        <div className="flex items-center gap-2.5 flex-wrap w-full md:w-auto justify-end">
          <button
            onClick={handleCreateNewDraft}
            className="px-3.5 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5 text-welele-orange" />
            <span>New Story</span>
          </button>

          {diagnostic && (
            <button
              onClick={() => setIsSubmitModalOpen(true)}
              className="px-4 py-2 rounded-[7px] bg-gradient-to-r from-emerald-500 to-teal-400 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-500/20 hover:opacity-95 transition-all cursor-pointer"
            >
              <ShieldCheck className="w-4 h-4 font-bold" />
              <span>Submit for Greenlight</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Notification Toast */}
      {feedbackNotice && (
        <div className="p-3 rounded-[7px] bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedbackNotice.message}</span>
        </div>
      )}

      {/* Persistent Workbench Navigation Bar */}
      <div className="flex items-center justify-between border-b border-white/10 pb-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('draft')}
            className={`px-4 py-2 rounded-[7px] font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'draft'
                ? 'bg-welele-orange text-black shadow-md'
                : 'text-welele-muted hover:text-white hover:bg-white/5'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>1. Story Draft</span>
          </button>

          <button
            onClick={() => {
              if (diagnostic) {
                setActiveTab('diagnostic');
              } else {
                handleRunDiagnostic();
              }
            }}
            className={`px-4 py-2 rounded-[7px] font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'diagnostic'
                ? 'bg-welele-orange text-black shadow-md'
                : 'text-welele-muted hover:text-white hover:bg-white/5'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span>2. Diagnostic Review {diagnostic ? `(${diagnostic.readiness_score}%)` : ''}</span>
          </button>

          <button
            onClick={() => setActiveTab('submissions')}
            className={`px-4 py-2 rounded-[7px] font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'submissions'
                ? 'bg-welele-orange text-black shadow-md'
                : 'text-welele-muted hover:text-white hover:bg-white/5'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>3. Submissions & IP Pipeline ({submissions.length})</span>
          </button>
        </div>

        {/* Active Draft Selector */}
        {drafts.length > 1 && (
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-welele-muted font-bold">Active Story:</span>
            <select
              value={activeDraft.id || ''}
              onChange={(e) => {
                const found = drafts.find((d) => d.id === e.target.value);
                if (found) {
                  setActiveDraft(found);
                  setDiagnostic(null);
                }
              }}
              className="px-2.5 py-1 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs focus:border-welele-orange focus:outline-none"
            >
              {drafts.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* ACTIVE TAB CONTENT */}
      {/* ========================================================================= */}

      {/* TAB 1: STORY DRAFT */}
      {activeTab === 'draft' && (
        <StoryReviewIntake
          draft={activeDraft}
          onChange={setActiveDraft}
          onSave={handleSaveDraft}
          onDiagnose={handleRunDiagnostic}
          isSaving={isSaving}
          isDiagnosing={isDiagnosing}
        />
      )}

      {/* TAB 2: DIAGNOSTIC REVIEW */}
      {activeTab === 'diagnostic' && (
        diagnostic ? (
          <StoryReviewDiagnostic
            diagnostic={diagnostic}
            onEditDraft={() => setActiveTab('draft')}
            onRerunDiagnostic={handleRunDiagnostic}
            onSubmitForGreenlight={() => setIsSubmitModalOpen(true)}
            isDiagnosing={isDiagnosing}
          />
        ) : (
          <div className="p-12 text-center rounded-[7px] bg-[#14151C] border border-white/10 space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">No Diagnostic Run Yet</h3>
            <p className="text-xs text-welele-muted max-w-md mx-auto">
              Run the Story Review™ diagnostic on &quot;{activeDraft.title}&quot; to receive your 4-dimension readiness score and editorial coaching.
            </p>
            <button
              onClick={handleRunDiagnostic}
              disabled={isDiagnosing}
              className="px-4 py-2 rounded-[7px] bg-welele-orange text-black font-extrabold text-xs inline-flex items-center gap-2 cursor-pointer shadow-md"
            >
              <Sparkles className="w-4 h-4 fill-black" />
              <span>{isDiagnosing ? 'Analyzing Story...' : 'Run Story Review™ Diagnostic'}</span>
            </button>
          </div>
        )
      )}

      {/* TAB 3: SUBMISSIONS & IP PIPELINE */}
      {activeTab === 'submissions' && (
        <div className="space-y-4">
          <div className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                IP Pipeline Intake Roster
              </h3>
              <p className="text-xs text-welele-muted mt-0.5">
                Official intake records submitted for Welele editorial review and Story Forge™ development.
              </p>
            </div>
            <button
              onClick={() => {
                setActiveTab('draft');
                setIsSubmitModalOpen(true);
              }}
              className="px-3.5 py-1.5 rounded-[7px] bg-gradient-to-r from-emerald-500 to-teal-400 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-md cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Submit Current Draft</span>
            </button>
          </div>

          {submissions.length === 0 ? (
            <div className="p-12 text-center rounded-[7px] bg-[#14151C] border border-white/10 space-y-3">
              <Clock className="w-10 h-10 text-zinc-600 mx-auto" />
              <h4 className="text-sm font-bold text-zinc-400">No Submissions in IP Pipeline Yet</h4>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                Once your story achieves a high Readiness Score in Story Review™, click &quot;Submit for Greenlight&quot; to enter the editorial pipeline.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {submissions.map((sub) => (
                <div
                  key={sub.submission_id}
                  className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 hover:border-emerald-500/30 transition-all space-y-2.5"
                >
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2.5">
                      <span className="font-extrabold text-sm text-white">{sub.title}</span>
                      <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono">
                        {sub.status}
                      </span>
                    </div>
                    <span className="text-[11px] text-welele-muted font-mono">
                      ID: {sub.submission_id} • {new Date(sub.submitted_at).toLocaleDateString()}
                    </span>
                  </div>

                  <p className="text-xs text-zinc-300">
                    {sub.submission_package?.synopsis || 'Narrative pitch package under editorial triage.'}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-welele-muted pt-2 border-t border-white/5">
                    <div className="flex items-center gap-3">
                      <span>Creator: <strong className="text-white">{sub.creator_name}</strong></span>
                      <span>•</span>
                      <span>Readiness: <strong className="text-emerald-400">{sub.diagnostic_summary?.readiness_score || 70}%</strong></span>
                    </div>
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Queued for Editorial Triage
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Greenlight Submit Modal */}
      <GreenlightSubmitModal
        isOpen={isSubmitModalOpen}
        onClose={() => setIsSubmitModalOpen(false)}
        draft={activeDraft}
        diagnostic={diagnostic}
        onSubmit={handleConfirmSubmitForGreenlight}
        isSubmitting={isSubmitting}
      />
    </div>
  );
};
