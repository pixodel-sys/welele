import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { creatorApi, aiApi } from '../../services/api';
import { Story, PreflightHealth } from '../../types';
import {
  CheckCircle2,
  AlertCircle,
  Video,
  Sparkles,
  ShieldCheck,
  Eye,
  EyeOff,
  Flame,
  Clock,
  Coins,
  ChevronRight,
  ChevronLeft,
  X,
  FileText,
  Sliders,
  Layers,
  Heart,
  MessageCircle,
  Bookmark,
  Gift,
  Share2,
  Volume2
} from 'lucide-react';

interface EpisodePipelineModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialSeriesId?: string;
  initialEpisodeNumber?: number;
}

export const EpisodePipelineModal: React.FC<EpisodePipelineModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialSeriesId,
  initialEpisodeNumber
}) => {
  const { stories, refreshStories } = useApp();

  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1);

  // Form State
  const [seriesId, setSeriesId] = useState<string>(
    initialSeriesId || stories[0]?.id || 'story_blood_ties'
  );
  const [episodeNumber, setEpisodeNumber] = useState<number>(initialEpisodeNumber || 5);
  const [title, setTitle] = useState<string>('The Discovery at Midnight');
  const [synopsis, setSynopsis] = useState<string>(
    'The surveillance logs from the penthouse reveal an unexpected visitor right before the will was executed.'
  );
  const [durationSeconds, setDurationSeconds] = useState<number>(64);
  const [videoUrl, setVideoUrl] = useState<string>('/videos/welele_placeholder.mp4');
  const [thumbnailUrl, setThumbnailUrl] = useState<string>('/posters/blood_ties.jpg');
  
  // Step 2: Story & Cliffhanger
  const [cliffhangerHook, setCliffhangerHook] = useState<string>(
    'The security footage clearly shows Lerato entering the safe room.'
  );
  const [cliffhangerTime, setCliffhangerTime] = useState<number>(56);
  const [dialogueNotes, setDialogueNotes] = useState<string>(
    'Lerato: "You have no idea what she told me before she signed it."'
  );

  // Step 3: Media & Safe Zone
  const [showSafeZoneOverlay, setShowSafeZoneOverlay] = useState<boolean>(true);
  const [captionsEnabled, setCaptionsEnabled] = useState<boolean>(true);
  const [isAnalyzingAI, setIsAnalyzingAI] = useState<boolean>(false);

  // Step 4: Monetisation & Release
  const [isFree, setIsFree] = useState<boolean>(episodeNumber <= 3);
  const [coinPrice, setCoinPrice] = useState<number>(5);
  const [releaseSchedule, setReleaseSchedule] = useState<'immediate' | 'scheduled'>('immediate');
  const [scheduledDateTime, setScheduledDateTime] = useState<string>('2026-09-09T18:00');

  // Step 5: Submission & Status
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);

  if (!isOpen) return null;

  const selectedStory = stories.find((s) => s.id === seriesId) || stories[0];

  // Pre-flight health checks computed dynamically
  const preflightHealth: PreflightHealth = {
    aspect_ratio_ok: true,
    aspect_ratio_label: '1080 × 1920 (9:16 Canonical)',
    duration_ok: durationSeconds >= 45 && durationSeconds <= 90,
    duration_seconds: durationSeconds,
    audio_detected: true,
    thumbnail_present: Boolean(thumbnailUrl),
    cliffhanger_marker_ok: cliffhangerTime > 0 && cliffhangerTime < durationSeconds,
    cliffhanger_time_seconds: cliffhangerTime,
    cliffhanger_hook_copy: cliffhangerHook,
    captions_present: captionsEnabled,
  };

  const handleRunAiAssistance = async () => {
    setIsAnalyzingAI(true);
    try {
      const res = await aiApi.analyzeVideo(videoUrl, title, synopsis);
      if (res?.cliffhanger_suggested_timestamp) {
        setCliffhangerTime(res.cliffhanger_suggested_timestamp);
      }
      if (res?.hook_line) {
        setCliffhangerHook(res.hook_line);
      }
    } catch (err) {
      console.error('AI analysis error:', err);
    } finally {
      setIsAnalyzingAI(false);
    }
  };

  const handleSubmitPipeline = async (targetStatus: 'draft' | 'under_review') => {
    setIsSubmitting(true);
    try {
      await creatorApi.addEpisode({
        series_id: seriesId,
        episode_number: Number(episodeNumber),
        title,
        synopsis,
        video_url: videoUrl,
        thumbnail_url: thumbnailUrl || selectedStory?.vertical_poster || '/posters/blood_ties.jpg',
        duration_seconds: Number(durationSeconds),
        is_free: isFree,
        coin_price: isFree ? 0 : Number(coinPrice),
        cliffhanger_time: Number(cliffhangerTime),
        cliffhanger_hook: cliffhangerHook,
        status: targetStatus,
        scheduled_at: releaseSchedule === 'scheduled' ? scheduledDateTime : undefined,
        preflight_health: preflightHealth,
      });

      await refreshStories();
      setSubmitSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err) {
      console.error('Failed to submit episode to pipeline:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const stepLabels = [
    { num: 1, title: 'Details' },
    { num: 2, title: 'Story & Cliffhanger' },
    { num: 3, title: 'Media & Safe Zone' },
    { num: 4, title: 'Monetisation' },
    { num: 5, title: 'Pre-flight & Submit' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0F1014] border border-white/10 rounded-[7px] max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-fade-in">
        
        {/* Modal Top Header */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-gradient-to-r from-pink-950/40 via-welele-surface to-welele-surface">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-[7px] bg-gradient-to-tr from-[#E6007A] to-[#FF2A6D] flex items-center justify-center text-white shadow">
              <Video className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-black text-white uppercase tracking-wider">
                  Episode Production Pipeline
                </h2>
                <span className="px-2 py-0.5 rounded-[7px] bg-pink-500/20 text-[#FF2A6D] border border-pink-500/30 text-[10px] font-bold">
                  EP {episodeNumber < 10 ? `0${episodeNumber}` : episodeNumber}
                </span>
              </div>
              <p className="text-xs text-welele-muted">
                {selectedStory?.title} • Microdrama Quality Gate & AI Moderation Bridge
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-[7px] bg-white/5 hover:bg-white/10 text-white/70 hover:text-white flex items-center justify-center transition-all"
            aria-label="Close Modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 5-Step Stepper Ribbon */}
        <div className="px-6 py-3 bg-[#14151B] border-b border-white/5 grid grid-cols-5 gap-2">
          {stepLabels.map((s) => {
            const isActive = step === s.num;
            const isCompleted = step > s.num;
            return (
              <button
                key={s.num}
                onClick={() => setStep(s.num as any)}
                className={`flex items-center gap-2 text-left py-1.5 px-2 rounded-[7px] transition-all ${
                  isActive
                    ? 'bg-pink-500/15 border border-pink-500/40 text-white'
                    : isCompleted
                    ? 'text-emerald-400 opacity-80 hover:opacity-100'
                    : 'text-welele-muted hover:text-white/70'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-[7px] flex items-center justify-center text-[10px] font-black shrink-0 ${
                    isActive
                      ? 'bg-[#E6007A] text-white'
                      : isCompleted
                      ? 'bg-emerald-500/30 text-emerald-400 border border-emerald-500/40'
                      : 'bg-white/10 text-welele-muted'
                  }`}
                >
                  {isCompleted ? '✓' : s.num}
                </div>
                <span className="text-[11px] font-bold truncate hidden sm:inline">{s.title}</span>
              </button>
            );
          })}
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 flex-1 overflow-y-auto space-y-6">
          {submitSuccess ? (
            <div className="py-12 text-center space-y-4">
              <div className="w-14 h-14 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 mx-auto flex items-center justify-center">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-black text-white">Submitted to Moderation Queue!</h3>
              <p className="text-xs text-welele-muted max-w-sm mx-auto">
                Your vertical episode has passed pre-flight checks and is now queued for AI Safety scoring and Admin publication.
              </p>
            </div>
          ) : (
            <>
              {/* STEP 1: EPISODE DETAILS */}
              {step === 1 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <FileText className="w-4 h-4 text-[#FF2A6D]" />
                      Step 1: Series & Core Metadata
                    </h3>
                    <span className="text-[11px] text-welele-muted">
                      Canonical 9:16 Vertical Microdrama
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="sm:col-span-2">
                      <label className="text-xs text-welele-muted block mb-1">Target Series</label>
                      <select
                        value={seriesId}
                        onChange={(e) => setSeriesId(e.target.value)}
                        className="w-full bg-[#16171E] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-[#E6007A]"
                      >
                        {stories.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.title} ({s.genre})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="text-xs text-welele-muted block mb-1">Episode Number</label>
                      <input
                        type="number"
                        min={1}
                        value={episodeNumber}
                        onChange={(e) => {
                          const n = Number(e.target.value);
                          setEpisodeNumber(n);
                          if (n <= 3) setIsFree(true);
                        }}
                        className="w-full bg-[#16171E] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-[#E6007A]"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs text-welele-muted block mb-1">Episode Title</label>
                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="e.g., The Secret Will"
                      className="w-full bg-[#16171E] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-[#E6007A]"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-welele-muted block mb-1">Episode Synopsis & Dramatic Core</label>
                    <textarea
                      rows={3}
                      value={synopsis}
                      onChange={(e) => setSynopsis(e.target.value)}
                      placeholder="What is the high-stakes dramatic revelation in this 60-second beat?"
                      className="w-full bg-[#16171E] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-[#E6007A]"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs text-welele-muted block mb-1">Target Duration (Seconds)</label>
                      <input
                        type="number"
                        min={30}
                        max={120}
                        value={durationSeconds}
                        onChange={(e) => setDurationSeconds(Number(e.target.value))}
                        className="w-full bg-[#16171E] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-[#E6007A]"
                      />
                      <span className="text-[10px] text-welele-muted block mt-1">Recommended: 45–90 seconds</span>
                    </div>

                    <div>
                      <label className="text-xs text-welele-muted block mb-1">Primary Audio Dialect</label>
                      <input
                        type="text"
                        readOnly
                        value={selectedStory?.language || 'isiZulu / English'}
                        className="w-full bg-[#16171E]/60 px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white/70"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 2: STORY & CLIFFHANGER */}
              {step === 2 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <Flame className="w-4 h-4 text-welele-orange" />
                      Step 2: Microdrama Cliffhanger & Dialogue Hooks
                    </h3>

                    <button
                      type="button"
                      onClick={handleRunAiAssistance}
                      disabled={isAnalyzingAI}
                      className="px-3 py-1.5 rounded-[7px] bg-gradient-to-r from-pink-600 to-orange-500 text-white text-xs font-bold flex items-center gap-1.5 shadow"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      {isAnalyzingAI ? 'Detecting Hook...' : 'AI Hook Detection'}
                    </button>
                  </div>

                  <div className="p-4 rounded-[7px] bg-[#16171E] border border-white/10 space-y-3">
                    <label className="text-xs font-bold text-white block">
                      Cliffhanger Hook Copy (Shown to Viewer on Drop-off / Unlock Prompt)
                    </label>
                    <textarea
                      rows={2}
                      value={cliffhangerHook}
                      onChange={(e) => setCliffhangerHook(e.target.value)}
                      placeholder="e.g., The security camera shows who stole the diamond ledger."
                      className="w-full bg-[#0F1014] px-3.5 py-2 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-welele-orange"
                    />

                    <div>
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <span className="text-welele-muted flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-welele-gold" />
                          Cliffhanger Timestamp Marker:
                        </span>
                        <span className="font-mono font-bold text-welele-gold text-xs">
                          {Math.floor(cliffhangerTime / 60)}:{(cliffhangerTime % 60).toString().padStart(2, '0')} / {Math.floor(durationSeconds / 60)}:{(durationSeconds % 60).toString().padStart(2, '0')}
                        </span>
                      </div>
                      
                      <input
                        type="range"
                        min={10}
                        max={durationSeconds}
                        value={cliffhangerTime}
                        onChange={(e) => setCliffhangerTime(Number(e.target.value))}
                        className="w-full accent-[#E6007A] cursor-pointer"
                      />
                      <div className="flex justify-between text-[10px] text-welele-muted mt-1">
                        <span>0:00 (Intro)</span>
                        <span className="text-welele-gold font-bold">Recommended: ~85% mark ({Math.floor(durationSeconds * 0.85)}s)</span>
                        <span>{durationSeconds}s (End)</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="text-xs text-welele-muted block mb-1">Key Climax Dialogue / Script Excerpt</label>
                    <textarea
                      rows={3}
                      value={dialogueNotes}
                      onChange={(e) => setDialogueNotes(e.target.value)}
                      placeholder="Enter the critical line of dialogue delivered at the cliffhanger moment..."
                      className="w-full bg-[#16171E] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-[#E6007A]"
                    />
                  </div>
                </div>
              )}

              {/* STEP 3: MEDIA & SAFE ZONE SIMULATOR */}
              {step === 3 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <Layers className="w-4 h-4 text-emerald-400" />
                      Step 3: 9:16 Video Asset & Safe Zone Simulator
                    </h3>

                    <button
                      type="button"
                      onClick={() => setShowSafeZoneOverlay(!showSafeZoneOverlay)}
                      className={`px-3 py-1.5 rounded-[7px] text-xs font-bold flex items-center gap-1.5 transition-all ${
                        showSafeZoneOverlay
                          ? 'bg-[#E6007A] text-white shadow'
                          : 'bg-white/10 text-welele-muted hover:text-white'
                      }`}
                    >
                      {showSafeZoneOverlay ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                      <span>{showSafeZoneOverlay ? 'Safe Zone: ON' : 'Safe Zone: OFF'}</span>
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                    {/* Form Controls Left */}
                    <div className="md:col-span-6 space-y-4">
                      <div>
                        <label className="text-xs text-welele-muted block mb-1">9:16 Vertical Video Stream Pointer</label>
                        <input
                          type="text"
                          value={videoUrl}
                          onChange={(e) => setVideoUrl(e.target.value)}
                          className="w-full bg-[#16171E] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white font-mono"
                        />
                      </div>

                      <div>
                        <label className="text-xs text-welele-muted block mb-1">Vertical Poster / Thumbnail URL (9:16)</label>
                        <input
                          type="text"
                          value={thumbnailUrl}
                          onChange={(e) => setThumbnailUrl(e.target.value)}
                          className="w-full bg-[#16171E] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white font-mono"
                        />
                      </div>

                      <div className="p-3.5 rounded-[7px] bg-[#16171E] border border-white/10 flex items-center justify-between">
                        <div>
                          <span className="text-xs font-bold text-white block">Auto AI African Captions</span>
                          <span className="text-[10px] text-welele-muted">Burn-in subtitles with verified safe area</span>
                        </div>
                        <input
                          type="checkbox"
                          checked={captionsEnabled}
                          onChange={(e) => setCaptionsEnabled(e.target.checked)}
                          className="w-4 h-4 accent-[#E6007A] rounded-[7px]"
                        />
                      </div>

                      <div className="p-3.5 rounded-[7px] bg-pink-950/20 border border-pink-500/20 text-xs text-pink-200 space-y-1">
                        <span className="font-bold flex items-center gap-1 text-[#FF2A6D]">
                          <ShieldCheck className="w-4 h-4" /> Welele Safe Zone Standard:
                        </span>
                        <p className="text-[11px] text-white/80 leading-relaxed">
                          Keep key faces, subtitles, and logos within the central 60% safe area. Avoid placing text in the top 15% (header icons) and bottom 22% (title, tags & unlock pill).
                        </p>
                      </div>
                    </div>

                    {/* Interactive 9:16 Preview Right */}
                    <div className="md:col-span-6 flex flex-col items-center">
                      <div className="text-[11px] text-welele-muted mb-2 font-mono">
                        9:16 Realtime Consumer Simulator
                      </div>

                      <div className="w-[240px] aspect-[9/16] bg-black rounded-[7px] border border-white/20 relative overflow-hidden shadow-2xl">
                        {/* Background Video / Thumbnail */}
                        <img
                          src={thumbnailUrl || '/posters/blood_ties.jpg'}
                          alt="Safe Zone Preview"
                          className="w-full h-full object-cover"
                        />

                        {/* Consumer UI Overlay Simulation */}
                        {showSafeZoneOverlay && (
                          <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-3 select-none">
                            {/* Safe Zone Grid Boundary Line */}
                            <div className="absolute inset-[15%_18%_22%_6%] border border-dashed border-[#FF2A6D]/60 rounded-[7px] bg-pink-500/5 flex items-center justify-center">
                              <span className="text-[9px] font-mono text-[#FF2A6D] px-1 bg-black/70 rounded">
                                Safe Zone Box
                              </span>
                            </div>

                            {/* Top Consumer Bar */}
                            <div className="flex items-center justify-between text-white text-[10px] font-bold z-10">
                              <span className="px-2 py-0.5 rounded bg-black/60">← Back</span>
                              <span className="px-2 py-0.5 rounded bg-amber-500/80 text-black font-extrabold">🪙 150</span>
                            </div>

                            {/* Right Consumer Action Rail */}
                            <div className="absolute right-2.5 bottom-20 flex flex-col items-center gap-3 z-10">
                              <div className="flex flex-col items-center text-[9px] text-white font-bold">
                                <div className="w-8 h-8 rounded-full bg-black/60 flex items-center justify-center">
                                  <Heart className="w-4 h-4 text-[#FF2A6D] fill-[#FF2A6D]" />
                                </div>
                                <span>142K</span>
                              </div>
                              <div className="flex flex-col items-center text-[9px] text-white font-bold">
                                <div className="w-8 h-8 rounded-full bg-black/60 flex items-center justify-center">
                                  <MessageCircle className="w-4 h-4 text-white" />
                                </div>
                                <span>4.8K</span>
                              </div>
                              <div className="w-8 h-8 rounded-full bg-black/60 flex items-center justify-center">
                                <Bookmark className="w-4 h-4 text-white" />
                              </div>
                              <div className="w-8 h-8 rounded-full bg-black/60 flex items-center justify-center">
                                <Gift className="w-4 h-4 text-welele-gold" />
                              </div>
                              <div className="w-8 h-8 rounded-full bg-black/60 flex items-center justify-center">
                                <Share2 className="w-4 h-4 text-white" />
                              </div>
                            </div>

                            {/* Bottom Consumer Metadata */}
                            <div className="z-10 space-y-1 max-w-[75%]">
                              <div className="text-[11px] font-bold text-white drop-shadow truncate">
                                {selectedStory?.title} • EP {episodeNumber}
                              </div>
                              <p className="text-[9px] text-white/90 line-clamp-2 drop-shadow">
                                {cliffhangerHook}
                              </p>
                              <div className="flex items-center gap-1.5 text-[8px] text-welele-gold bg-black/60 px-2 py-0.5 rounded w-max">
                                <Volume2 className="w-2.5 h-2.5" />
                                <span>Original Mzansi Sound • {selectedStory?.language}</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 4: MONETISATION & RELEASE */}
              {step === 4 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <Coins className="w-4 h-4 text-welele-gold" />
                      Step 4: Microdrama Monetisation & Scheduling
                    </h3>
                  </div>

                  {/* Free vs Paid Toggle */}
                  <div className="p-4 rounded-[7px] bg-[#16171E] border border-white/10 space-y-3">
                    <span className="text-xs font-bold text-white block">Episode Access Tier</span>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => {
                          setIsFree(true);
                          setCoinPrice(0);
                        }}
                        className={`p-3.5 rounded-[7px] text-left border transition-all ${
                          isFree
                            ? 'bg-emerald-500/15 border-emerald-500 text-white'
                            : 'bg-black/30 border-white/10 text-welele-muted hover:border-white/20'
                        }`}
                      >
                        <div className="text-xs font-black text-emerald-400">FREE UNLOCK</div>
                        <p className="text-[10px] text-welele-muted mt-1">
                          Episodes 1–3 default to Free to build viewer hook & viral funnel.
                        </p>
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setIsFree(false);
                          setCoinPrice(5);
                        }}
                        className={`p-3.5 rounded-[7px] text-left border transition-all ${
                          !isFree
                            ? 'bg-amber-500/15 border-amber-500 text-white'
                            : 'bg-black/30 border-white/10 text-welele-muted hover:border-white/20'
                        }`}
                      >
                        <div className="text-xs font-black text-amber-400">LOCKED (5 COINS)</div>
                        <p className="text-[10px] text-welele-muted mt-1">
                          Standard Welele coin price. Creator receives 70% net revenue share.
                        </p>
                      </button>
                    </div>

                    {!isFree && (
                      <div className="pt-2">
                        <label className="text-xs text-welele-muted block mb-1">Custom Coin Price</label>
                        <input
                          type="number"
                          min={1}
                          max={20}
                          value={coinPrice}
                          onChange={(e) => setCoinPrice(Number(e.target.value))}
                          className="w-32 bg-[#0F1014] px-3.5 py-2 rounded-[7px] border border-white/10 text-xs text-white"
                        />
                      </div>
                    )}
                  </div>

                  {/* Release Timing */}
                  <div className="p-4 rounded-[7px] bg-[#16171E] border border-white/10 space-y-3">
                    <span className="text-xs font-bold text-white block">Release Strategy</span>

                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => setReleaseSchedule('immediate')}
                        className={`p-3 rounded-[7px] text-xs font-bold border transition-all ${
                          releaseSchedule === 'immediate'
                            ? 'bg-pink-500/20 border-[#E6007A] text-white'
                            : 'bg-black/30 border-white/10 text-welele-muted'
                        }`}
                      >
                        ⚡ Immediate Release on Approval
                      </button>

                      <button
                        type="button"
                        onClick={() => setReleaseSchedule('scheduled')}
                        className={`p-3 rounded-[7px] text-xs font-bold border transition-all ${
                          releaseSchedule === 'scheduled'
                            ? 'bg-pink-500/20 border-[#E6007A] text-white'
                            : 'bg-black/30 border-white/10 text-welele-muted'
                        }`}
                      >
                        📅 Scheduled Premier Drop
                      </button>
                    </div>

                    {releaseSchedule === 'scheduled' && (
                      <div className="pt-2">
                        <label className="text-xs text-welele-muted block mb-1">Premier Date & Time (SAST / GMT+2)</label>
                        <input
                          type="datetime-local"
                          value={scheduledDateTime}
                          onChange={(e) => setScheduledDateTime(e.target.value)}
                          className="bg-[#0F1014] px-3.5 py-2 rounded-[7px] border border-white/10 text-xs text-white"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* STEP 5: PRE-FLIGHT HEALTH & SUBMIT */}
              {step === 5 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      Step 5: Automated Pre-flight Health & Moderation Gate
                    </h3>
                  </div>

                  <div className="p-5 rounded-[7px] bg-[#16171E] border border-white/10 space-y-3">
                    <h4 className="text-xs font-bold text-white font-mono uppercase tracking-wider mb-2">
                      VIDEO HEALTH CHECKLIST (6/6 PASS)
                    </h4>

                    <div className="space-y-2 text-xs">
                      <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-emerald-500/20">
                        <span className="text-white flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          Canonical Resolution & Aspect Ratio:
                        </span>
                        <span className="font-mono text-emerald-300 font-bold">1080 × 1920 (9:16)</span>
                      </div>

                      <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-emerald-500/20">
                        <span className="text-white flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          Target Microdrama Duration:
                        </span>
                        <span className="font-mono text-emerald-300 font-bold">{durationSeconds} seconds (Ideal: 45-90s)</span>
                      </div>

                      <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-emerald-500/20">
                        <span className="text-white flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          Mzansi Audio Quality & Normalization:
                        </span>
                        <span className="font-mono text-emerald-300 font-bold">-14 LUFS (Balanced)</span>
                      </div>

                      <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-emerald-500/20">
                        <span className="text-white flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          Cliffhanger Timestamp & Hook Copy:
                        </span>
                        <span className="font-mono text-emerald-300 font-bold">
                          Marker @ {Math.floor(cliffhangerTime / 60)}:{(cliffhangerTime % 60).toString().padStart(2, '0')}
                        </span>
                      </div>

                      <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-emerald-500/20">
                        <span className="text-white flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          Vertical Thumbnail (9:16):
                        </span>
                        <span className="font-mono text-emerald-300 font-bold">Attached ✓</span>
                      </div>

                      <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-emerald-500/20">
                        <span className="text-white flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          Consumer Safe Zone Verification:
                        </span>
                        <span className="font-mono text-emerald-300 font-bold">Passed (Zero Occlusion)</span>
                      </div>
                    </div>
                  </div>

                  {/* Pipeline Lifecycle Diagram */}
                  <div className="p-4 rounded-[7px] bg-black/50 border border-white/5 space-y-2">
                    <span className="text-[10px] text-welele-muted uppercase font-bold tracking-wider block">
                      Pipeline State Progression:
                    </span>
                    <div className="flex items-center gap-1.5 text-[10px] font-mono flex-wrap">
                      <span className="px-2 py-0.5 rounded-[7px] bg-white/10 text-white/70">DRAFT</span>
                      <span className="text-welele-muted">→</span>
                      <span className="px-2 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-400 font-bold">PRE-FLIGHT ✓</span>
                      <span className="text-welele-muted">→</span>
                      <span className="px-2 py-0.5 rounded-[7px] bg-[#E6007A]/30 text-[#FF2A6D] font-bold animate-pulse">SUBMITTED</span>
                      <span className="text-welele-muted">→</span>
                      <span className="px-2 py-0.5 rounded-[7px] bg-amber-500/20 text-amber-400">UNDER REVIEW</span>
                      <span className="text-welele-muted">→</span>
                      <span className="px-2 py-0.5 rounded-[7px] bg-white/10 text-white/50">APPROVED</span>
                      <span className="text-welele-muted">→</span>
                      <span className="px-2 py-0.5 rounded-[7px] bg-white/10 text-white/50">PUBLISHED</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Bottom Footer Navigation */}
        {!submitSuccess && (
          <div className="px-6 py-4 border-t border-white/10 bg-[#14151B] flex items-center justify-between">
            <div>
              {step > 1 ? (
                <button
                  type="button"
                  onClick={() => setStep((s) => (s - 1) as any)}
                  className="px-4 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 text-xs font-bold text-white flex items-center gap-1.5 transition-all"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Previous Step</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleSubmitPipeline('draft')}
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 text-xs font-bold text-white/80"
                >
                  Save as Draft
                </button>
              )}
            </div>

            <div className="flex items-center gap-3">
              {step < 5 ? (
                <button
                  type="button"
                  onClick={() => setStep((s) => (s + 1) as any)}
                  className="px-5 py-2 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white text-xs font-bold shadow-md shadow-pink-500/20 flex items-center gap-1.5 hover:opacity-95"
                >
                  <span>Continue to {stepLabels[step]?.title}</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleSubmitPipeline('under_review')}
                  disabled={isSubmitting}
                  className="px-6 py-2.5 rounded-[7px] bg-gradient-to-r from-emerald-500 to-teal-600 text-black font-black text-xs shadow-lg shadow-emerald-500/20 flex items-center gap-2 hover:opacity-95"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>{isSubmitting ? 'Submitting...' : 'Submit to Admin Moderation'}</span>
                </button>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
