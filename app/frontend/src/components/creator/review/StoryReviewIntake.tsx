import React from 'react';
import { StoryDraft } from '../../../types/storyReview';
import { Sparkles, Save, BookOpen, User, Film, Plus, Trash2, MapPin, Zap } from 'lucide-react';

interface StoryReviewIntakeProps {
  draft: StoryDraft;
  onChange: (updated: StoryDraft) => void;
  onSave: () => void;
  onDiagnose: () => void;
  isSaving: boolean;
  isDiagnosing: boolean;
}

export const StoryReviewIntake: React.FC<StoryReviewIntakeProps> = ({
  draft,
  onChange,
  onSave,
  onDiagnose,
  isSaving,
  isDiagnosing,
}) => {
  const handleFieldChange = (field: keyof StoryDraft, value: any) => {
    onChange({
      ...draft,
      [field]: value,
    });
  };

  const handleAddHook = () => {
    const hooks = draft.episode_hooks || [];
    handleFieldChange('episode_hooks', [...hooks, `Episode ${hooks.length + 1} Hook: `]);
  };

  const handleUpdateHook = (index: number, val: string) => {
    const hooks = [...(draft.episode_hooks || [])];
    hooks[index] = val;
    handleFieldChange('episode_hooks', hooks);
  };

  const handleRemoveHook = (index: number) => {
    const hooks = (draft.episode_hooks || []).filter((_, i) => i !== index);
    handleFieldChange('episode_hooks', hooks);
  };

  return (
    <div className="space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-[7px] bg-[#14151C] border border-white/10">
        <div>
          <h2 className="text-base font-black text-white flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-welele-orange" />
            Story Draft & Core Architecture
          </h2>
          <p className="text-xs text-welele-muted mt-0.5">
            Craft your vertical microdrama premise, character polarity, and episodic hooks. Work is saved persistently.
          </p>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          <button
            onClick={onSave}
            disabled={isSaving}
            className="px-3.5 py-2 rounded-[7px] bg-white/10 hover:bg-white/15 border border-white/15 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5 text-welele-gold" />
            <span>{isSaving ? 'Saving...' : 'Save Draft'}</span>
          </button>
          <button
            onClick={onDiagnose}
            disabled={isDiagnosing || !draft.title.trim()}
            className="px-4 py-2 rounded-[7px] bg-gradient-to-r from-welele-orange to-amber-500 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-lg shadow-orange-500/20 hover:opacity-95 transition-all cursor-pointer disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 fill-black" />
            <span>{isDiagnosing ? 'Analyzing Story...' : 'Run Story Review™ Diagnostic'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Premise & Metadata */}
        <div className="lg:col-span-7 space-y-5">
          {/* Title & Format */}
          <div className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 text-welele-orange">
              <Film className="w-3.5 h-3.5" /> Story Identity
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2 space-y-1.5">
                <label className="text-[11px] font-bold text-welele-muted">Working Title</label>
                <input
                  type="text"
                  value={draft.title}
                  onChange={(e) => handleFieldChange('title', e.target.value)}
                  placeholder="e.g. Ancestral Debt, The Wrong Funeral..."
                  className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-welele-orange focus:outline-none"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-[11px] font-bold text-welele-muted">Format</label>
                <select
                  value={draft.target_format}
                  onChange={(e) => handleFieldChange('target_format', e.target.value)}
                  className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs focus:border-welele-orange focus:outline-none"
                >
                  <option value="VERTICAL_MICRODRAMA">Vertical Microdrama (9:16)</option>
                  <option value="SHORT_SERIES">Short Series</option>
                  <option value="FEATURE">Feature Film</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-welele-muted">High-Concept Logline / Core Hook</label>
              <textarea
                value={draft.logline}
                onChange={(e) => handleFieldChange('logline', e.target.value)}
                placeholder="A compelling 1-2 sentence hook highlighting the central disruption, stakes, and curiosity gap..."
                rows={2}
                className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-welele-orange focus:outline-none resize-none"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-[11px] font-bold text-welele-muted">Tone & Genre</label>
                <input
                  type="text"
                  value={draft.tone}
                  onChange={(e) => handleFieldChange('tone', e.target.value)}
                  placeholder="e.g. Supernatural Comedy / High Stakes Family Drama"
                  className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-welele-orange focus:outline-none"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-[11px] font-bold text-welele-muted">Production Setting & Locations</label>
                <input
                  type="text"
                  value={draft.world_setting}
                  onChange={(e) => handleFieldChange('world_setting', e.target.value)}
                  placeholder="e.g. A bustling family home & church yard in Soweto"
                  className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-welele-orange focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Full Draft / Scene Notes */}
          <div className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-white uppercase tracking-wider text-welele-orange flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5" /> Story Draft / Beat Outline
              </label>
              <span className="text-[10px] text-welele-muted font-mono">
                {draft.full_draft_text ? `${draft.full_draft_text.length} chars` : 'Optional'}
              </span>
            </div>
            <textarea
              value={draft.full_draft_text}
              onChange={(e) => handleFieldChange('full_draft_text', e.target.value)}
              placeholder="Paste your scene outline, script excerpts, or detailed narrative treatment here for deeper diagnostic assessment..."
              rows={8}
              className="w-full px-3 py-2.5 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-welele-orange focus:outline-none font-mono leading-relaxed"
            />
          </div>
        </div>

        {/* Right Column: Character Polarity & Episodic Hooks */}
        <div className="lg:col-span-5 space-y-5">
          {/* Character Polarity (Want vs Need vs Counterforce) */}
          <div className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 space-y-3.5">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 text-amber-400">
              <User className="w-3.5 h-3.5" /> Character Engine & Conflict
            </h3>

            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-welele-muted">Protagonist Name & Role</label>
              <input
                type="text"
                value={draft.protagonist_name}
                onChange={(e) => handleFieldChange('protagonist_name', e.target.value)}
                placeholder="e.g. Sipho (reluctant heir) or Nandi (investigative reporter)"
                className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-amber-400 focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <div className="space-y-1.5">
                <label className="text-[11px] font-bold text-welele-muted">External Want (Objective)</label>
                <textarea
                  value={draft.protagonist_want}
                  onChange={(e) => handleFieldChange('protagonist_want', e.target.value)}
                  placeholder="What tangible goal are they chasing immediately?"
                  rows={2}
                  className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-amber-400 focus:outline-none resize-none"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-[11px] font-bold text-welele-muted">Internal Need (Arc)</label>
                <textarea
                  value={draft.protagonist_need}
                  onChange={(e) => handleFieldChange('protagonist_need', e.target.value)}
                  placeholder="What emotional truth must they learn to grow?"
                  rows={2}
                  className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-amber-400 focus:outline-none resize-none"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-welele-muted">Counterforce / Opposing Force</label>
              <textarea
                value={draft.counterforce_or_antagonist}
                onChange={(e) => handleFieldChange('counterforce_or_antagonist', e.target.value)}
                placeholder="Who or what systematically opposes them? (Character, family expectation, debt, curse, corrupt system...)"
                rows={2}
                className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-amber-400 focus:outline-none resize-none"
              />
            </div>
          </div>

          {/* Episodic Hooks */}
          <div className="p-4 rounded-[7px] bg-[#14151C] border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 text-pink-400">
                <Zap className="w-3.5 h-3.5" /> Episode Cliffhangers & Hooks
              </h3>
              <button
                onClick={handleAddHook}
                className="text-[11px] text-pink-400 hover:text-pink-300 font-bold flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3 h-3" /> Add Beat
              </button>
            </div>

            {(!draft.episode_hooks || draft.episode_hooks.length === 0) ? (
              <p className="text-xs text-zinc-500 italic py-2">
                No episode hooks defined yet. Click &quot;Add Beat&quot; to outline cliffhangers for episodes 1–3.
              </p>
            ) : (
              <div className="space-y-2">
                {draft.episode_hooks.map((hook, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={hook}
                      onChange={(e) => handleUpdateHook(idx, e.target.value)}
                      placeholder={`Ep ${idx + 1} cliffhanger reveal...`}
                      className="flex-1 px-3 py-1.5 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-pink-400 focus:outline-none"
                    />
                    <button
                      onClick={() => handleRemoveHook(idx)}
                      className="p-1.5 text-zinc-500 hover:text-red-400 transition-colors"
                      title="Remove hook"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
