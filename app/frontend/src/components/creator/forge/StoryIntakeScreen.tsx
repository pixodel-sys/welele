import React, { useState, useEffect } from 'react';
import { storyForgeApi } from '../../../services/storyForgeApi';
import { StorySummary } from '../../../types/storyForge';
import {
  Sparkles,
  Flame,
  PlusCircle,
  FolderOpen,
  ArrowRight,
  BookOpen,
  Clapperboard,
  Layers,
  Globe,
  RefreshCw,
  AlertCircle
} from 'lucide-react';

interface StoryIntakeScreenProps {
  onStoryCreated: (storyId: string, initialPremise?: string) => void;
  onResumeStory: (storyId: string) => void;
}

export const StoryIntakeScreen: React.FC<StoryIntakeScreenProps> = ({
  onStoryCreated,
  onResumeStory,
}) => {
  const [activeTab, setActiveTab] = useState<'new' | 'resume'>('new');
  
  // New Story Form States
  const [title, setTitle] = useState('');
  const [premise, setPremise] = useState('');
  const [creativeObjective, setCreativeObjective] = useState('');
  const [productionObjective, setProductionObjective] = useState('');
  const [primaryLanguage, setPrimaryLanguage] = useState('isiZulu');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Resume Stories State
  const [existingStories, setExistingStories] = useState<StorySummary[]>([]);
  const [isLoadingStories, setIsLoadingStories] = useState(false);

  useEffect(() => {
    if (activeTab === 'resume') {
      loadStories();
    }
  }, [activeTab]);

  const loadStories = async () => {
    setIsLoadingStories(true);
    try {
      const list = await storyForgeApi.listStories();
      setExistingStories(list);
    } catch (e: any) {
      console.warn('Could not load existing stories:', e);
    } finally {
      setIsLoadingStories(false);
    }
  };

  const handleCreateStory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !premise.trim()) {
      setErrorMessage('Please provide both a Title and a starting Premise.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const created = await storyForgeApi.createStory({
        title: title.trim(),
        owner_id: 'creator_current',
        logline: premise.trim(),
        primary_language: primaryLanguage,
      });

      onStoryCreated(created.story_id, premise.trim());
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to create story on Forge backend';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 space-y-6">
      {/* Top Banner */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FF6500]/10 border border-[#FF6500]/30 text-[#FF6500] text-xs font-mono font-bold uppercase tracking-wider">
          <Flame className="w-3.5 h-3.5" />
          <span>Story Forge™ Internal Narrative Reasoning</span>
          <span className="text-[11px] font-mono text-white/50 border-l border-white/20 pl-2">Forge Configuration: CFG-001</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-white font-sans tracking-tight">
          Creator Story Cockpit
        </h1>
        <p className="text-sm text-white/60 max-w-lg mx-auto">
          Begin with a raw premise or seed. The Forge kernel will discover characters, world rules, and episodic spines under your creative authority.
        </p>
      </div>

      {/* Mode Switcher */}
      <div className="flex items-center justify-center">
        <div className="p-1 rounded-xl bg-black/40 border border-white/10 flex items-center gap-1">
          <button
            onClick={() => setActiveTab('new')}
            className={`px-5 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'new'
                ? 'bg-[#FF6500] text-black shadow-lg shadow-[#FF6500]/25'
                : 'text-white/60 hover:text-white'
            }`}
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Start a New Story</span>
          </button>
          <button
            onClick={() => setActiveTab('resume')}
            className={`px-5 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'resume'
                ? 'bg-[#FF6500] text-black shadow-lg shadow-[#FF6500]/25'
                : 'text-white/60 hover:text-white'
            }`}
          >
            <FolderOpen className="w-3.5 h-3.5" />
            <span>Resume Existing Story</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-200 text-xs flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <p>{errorMessage}</p>
        </div>
      )}

      {/* TAB 1: NEW STORY (Blank Canvas) */}
      {activeTab === 'new' && (
        <form
          onSubmit={handleCreateStory}
          className="bg-[#12131C] border border-white/10 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-5"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-white/80 mb-1.5">
                Story Title <span className="text-[#FF6500]">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. The Wrong Funeral"
                className="w-full px-4 py-3 rounded-xl bg-black/60 border border-white/15 focus:border-[#FF6500] focus:ring-1 focus:ring-[#FF6500] text-white text-sm placeholder-white/20 outline-none transition-all"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-white/80 mb-1.5">
                Raw Story Material / Starting Premise <span className="text-[#FF6500]">*</span>
              </label>
              <textarea
                value={premise}
                onChange={(e) => setPremise(e.target.value)}
                rows={4}
                placeholder="e.g. A man arrives at a funeral expecting to mourn his uncle. He quickly realises he is at the wrong funeral. Before he can leave, the family mistakes him for someone they have been waiting for."
                className="w-full px-4 py-3 rounded-xl bg-black/60 border border-white/15 focus:border-[#FF6500] focus:ring-1 focus:ring-[#FF6500] text-white text-sm placeholder-white/20 outline-none transition-all resize-none leading-relaxed"
                required
              />
              <p className="text-[11px] text-white/40 mt-1 font-mono">
                The submission can be deliberately sparse. The Forge will formulate questions to resolve missing invariants.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono font-bold uppercase tracking-wider text-white/70 mb-1.5">
                  Creative Objective (Optional)
                </label>
                <input
                  type="text"
                  value={creativeObjective}
                  onChange={(e) => setCreativeObjective(e.target.value)}
                  placeholder="e.g. South African supernatural comedy / vertical microdrama"
                  className="w-full px-4 py-2.5 rounded-xl bg-black/60 border border-white/15 focus:border-[#FF6500] text-white text-xs placeholder-white/20 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold uppercase tracking-wider text-white/70 mb-1.5">
                  Production Objective (Optional)
                </label>
                <input
                  type="text"
                  value={productionObjective}
                  onChange={(e) => setProductionObjective(e.target.value)}
                  placeholder="e.g. Low budget, primarily one funeral venue, episodic cliffhangers"
                  className="w-full px-4 py-2.5 rounded-xl bg-black/60 border border-white/15 focus:border-[#FF6500] text-white text-xs placeholder-white/20 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-white/70 mb-1.5">
                Primary Language
              </label>
              <select
                value={primaryLanguage}
                onChange={(e) => setPrimaryLanguage(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-black/60 border border-white/15 text-white text-xs outline-none"
              >
                <option value="isiZulu">isiZulu</option>
                <option value="English">English</option>
                <option value="isiXhosa">isiXhosa</option>
                <option value="Sesotho">Sesotho</option>
                <option value="Setswana">Setswana</option>
              </select>
            </div>
          </div>

          <div className="pt-4 border-t border-white/5 flex items-center justify-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#FF6500] to-[#FF8500] hover:from-[#FF7500] hover:to-[#FF9500] disabled:opacity-40 text-black font-black text-xs uppercase tracking-wider transition-all flex items-center gap-2 shadow-xl shadow-[#FF6500]/20 active:scale-98"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Initializing Forge Session...</span>
                </>
              ) : (
                <>
                  <span>Enter Forge Session</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      )}

      {/* TAB 2: RESUME STORY */}
      {activeTab === 'resume' && (
        <div className="bg-[#12131C] border border-white/10 rounded-2xl p-6 shadow-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-white/80 font-mono">
              Saved Forge Stories ({existingStories.length})
            </h3>
            <button
              onClick={loadStories}
              disabled={isLoadingStories}
              className="text-xs text-white/50 hover:text-white flex items-center gap-1"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingStories ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          {isLoadingStories ? (
            <div className="py-12 text-center text-xs text-white/40 font-mono">
              Loading stories from Forge engine...
            </div>
          ) : existingStories.length === 0 ? (
            <div className="py-12 text-center text-xs text-white/40 font-mono space-y-2">
              <p>No existing stories found on this backend.</p>
              <button
                onClick={() => setActiveTab('new')}
                className="text-[#FF6500] hover:underline font-bold"
              >
                Create your first story →
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {existingStories.map((s) => (
                <div
                  key={s.id}
                  onClick={() => onResumeStory(s.id)}
                  className="p-4 rounded-xl bg-black/40 border border-white/10 hover:border-[#FF6500]/60 transition-all cursor-pointer group flex flex-col justify-between"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="px-2 py-0.5 rounded bg-white/10 text-white/80 font-bold">
                        v{s.current_state_version}
                      </span>
                      <span className="text-emerald-400 font-semibold">{s.status}</span>
                    </div>
                    <h4 className="text-base font-black text-white group-hover:text-[#FF6500] truncate">
                      {s.title}
                    </h4>
                    {s.logline && (
                      <p className="text-xs text-white/60 line-clamp-2 leading-relaxed">
                        {s.logline}
                      </p>
                    )}
                  </div>
                  <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-xs text-[#FF6500] font-bold">
                    <span>Resume Cockpit</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
