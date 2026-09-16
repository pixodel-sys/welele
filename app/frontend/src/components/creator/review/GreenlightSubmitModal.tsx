import React, { useState } from 'react';
import { StoryDraft, StoryReviewDiagnostic } from '../../../types/storyReview';
import { ShieldCheck, X, AlertCircle, ArrowRight, CheckCircle2, Film } from 'lucide-react';

interface GreenlightSubmitModalProps {
  isOpen: boolean;
  onClose: () => void;
  draft: StoryDraft;
  diagnostic: StoryReviewDiagnostic | null;
  onSubmit: (creatorNotes: string) => Promise<void>;
  isSubmitting: boolean;
}

export const GreenlightSubmitModal: React.FC<GreenlightSubmitModalProps> = ({
  isOpen,
  onClose,
  draft,
  diagnostic,
  onSubmit,
  isSubmitting,
}) => {
  const [creatorNotes, setCreatorNotes] = useState<string>('');
  const [agreedToTerms, setAgreedToTerms] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agreedToTerms) return;
    await onSubmit(creatorNotes);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-[7px] bg-[#14151C] border border-white/15 shadow-2xl overflow-hidden text-white">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/10 bg-gradient-to-r from-emerald-950/40 to-transparent">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-extrabold text-white">Welele IP Pipeline Submission</h3>
              <p className="text-[11px] text-welele-muted">Submit story package for Greenlight & Editorial Intake</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-[7px] text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Submission Details Card */}
          <div className="p-3.5 rounded-[7px] bg-black/40 border border-white/10 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <Film className="w-3.5 h-3.5 text-welele-orange" /> {draft.title}
              </span>
              <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {diagnostic ? `${diagnostic.readiness_score}% Readiness` : 'Self-Prepared'}
              </span>
            </div>
            <p className="text-xs text-zinc-300 line-clamp-2">
              {draft.logline || 'High-concept vertical microdrama narrative package.'}
            </p>
            <div className="flex items-center gap-3 text-[11px] text-welele-muted pt-1 border-t border-white/5">
              <span>Format: <strong className="text-white">{draft.target_format}</strong></span>
              <span>•</span>
              <span>Tone: <strong className="text-white">{draft.tone}</strong></span>
            </div>
          </div>

          {/* Creator Notes / Director Statement */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-white">Creator Statement & Notes (Optional)</label>
            <textarea
              value={creatorNotes}
              onChange={(e) => setCreatorNotes(e.target.value)}
              placeholder="Add any specific notes for Welele editorial triage (e.g. casting vision, target audience nuances, production timeline)..."
              rows={3}
              className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-[7px] text-white text-xs placeholder:text-zinc-600 focus:border-emerald-500 focus:outline-none resize-none"
            />
          </div>

          {/* Governing IP Notice */}
          <div className="p-3 rounded-[7px] bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1 text-[11px] leading-relaxed">
              <span className="font-bold block text-amber-300">Submission ≠ Automatic Greenlight</span>
              <span>
                Submitting creates an authoritative Creator Intake Record in the Welele IP Pipeline (Status: <em>SUBMITTED_FOR_REVIEW</em>).
                Our editorial team will evaluate your pitch package for production development.
              </span>
            </div>
          </div>

          {/* Legal / Provenance Checkbox */}
          <label className="flex items-start gap-2.5 cursor-pointer pt-1">
            <input
              type="checkbox"
              checked={agreedToTerms}
              onChange={(e) => setAgreedToTerms(e.target.checked)}
              className="mt-0.5 rounded border-white/20 text-emerald-500 focus:ring-emerald-500 bg-black/40"
            />
            <span className="text-[11px] text-zinc-300 leading-tight">
              I certify that this original story and pitch package is my creator IP and I authorize Welele Media editorial evaluation.
            </span>
          </label>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 text-xs font-bold text-zinc-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!agreedToTerms || isSubmitting}
              className="px-5 py-2 rounded-[7px] bg-gradient-to-r from-emerald-500 to-teal-400 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-500/20 hover:opacity-95 transition-all cursor-pointer disabled:opacity-50"
            >
              <ShieldCheck className="w-4 h-4 font-bold" />
              <span>{isSubmitting ? 'Submitting to IP Pipeline...' : 'Submit for Greenlight'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
