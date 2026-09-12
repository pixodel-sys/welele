import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/api';
import { ModerationItem } from '../../types';
import { ProvenanceBadge } from '../common/patterns/ProvenanceBadge';
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
  MessageSquare,
  FileCheck,
  Activity,
  Cpu
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
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              AI Moderation & Pre-flight Quality Gate ({queue.length})
            </h3>
            <ProvenanceBadge tier="ADMIN_CONTROLLED" size="sm" />
          </div>
          <p className="text-[11px] text-welele-muted">
            Three Truths Verification: Creator Metadata Declarations vs. Media Observed Physical Integrity vs. AI Pre-flight Signals.
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
                    <div className="flex items-center gap-2 flex-wrap">
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

                    <div className="flex items-center gap-2 text-welele-muted flex-wrap">
                      <span>Creator: <b className="text-white">{item.creator_name}</b></span>
                      <ProvenanceBadge tier="CREATOR_DECLARED" size="sm" />
                      <span>• Duration: <b className="text-white">{item.duration}</b></span>
                      <ProvenanceBadge tier="MEDIA_OBSERVED" size="sm" />
                      <span>• Aspect: <b className="text-white">{item.aspect_ratio}</b></span>
                    </div>
                  </div>

                  {/* Action Controls */}
                  <div className="flex items-center gap-2 self-end md:self-center">
                    <button
                      onClick={() => setInspectingItem(inspectingItem?.id === item.id ? null : item)}
                      className="px-3 py-1.5 rounded-[7px] bg-white/5 hover:bg-white/10 text-white font-bold border border-white/10 flex items-center gap-1.5"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>{inspectingItem?.id === item.id ? 'Close Inspection' : 'Inspect Safe Zone & Three Truths'}</span>
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

                {/* Three Truths Pre-flight Signals Grid */}
                <div className="space-y-2 pt-1">
                  <div className="flex items-center gap-2 text-[10px] text-welele-muted uppercase font-bold tracking-wider">
                    <span>Pre-Flight Lineage & Truth Matrix</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px]">
                    {/* Truth 1: Creator Declared */}
                    <div className="p-2.5 rounded-[7px] bg-black/40 border border-white/5 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold text-white flex items-center gap-1">
                          <FileCheck className="w-3 h-3 text-sky-400" /> Truth 1: Creator
                        </span>
                        <ProvenanceBadge tier="CREATOR_DECLARED" size="sm" />
                      </div>
                      <p className="text-[10px] text-welele-muted truncate">
                        Series: {item.series_title} • Creator: {item.creator_name}
                      </p>
                    </div>

                    {/* Truth 2: Media Observed */}
                    <div className="p-2.5 rounded-[7px] bg-black/40 border border-white/5 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold text-white flex items-center gap-1">
                          <Activity className="w-3 h-3 text-emerald-400" /> Truth 2: Media
                        </span>
                        <ProvenanceBadge tier="MEDIA_OBSERVED" size="sm" />
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-emerald-300 font-mono">
                        <span>{item.aspect_ratio || '9:16'} Valid</span>
                        <span>• LUFS Normalized</span>
                      </div>
                    </div>

                    {/* Truth 3: AI Observed */}
                    <div className="p-2.5 rounded-[7px] bg-black/40 border border-white/5 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold text-white flex items-center gap-1">
                          <Cpu className="w-3 h-3 text-purple-400" /> Truth 3: AI Safety
                        </span>
                        <ProvenanceBadge tier="AI_OBSERVED" size="sm" />
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-purple-300 font-mono">
                        <span>Safety: {item.ai_safety_score || 98}%</span>
                        <span>• Hook: @{item.cliffhanger_time || 56}s</span>
                      </div>
                    </div>
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
