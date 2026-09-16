import React, { useState, useEffect } from 'react';
import { storyReviewApi } from '../../services/storyReviewApi';
import { CreatorSubmission } from '../../types/storyReview';
import { ShieldCheck, Clock, FileText, CheckCircle2, ChevronRight, Sparkles, Filter, AlertCircle } from 'lucide-react';

interface AdminIntakeQueueProps {
  onSelectForForge?: (submission: CreatorSubmission) => void;
}

export const AdminIntakeQueue: React.FC<AdminIntakeQueueProps> = ({ onSelectForForge }) => {
  const [submissions, setSubmissions] = useState<CreatorSubmission[]>([]);
  const [selectedSub, setSelectedSub] = useState<CreatorSubmission | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadSubmissions();
  }, []);

  const loadSubmissions = async () => {
    try {
      const list = await storyReviewApi.getSubmissions();
      setSubmissions(list || []);
      if (list && list.length > 0 && !selectedSub) {
        setSelectedSub(list[0]);
      }
    } catch (e) {
      console.warn('Could not load admin intake submissions:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in text-white">
      {/* Header Banner */}
      <div className="p-5 rounded-[7px] bg-gradient-to-r from-emerald-950/40 via-welele-surface-2 to-welele-surface border border-emerald-500/20 shadow-xl flex items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-bold">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-extrabold text-white">IP Pipeline — Creator Intake & Editorial Triage</h2>
              <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {submissions.length} Active Submissions
              </span>
            </div>
            <p className="text-xs text-welele-muted mt-0.5">
              Review creator submissions from Story Review™ and select high-potential IP for internal Story Forge™ production development.
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-zinc-500 text-xs">Loading IP Pipeline Submissions...</div>
      ) : submissions.length === 0 ? (
        <div className="p-12 text-center rounded-[7px] bg-[#14151C] border border-white/10 space-y-3">
          <Clock className="w-10 h-10 text-zinc-600 mx-auto" />
          <h3 className="text-sm font-bold text-zinc-400">No Creator Submissions in Queue</h3>
          <p className="text-xs text-zinc-500 max-w-sm mx-auto">
            Submissions made via Story Review™ in the Creator App will appear here for editorial triage.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Submissions List */}
          <div className="lg:col-span-5 space-y-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider text-welele-muted">
              Intake Roster
            </h3>
            <div className="space-y-2.5">
              {submissions.map((sub) => {
                const isSelected = selectedSub?.submission_id === sub.submission_id;
                return (
                  <div
                    key={sub.submission_id}
                    onClick={() => setSelectedSub(sub)}
                    className={`p-3.5 rounded-[7px] border transition-all cursor-pointer space-y-2 ${
                      isSelected
                        ? 'bg-emerald-950/30 border-emerald-500/50 shadow-md'
                        : 'bg-[#14151C] border-white/10 hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-black text-white">{sub.title}</span>
                      <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono">
                        {sub.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-400 line-clamp-2">
                      {sub.submission_package?.synopsis || 'Story package'}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-welele-muted pt-1 border-t border-white/5">
                      <span>Creator: <strong className="text-white">{sub.creator_name}</strong></span>
                      <span className="text-emerald-400 font-bold">
                        Readiness: {sub.diagnostic_summary?.readiness_score || 70}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Submission Inspector & Action Panel */}
          <div className="lg:col-span-7">
            {selectedSub ? (
              <div className="p-5 rounded-[7px] bg-[#14151C] border border-white/10 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-white/10">
                  <div>
                    <h3 className="text-base font-black text-white">{selectedSub.title}</h3>
                    <p className="text-xs text-welele-muted">
                      Creator: <strong className="text-white">{selectedSub.creator_name}</strong> • Submitted:{' '}
                      {new Date(selectedSub.submitted_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded-[7px] text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Readiness: {selectedSub.diagnostic_summary?.readiness_score || 70}%
                  </span>
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider text-emerald-400">
                    Synopsis / Logline
                  </h4>
                  <p className="text-xs text-zinc-300 leading-relaxed p-3 rounded-[7px] bg-black/40 border border-white/10">
                    {selectedSub.submission_package?.synopsis || 'No logline provided.'}
                  </p>
                </div>

                {selectedSub.submission_package?.creator_notes && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider text-amber-400">
                      Creator Statement & Notes
                    </h4>
                    <p className="text-xs text-zinc-300 leading-relaxed p-3 rounded-[7px] bg-black/40 border border-white/10">
                      {selectedSub.submission_package.creator_notes}
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="p-3 rounded-[7px] bg-black/40 border border-white/10 space-y-1">
                    <span className="text-[10px] font-bold text-welele-muted uppercase">Target Setting</span>
                    <p className="text-xs text-white font-medium">
                      {selectedSub.submission_package?.primary_locations || 'Grounded Locations'}
                    </p>
                  </div>
                  <div className="p-3 rounded-[7px] bg-black/40 border border-white/10 space-y-1">
                    <span className="text-[10px] font-bold text-welele-muted uppercase">Planned Episodes</span>
                    <p className="text-xs text-white font-medium">
                      {selectedSub.submission_package?.estimated_episodes || 6} Episodes (9:16)
                    </p>
                  </div>
                </div>

                {/* Editorial Actions */}
                <div className="pt-4 border-t border-white/10 flex items-center justify-between gap-3">
                  <span className="text-[11px] text-welele-muted">
                    Submission ID: <code className="text-white font-mono">{selectedSub.submission_id}</code>
                  </span>

                  {onSelectForForge && (
                    <button
                      onClick={() => onSelectForForge(selectedSub)}
                      className="px-4 py-2 rounded-[7px] bg-gradient-to-r from-welele-gold to-amber-500 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-amber-500/20 cursor-pointer"
                    >
                      <Sparkles className="w-4 h-4 fill-black" />
                      <span>Develop in Story Forge™</span>
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-zinc-500 text-xs">Select a submission to inspect</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
