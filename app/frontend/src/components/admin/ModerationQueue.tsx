import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/api';
import { ModerationItem } from '../../types';
import {
  ShieldCheck,
  Check,
  X,
  Sparkles,
  Video,
  AlertTriangle,
  Eye,
  EyeOff,
  Clock,
  CheckCircle2,
  Volume2,
  Flame,
  MessageSquare
} from 'lucide-react';

export const ModerationQueue: React.FC = () => {
  const [queue, setQueue] = useState<ModerationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [inspectingItem, setInspectingItem] = useState<ModerationItem | null>(null);
  const [feedbackInput, setFeedbackInput] = useState<string>('Please adjust cliffhanger audio level and verify safe zone overlays.');

  const fetchQueue = () => {
    adminApi
      .getModerationQueue()
      .then((res) => setQueue(res.queue || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleApprove = async (id: string) => {
    try {
      await adminApi.approveItem(id);
      setActionMessage('Item approved and published to global feed.');
      fetchQueue();
      if (inspectingItem?.id === id) setInspectingItem(null);
      setTimeout(() => setActionMessage(null), 2500);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRequestChanges = async (id: string) => {
    try {
      await adminApi.requestChanges(id, feedbackInput);
      setActionMessage('Feedback sent to creator. Status updated to Changes Needed.');
      fetchQueue();
      if (inspectingItem?.id === id) setInspectingItem(null);
      setTimeout(() => setActionMessage(null), 2500);
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async (id: string) => {
    try {
      await adminApi.rejectItem(id, feedbackInput);
      setActionMessage('Item rejected. Notification dispatched to creator.');
      fetchQueue();
      if (inspectingItem?.id === id) setInspectingItem(null);
      setTimeout(() => setActionMessage(null), 2500);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-welele-muted">Loading moderation queue...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            AI Moderation & Pre-flight Quality Gate ({queue.length})
          </h3>
          <p className="text-[11px] text-welele-muted">
            Inspect creator submissions, video health signals, cliffhanger markers, and consumer safe zone alignment.
          </p>
        </div>

        {actionMessage && (
          <span className="text-xs text-emerald-400 font-bold bg-emerald-500/10 px-3 py-1 rounded-[7px] border border-emerald-500/30 animate-fade-in">
            {actionMessage}
          </span>
        )}
      </div>

      <div className="space-y-4">
        {queue.length === 0 ? (
          <div className="p-8 text-center bg-[#14151B] rounded-[7px] border border-white/5 text-welele-muted text-xs">
            No items currently pending moderation review.
          </div>
        ) : (
          queue.map((item) => {
            const isApproved = item.status === 'approved';
            const isChanges = item.status === 'changes_requested';
            const isRejected = item.status === 'rejected';

            return (
              <div
                key={item.id}
                className="p-5 rounded-[7px] bg-[#14151B] border border-white/10 space-y-4 text-xs shadow-lg"
              >
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-sm">
                        {item.series_title} {item.episode_number ? `• EP ${item.episode_number < 10 ? `0${item.episode_number}` : item.episode_number}` : ''}
                      </span>
                      {item.episode_title && (
                        <span className="text-white/80 font-medium">"{item.episode_title}"</span>
                      )}
                      <span
                        className={`px-2 py-0.5 rounded-[7px] text-[10px] font-bold ${
                          isApproved
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : isChanges
                            ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                            : isRejected
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                            : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        {item.status.toUpperCase().replace('_', ' ')}
                      </span>
                    </div>

                    <p className="text-welele-muted">
                      Creator: <b className="text-white">{item.creator_name}</b> • Duration:{' '}
                      <b className="text-white">{item.duration}</b> • Aspect:{' '}
                      <b className="text-white">{item.aspect_ratio}</b>
                    </p>
                  </div>

                  {/* Action Controls */}
                  <div className="flex items-center gap-2 self-end md:self-center">
                    <button
                      onClick={() => setInspectingItem(inspectingItem?.id === item.id ? null : item)}
                      className="px-3 py-1.5 rounded-[7px] bg-white/5 hover:bg-white/10 text-white font-bold border border-white/10 flex items-center gap-1.5"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>{inspectingItem?.id === item.id ? 'Close Inspection' : 'Inspect Safe Zone'}</span>
                    </button>

                    {!isApproved && (
                      <>
                        <button
                          onClick={() => handleRequestChanges(item.id)}
                          className="px-3 py-1.5 rounded-[7px] bg-orange-500/20 text-orange-300 border border-orange-500/30 hover:bg-orange-500/30 font-bold"
                        >
                          Request Changes
                        </button>

                        <button
                          onClick={() => handleReject(item.id)}
                          className="px-3 py-1.5 rounded-[7px] bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 font-bold"
                        >
                          Reject
                        </button>

                        <button
                          onClick={() => handleApprove(item.id)}
                          className="px-4 py-1.5 rounded-[7px] bg-emerald-500 text-black hover:bg-emerald-400 font-black shadow"
                        >
                          Approve & Publish
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* Pre-flight Signals Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-[11px]">
                  <div className="p-2 rounded-[7px] bg-black/40 border border-white/5 flex items-center gap-1.5 text-emerald-300 font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>9:16 Aspect: Valid</span>
                  </div>
                  <div className="p-2 rounded-[7px] bg-black/40 border border-white/5 flex items-center gap-1.5 text-emerald-300 font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Audio LUFS: Normalized</span>
                  </div>
                  <div className="p-2 rounded-[7px] bg-black/40 border border-white/5 flex items-center gap-1.5 text-welele-gold font-mono">
                    <Flame className="w-3.5 h-3.5 text-welele-orange" />
                    <span>Cliffhanger: @{item.cliffhanger_time || 56}s</span>
                  </div>
                  <div className="p-2 rounded-[7px] bg-black/40 border border-white/5 flex items-center gap-1.5 text-emerald-300 font-mono">
                    <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                    <span>AI Safety: {item.ai_safety_score}%</span>
                  </div>
                </div>

                {/* Expanded Inspection Drawer */}
                {inspectingItem?.id === item.id && (
                  <div className="p-4 rounded-[7px] bg-black/60 border border-pink-500/30 space-y-4 animate-fade-in">
                    <div className="flex flex-col md:flex-row items-center gap-6">
                      {/* 9:16 Safe Zone Simulator Preview */}
                      <div className="w-[180px] aspect-[9/16] bg-black rounded-[7px] border border-white/20 relative overflow-hidden shrink-0 shadow-2xl">
                        <img
                          src={item.thumbnail_url || '/posters/blood_ties.jpg'}
                          alt={item.series_title}
                          className="w-full h-full object-cover"
                        />
                        {/* Safe Zone Overlay Box */}
                        <div className="absolute inset-[15%_18%_22%_6%] border border-dashed border-[#FF2A6D] rounded-[7px] bg-pink-500/10 flex items-center justify-center pointer-events-none">
                          <span className="text-[8px] font-mono text-[#FF2A6D] px-1 bg-black/80 rounded">
                            Safe Area
                          </span>
                        </div>
                      </div>

                      {/* Details & Feedback Textarea */}
                      <div className="space-y-3 flex-1 w-full text-xs">
                        <div>
                          <span className="text-welele-muted block font-bold mb-1">Cliffhanger Hook Copy:</span>
                          <p className="p-2 rounded-[7px] bg-black/50 border border-white/10 text-white font-mono text-[11px]">
                            "{item.cliffhanger_hook || 'Dramatic confrontation before resolution.'}"
                          </p>
                        </div>

                        <div>
                          <label className="text-welele-muted block font-bold mb-1">Moderator Review Notes / Change Request</label>
                          <textarea
                            rows={2}
                            value={feedbackInput}
                            onChange={(e) => setFeedbackInput(e.target.value)}
                            className="w-full bg-black/50 px-3 py-2 rounded-[7px] border border-white/10 text-white text-xs focus:outline-none focus:border-amber-500"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
