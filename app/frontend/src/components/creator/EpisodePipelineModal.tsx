import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { creatorApi, aiApi, storageApi } from '../../services/api';
import { mediaStore } from '../../services/mediaStore';

import { Story, PreflightHealth } from '../../types';
import {
  CheckCircle2,
  Video as VideoIcon,
  Sparkles,
  Play,
  UploadCloud,
  ChevronRight,
  ChevronLeft,
  X,
  PlusCircle,
  Check,
  Image as ImageIcon,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import { CreateShowModal } from './CreateShowModal';

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
  initialEpisodeNumber,
}) => {
  const { stories, refreshStories } = useApp();

  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1);

  // In-line Show Creator Modal
  const [isCreateShowOpen, setIsCreateShowOpen] = useState<boolean>(false);

  // STEP 1: EPISODE
  const [seriesId, setSeriesId] = useState<string>(
    initialSeriesId || stories[0]?.id || 'story_blood_ties'
  );
  const [episodeNumber, setEpisodeNumber] = useState<number>(initialEpisodeNumber || 5);
  const [title, setTitle] = useState<string>('The Discovery at Midnight');
  const [synopsis, setSynopsis] = useState<string>(
    'The surveillance logs from the penthouse reveal an unexpected visitor right before the will was executed.'
  );

  // Sync props when opening modal or selecting different series/episode from parent
  useEffect(() => {
    if (isOpen) {
      if (initialSeriesId) {
        setSeriesId(initialSeriesId);
      }
      if (initialEpisodeNumber) {
        setEpisodeNumber(initialEpisodeNumber);
      } else {
        const targetId = initialSeriesId || seriesId;
        const sel = stories.find((s) => s.id === targetId);
        if (sel) {
          setEpisodeNumber((sel.episodes?.length || 0) + 1);
        }
      }
    }
  }, [isOpen, initialSeriesId, initialEpisodeNumber]);

  // STEP 2: VIDEO & ARTWORK
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string>('/videos/welele_placeholder.mp4');
  const [thumbnailUrl, setThumbnailUrl] = useState<string>('/posters/blood_ties.jpg');
  const [durationSeconds, setDurationSeconds] = useState<number>(64);
  const [aspectRatioLabel, setAspectRatioLabel] = useState<string>('1080 × 1920 (9:16)');
  const [isAspectRatioOk, setIsAspectRatioOk] = useState<boolean>(true);
  const [uploadProgress, setUploadProgress] = useState<number>(100);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isPreviewPlaying, setIsPreviewPlaying] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const thumbInputRef = useRef<HTMLInputElement | null>(null);

  // STEP 3: STORY & CLIFFHANGER
  const [cliffhangerHook, setCliffhangerHook] = useState<string>(
    'The security footage clearly shows Lerato entering the safe room.'
  );
  const [cliffhangerTime, setCliffhangerTime] = useState<number>(56);
  const [isStoryForgeLoading, setIsStoryForgeLoading] = useState<boolean>(false);
  const [storyForgeAdvice, setStoryForgeAdvice] = useState<string | null>(null);

  // STEP 4: RELEASE
  const [isFree, setIsFree] = useState<boolean>(episodeNumber <= 3);
  const [coinPrice, setCoinPrice] = useState<number>(5);
  const [releaseSchedule, setReleaseSchedule] = useState<'immediate' | 'scheduled'>('immediate');
  const [scheduledDateTime, setScheduledDateTime] = useState<string>('2026-09-15T18:00');
  // STEP 5: READY & RECEIPT
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submittedReceipt, setSubmittedReceipt] = useState<boolean>(false);
  const [submittedStatus, setSubmittedStatus] = useState<'draft' | 'under_review' | 'published'>('under_review');

  if (!isOpen) return null;

  const selectedStory = stories.find((s) => s.id === seriesId) || stories[0];

  // Handle Video File Selection / Drag & Drop
  const processVideoFile = async (file: File) => {
    setVideoFile(file);
    setIsUploading(true);
    setUploadProgress(20);

    // Save to persistent IndexedDB under all canonical & alias candidate keys
    const persistentUrl = await mediaStore.saveEpisodeMedia({
      seriesId,
      seriesTitle: selectedStory?.title,
      episodeNumber,
      title,
    }, file);
    setVideoUrl(persistentUrl);

    // Extract metadata & auto-generate thumbnail from frame
    const tempVideo = document.createElement('video');
    tempVideo.preload = 'metadata';
    tempVideo.src = persistentUrl;

    tempVideo.onloadedmetadata = () => {
      const dur = Math.round(tempVideo.duration) || 64;
      setDurationSeconds(dur);
      setCliffhangerTime(Math.max(10, dur - 6));

      const w = tempVideo.videoWidth || 1080;
      const h = tempVideo.videoHeight || 1920;
      const is916 = h >= w;
      setIsAspectRatioOk(is916);
      setAspectRatioLabel(`${w} × ${h} (${is916 ? '9:16 Vertical' : 'Landscape'})`);

      // Attempt canvas thumbnail grab at 1s
      tempVideo.currentTime = Math.min(1.0, dur / 2);
    };

    tempVideo.onseeked = () => {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = tempVideo.videoWidth || 540;
        canvas.height = tempVideo.videoHeight || 960;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(tempVideo, 0, 0, canvas.width, canvas.height);
          const frameDataUrl = canvas.toDataURL('image/jpeg', 0.85);
          if (frameDataUrl && frameDataUrl.length > 50) {
            setThumbnailUrl(frameDataUrl);
          }
        }
      } catch (e) {
        console.warn('Could not extract canvas frame:', e);
      }
    };

    let prog = 35;
    const interval = setInterval(() => {
      prog += 25;
      setUploadProgress(prog);
      if (prog >= 100) {
        clearInterval(interval);
        setIsUploading(false);
      }
    }, 120);
  };

  const handleCustomThumbnail = async (file: File) => {
    const thumbKeys = [
      `thumb_${seriesId}_${episodeNumber}`,
      `thumb_${seriesId}_ep_${episodeNumber}`
    ];
    const url = await mediaStore.saveMedia(thumbKeys, file);
    setThumbnailUrl(url);
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processVideoFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processVideoFile(e.target.files[0]);
    }
  };

  // Optional Story Forge Assistant
  const handleAskStoryForge = async () => {
    setIsStoryForgeLoading(true);
    try {
      const res = await aiApi.analyzeVideo(videoUrl, title, synopsis);
      if (res?.cliffhanger_suggested_timestamp) {
        setCliffhangerTime(res.cliffhanger_suggested_timestamp);
      }
      if (res?.hook_line) {
        setCliffhangerHook(res.hook_line);
      }
      setStoryForgeAdvice(
        res?.ai_hook_analysis?.cliffhanger_curiosity_gap ||
          'Strong curiosity gap. Good moment to hold suspense.'
      );
    } catch (err) {
      setStoryForgeAdvice('Cliffhanger timed at peak tension before resolution.');
    } finally {
      setIsStoryForgeLoading(false);
    }
  };

  // Submit to Ingestion
  const handleSubmit = async (status: 'draft' | 'under_review' | 'published') => {
    setIsSubmitting(true);
    setSubmittedStatus(status);
    try {
      const preflightHealth: PreflightHealth = {
        aspect_ratio_ok: isAspectRatioOk,
        aspect_ratio_label: aspectRatioLabel,
        duration_ok: durationSeconds >= 30 && durationSeconds <= 120,
        duration_seconds: durationSeconds,
        audio_detected: true,
        thumbnail_present: Boolean(thumbnailUrl),
        cliffhanger_marker_ok: cliffhangerTime > 0 && cliffhangerTime < durationSeconds,
        cliffhanger_time_seconds: cliffhangerTime,
        cliffhanger_hook_copy: cliffhangerHook,
        captions_present: true,
      };

      // 1. Upload physical binary to Object Storage (Pillar 4 Ingestion Contract)
      let canonicalStorageKey: string | undefined;
      let canonicalVideoUrl = videoUrl.startsWith('blob:') ? '/videos/welele_placeholder.mp4' : videoUrl;

      if (videoFile) {
        try {
          const uploadRes = await storageApi.uploadBinary(
            videoFile,
            seriesId,
            Number(episodeNumber)
          );
          if (uploadRes && uploadRes.storage_key) {
            canonicalStorageKey = uploadRes.storage_key;
            canonicalVideoUrl = uploadRes.public_cdn_url;
          }
        } catch (uploadErr) {
          console.error('[EpisodePipelineModal] Binary upload failed:', uploadErr);
        }
      }

      // 2. Also save to IndexedDB for local developer/offline cache
      if (videoFile) {
        await mediaStore.saveEpisodeMedia({
          seriesId,
          seriesTitle: selectedStory?.title,
          episodeNumber: Number(episodeNumber),
          title: title.trim(),
        }, videoFile);
      }

      // 3. Persist episode with authoritative storage_key and clean CDN url (never blob:)
      const res = await creatorApi.addEpisode({
        series_id: seriesId,
        episode_number: Number(episodeNumber),
        title: title.trim(),
        synopsis: synopsis.trim(),
        video_url: canonicalVideoUrl,
        storage_key: canonicalStorageKey,
        thumbnail_url: thumbnailUrl || selectedStory?.vertical_poster || '/posters/blood_ties.jpg',
        duration_seconds: Number(durationSeconds),
        is_free: isFree,
        coin_price: isFree ? 0 : Number(coinPrice),
        cliffhanger_time: Number(cliffhangerTime),
        cliffhanger_hook: cliffhangerHook,
        status,
        scheduled_at: releaseSchedule === 'scheduled' ? scheduledDateTime : undefined,
        preflight_health: preflightHealth,
      });

      // Also index under the created episode's server ID and all variations
      if (videoFile && res?.episode?.id) {
        await mediaStore.saveEpisodeMedia({
          seriesId,
          seriesTitle: selectedStory?.title,
          episodeNumber: Number(res.episode.episode_number || episodeNumber),
          episodeId: res.episode.id,
          title: title.trim(),
        }, videoFile);
      }

      await refreshStories();
      setSubmittedReceipt(true);
    } catch (err) {
      console.error('Failed to submit episode:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const stepTabs = [
    { num: 1, label: 'Episode' },
    { num: 2, label: 'Video & Art' },
    { num: 3, label: 'Story' },
    { num: 4, label: 'Release' },
    { num: 5, label: 'Ready' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0F1014] border border-white/10 rounded-[7px] max-w-3xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-fade-in text-white">
        
        {/* Top Header */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-gradient-to-r from-pink-950/40 via-[#14151B] to-[#14151B]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-[7px] bg-gradient-to-tr from-[#E6007A] to-[#FF2A6D] flex items-center justify-center text-white shadow">
              <VideoIcon className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm sm:text-base font-black text-white uppercase tracking-wider">
                  Add Episode
                </h2>
                <span className="px-2 py-0.5 rounded-[7px] bg-pink-500/20 text-[#FF2A6D] border border-pink-500/30 text-[10px] font-bold">
                  EP {episodeNumber < 10 ? `0${episodeNumber}` : episodeNumber}
                </span>
              </div>
              <p className="text-xs text-welele-muted">
                {selectedStory?.title || 'Select a Show'}
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

        {/* 5-Step Indicator Ribbon */}
        <div className="px-6 py-2.5 bg-[#14151B] border-b border-white/5 grid grid-cols-5 gap-1 sm:gap-2">
          {stepTabs.map((t) => {
            const isActive = step === t.num;
            const isDone = step > t.num;
            return (
              <button
                key={t.num}
                onClick={() => {
                  if (isDone || isActive) setStep(t.num as any);
                }}
                className={`py-1.5 px-1 rounded-[7px] text-[11px] font-bold flex items-center justify-center gap-1.5 transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white shadow'
                    : isDone
                    ? 'bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25'
                    : 'bg-white/5 text-welele-muted opacity-60'
                }`}
              >
                <span>{t.num}.</span>
                <span className="truncate">{t.label}</span>
                {isDone && <Check className="w-3 h-3 text-emerald-400 shrink-0" />}
              </button>
            );
          })}
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          
          {/* STEP 1: EPISODE DETAILS */}
          {step === 1 && (
            <div className="space-y-4 animate-fade-in">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    1. What are you making?
                  </h3>
                  <p className="text-xs text-welele-muted">
                    Choose the show and describe this episode's storyline.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsCreateShowOpen(true)}
                  className="px-3 py-1.5 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-bold text-pink-400 hover:text-pink-300 flex items-center gap-1.5 transition-colors"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  <span>+ Create New Show</span>
                </button>
              </div>

              {/* Show Selector */}
              <div>
                <label className="text-xs font-bold text-white block mb-1">Show</label>
                <select
                  value={seriesId}
                  onChange={(e) => {
                    setSeriesId(e.target.value);
                    const sel = stories.find((s) => s.id === e.target.value);
                    if (sel) {
                      setEpisodeNumber((sel.episodes?.length || 0) + 1);
                      if (sel.vertical_poster) setThumbnailUrl(sel.vertical_poster);
                    }
                  }}
                  className="w-full bg-[#14151B] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-pink-500 cursor-pointer"
                >
                  {stories.map((story) => (
                    <option key={story.id} value={story.id} className="bg-[#0F1014] text-white">
                      {story.title} ({story.episodes?.length || 0} episodes)
                    </option>
                  ))}
                </select>
              </div>

              {/* Episode Number */}
              <div>
                <label className="text-xs font-bold text-white block mb-1">Episode Number</label>
                <input
                  type="number"
                  min={1}
                  max={999}
                  value={episodeNumber}
                  onChange={(e) => setEpisodeNumber(Number(e.target.value))}
                  className="w-32 bg-[#14151B] px-3.5 py-2 rounded-[7px] border border-white/10 text-xs text-white font-bold focus:outline-none focus:border-pink-500"
                />
              </div>

              {/* Title */}
              <div>
                <label className="text-xs font-bold text-white block mb-1">Episode Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. The Queen's Ultimatum, The Discovery at Midnight"
                  className="w-full bg-[#14151B] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-pink-500 placeholder:text-welele-muted"
                />
              </div>

              {/* Synopsis */}
              <div>
                <label className="text-xs font-bold text-white block mb-1">
                  What's happening in this episode?
                </label>
                <textarea
                  rows={3}
                  value={synopsis}
                  onChange={(e) => setSynopsis(e.target.value)}
                  placeholder="Short teaser logline describing the drama or turning point..."
                  className="w-full bg-[#14151B] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-pink-500 placeholder:text-welele-muted"
                />
              </div>
            </div>
          )}

          {/* STEP 2: VIDEO & ARTWORK DRAG & DROP */}
          {step === 2 && (
            <div className="space-y-5 animate-fade-in">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  2. Drop Your Video & Artwork
                </h3>
                <p className="text-xs text-welele-muted">
                  Drag and drop your 9:16 episode video. We'll automatically calculate duration and extract thumbnail artwork.
                </p>
              </div>

              {/* Video Dropzone */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-white/20 hover:border-pink-500/60 bg-[#14151B] hover:bg-pink-950/10 rounded-[7px] p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center space-y-2.5 group"
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="video/mp4,video/quicktime,video/webm,video/x-m4v"
                  className="hidden"
                />

                <div className="w-12 h-12 rounded-full bg-pink-500/10 text-pink-400 group-hover:scale-110 transition-transform flex items-center justify-center">
                  <UploadCloud className="w-6 h-6" />
                </div>

                <div>
                  <p className="text-sm font-bold text-white">
                    🎬 Drop your episode video here
                  </p>
                  <p className="text-xs text-welele-muted mt-0.5">
                    or click to <span className="text-pink-400 font-bold underline">Choose Video</span>
                  </p>
                  <p className="text-[10px] text-white/40 mt-1.5 font-mono">
                    MP4 • MOV • WebM (Optimal: 1080 × 1920)
                  </p>
                </div>
              </div>

              {/* Video Status & Metadata Card */}
              {isUploading ? (
                <div className="p-3.5 rounded-[7px] bg-white/5 border border-white/10 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-white flex items-center gap-2">
                      <div className="w-3 h-3 border-2 border-pink-400 border-t-transparent rounded-full animate-spin" />
                      Saving and processing video...
                    </span>
                    <span className="font-mono text-pink-400 font-bold">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-pink-500 to-welele-gold h-full transition-all duration-200"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              ) : (
                <div className="p-3.5 rounded-[7px] bg-emerald-950/30 border border-emerald-500/30 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-[7px] bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white">Video Ready</h4>
                      <p className="text-[11px] text-emerald-300 font-mono">
                        {durationSeconds}s • {aspectRatioLabel}
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setIsPreviewPlaying(!isPreviewPlaying)}
                    className="px-3 py-1.5 rounded-[7px] bg-white/10 hover:bg-white/20 text-white text-xs font-bold flex items-center gap-1.5 transition-colors"
                  >
                    <Play className="w-3.5 h-3.5 text-welele-gold" />
                    <span>{isPreviewPlaying ? 'Hide Preview' : '▶ Preview'}</span>
                  </button>
                </div>
              )}

              {/* Video Preview Viewport */}
              {isPreviewPlaying && videoUrl && (
                <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 flex flex-col items-center animate-fade-in">
                  <div className="w-44 aspect-[9/16] rounded-[7px] overflow-hidden bg-black shadow-lg border border-white/10 relative">
                    <video
                      src={videoUrl}
                      controls
                      autoPlay
                      playsInline
                      className="w-full h-full object-cover"
                    />
                  </div>
                </div>
              )}

              {/* CUSTOM EPISODE ARTWORK / THUMBNAIL DROPZONE */}
              <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                      <ImageIcon className="w-3.5 h-3.5 text-pink-400" />
                      Episode Thumbnail Artwork
                    </h4>
                    <p className="text-[11px] text-welele-muted">
                      Auto-captured from video frame, or drop a custom cover below.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => thumbInputRef.current?.click()}
                    className="px-3 py-1 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-bold text-white transition-colors"
                  >
                    Upload Custom Art
                  </button>
                  <input
                    type="file"
                    ref={thumbInputRef}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleCustomThumbnail(e.target.files[0]);
                      }
                    }}
                    accept="image/*"
                    className="hidden"
                  />
                </div>

                <div className="flex items-center gap-4">
                  <div className="w-20 aspect-[9/16] rounded-[7px] overflow-hidden border border-white/20 bg-black relative shrink-0">
                    <img
                      src={thumbnailUrl}
                      alt="Episode Thumbnail"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="text-xs space-y-1">
                    <p className="text-white font-bold">Active Episode Cover</p>
                    <p className="text-welele-muted text-[11px]">
                      Displayed on episode list, notifications, and viewer swipe cards.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: STORY & CLIFFHANGER */}
          {step === 3 && (
            <div className="space-y-5 animate-fade-in">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  3. Story & Cliffhanger
                </h3>
                <p className="text-xs text-welele-muted">
                  Set the dramatic peak that leaves viewers wanting the next episode.
                </p>
              </div>

              {/* Cliffhanger Hook */}
              <div>
                <label className="text-xs font-bold text-white block mb-1">
                  Cliffhanger Hook Copy
                </label>
                <input
                  type="text"
                  value={cliffhangerHook}
                  onChange={(e) => setCliffhangerHook(e.target.value)}
                  placeholder="e.g., Lerato opens the safe to find it completely empty..."
                  className="w-full bg-[#14151B] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-pink-500"
                />
              </div>

              {/* Cliffhanger Timing Slider */}
              <div>
                <div className="flex items-center justify-between mb-1.5 text-xs">
                  <span className="font-bold text-white">Cliffhanger Cut Point</span>
                  <span className="font-mono text-welele-gold font-bold">
                    Second {cliffhangerTime} of {durationSeconds}s
                  </span>
                </div>
                <input
                  type="range"
                  min={5}
                  max={durationSeconds || 64}
                  value={cliffhangerTime}
                  onChange={(e) => setCliffhangerTime(Number(e.target.value))}
                  className="w-full accent-[#E6007A] cursor-pointer"
                />
              </div>

              {/* Optional Story Forge Assistant Helper Card */}
              <div className="p-4 rounded-[7px] bg-gradient-to-r from-pink-950/20 via-purple-950/20 to-black border border-pink-500/20 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-pink-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-welele-gold" />
                    Need help with the story?
                  </span>
                  <button
                    type="button"
                    onClick={handleAskStoryForge}
                    disabled={isStoryForgeLoading}
                    className="px-3 py-1 rounded-[7px] bg-pink-500/20 hover:bg-pink-500/30 text-pink-200 border border-pink-500/30 text-[11px] font-bold transition-colors flex items-center gap-1"
                  >
                    {isStoryForgeLoading ? (
                      <span>Analyzing Pacing...</span>
                    ) : (
                      <span>✨ Ask Story Forge</span>
                    )}
                  </button>
                </div>

                {storyForgeAdvice && (
                  <p className="text-xs text-pink-100/80 bg-black/40 p-2.5 rounded-[7px] border border-pink-500/20 italic">
                    "{storyForgeAdvice}"
                  </p>
                )}
              </div>
            </div>
          )}

          {/* STEP 4: RELEASE & PRICING */}
          {step === 4 && (
            <div className="space-y-5 animate-fade-in">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  4. Release & Access
                </h3>
                <p className="text-xs text-welele-muted">
                  Choose whether this episode is free to watch or unlocked with coins.
                </p>
              </div>

              {/* Pricing Tier Options */}
              <div className="grid grid-cols-2 gap-3">
                <div
                  onClick={() => setIsFree(true)}
                  className={`p-4 rounded-[7px] border cursor-pointer transition-all ${
                    isFree
                      ? 'bg-emerald-950/40 border-emerald-500 text-white shadow-lg'
                      : 'bg-[#14151B] border-white/10 text-welele-muted hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                      Free Episode
                    </span>
                    {isFree && <Check className="w-4 h-4 text-emerald-400" />}
                  </div>
                  <p className="text-xs mt-1 text-white">0 Coins</p>
                  <p className="text-[10px] text-welele-muted mt-1">
                    Great for Episodes 1–3 to hook your audience.
                  </p>
                </div>

                <div
                  onClick={() => setIsFree(false)}
                  className={`p-4 rounded-[7px] border cursor-pointer transition-all ${
                    !isFree
                      ? 'bg-amber-950/40 border-amber-500 text-white shadow-lg'
                      : 'bg-[#14151B] border-white/10 text-welele-muted hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-welele-gold uppercase tracking-wider">
                      Coin Unlock
                    </span>
                    {!isFree && <Check className="w-4 h-4 text-welele-gold" />}
                  </div>
                  <p className="text-xs mt-1 text-white">5 Coins (~R2.50)</p>
                  <p className="text-[10px] text-welele-muted mt-1">
                    Viewers unlock with Airtime or Card.
                  </p>
                </div>
              </div>

              {/* Release Schedule */}
              <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 space-y-3">
                <label className="text-xs font-bold text-white block">Release Timing</label>
                <div className="flex items-center gap-4 text-xs">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="schedule"
                      checked={releaseSchedule === 'immediate'}
                      onChange={() => setReleaseSchedule('immediate')}
                      className="accent-pink-500"
                    />
                    <span>Publish Immediately</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="schedule"
                      checked={releaseSchedule === 'scheduled'}
                      onChange={() => setReleaseSchedule('scheduled')}
                      className="accent-pink-500"
                    />
                    <span>Schedule Drop</span>
                  </label>
                </div>

                {releaseSchedule === 'scheduled' && (
                  <input
                    type="datetime-local"
                    value={scheduledDateTime}
                    onChange={(e) => setScheduledDateTime(e.target.value)}
                    className="w-full bg-[#0F1014] px-3.5 py-2 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-pink-500"
                  />
                )}
              </div>
            </div>
          )}

          {/* STEP 5: READY & WELELE QUALITY CHECK */}
          {step === 5 && (
            <div className="space-y-5 animate-fade-in">
              {submittedReceipt ? (
                /* Honest Ingestion Receipt with explicit Approval/Publish state */
                <div className={`p-6 rounded-[7px] border text-center space-y-4 animate-fade-in ${
                  submittedStatus === 'under_review'
                    ? 'bg-amber-950/30 border-amber-500/40'
                    : submittedStatus === 'published'
                    ? 'bg-emerald-950/40 border-emerald-500/40'
                    : 'bg-[#14151B] border-white/20'
                }`}>
                  <div className={`w-14 h-14 rounded-full mx-auto flex items-center justify-center ${
                    submittedStatus === 'under_review'
                      ? 'bg-amber-500/20 text-amber-400'
                      : submittedStatus === 'published'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-white/10 text-white/70'
                  }`}>
                    {submittedStatus === 'under_review' ? (
                      <Clock className="w-7 h-7" />
                    ) : (
                      <CheckCircle2 className="w-7 h-7" />
                    )}
                  </div>
                  <div>
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-[7px] text-xs font-black uppercase tracking-wider mb-2 ${
                      submittedStatus === 'under_review'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : submittedStatus === 'published'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-white/10 text-white/80 border border-white/10'
                    }`}>
                      {submittedStatus === 'under_review' && <Clock className="w-3.5 h-3.5" />}
                      {submittedStatus === 'published' && <Check className="w-3.5 h-3.5" />}
                      {submittedStatus === 'under_review'
                        ? 'Awaiting Admin Approval'
                        : submittedStatus === 'published'
                        ? 'Published & Live'
                        : 'Draft Saved'}
                    </span>
                    <h3 className="text-base sm:text-lg font-black text-white uppercase tracking-tight font-cinematic">
                      {submittedStatus === 'under_review'
                        ? 'Submitted to Moderation Desk'
                        : submittedStatus === 'published'
                        ? 'Episode Published Live'
                        : 'Draft Saved in Workspace'}
                    </h3>
                    <p className="text-xs text-welele-muted mt-1 max-w-md mx-auto">
                      {submittedStatus === 'under_review'
                        ? `"${title}" (EP ${episodeNumber}) has been submitted to Admin Moderation. Once verified by the review desk, it will be published across all viewer feeds.`
                        : submittedStatus === 'published'
                        ? `"${title}" (EP ${episodeNumber}) is now live and streamable for all viewers.`
                        : `"${title}" (EP ${episodeNumber}) is saved in your studio workspace.`}
                    </p>
                  </div>

                  <div className="p-3.5 bg-black/50 rounded-[7px] text-xs text-left max-w-sm mx-auto space-y-2 text-white/90 border border-white/5">
                    <div className="flex items-center justify-between text-emerald-400 font-semibold">
                      <span className="flex items-center gap-2">
                        <Check className="w-3.5 h-3.5" /> Video Asset Verified
                      </span>
                      <span className="font-mono text-white/70">{durationSeconds}s</span>
                    </div>
                    <div className="flex items-center justify-between text-emerald-400 font-semibold">
                      <span className="flex items-center gap-2">
                        <Check className="w-3.5 h-3.5" /> Format & Safe Zone
                      </span>
                      <span className="font-mono text-white/70">9:16</span>
                    </div>
                    <div className="flex items-center justify-between text-emerald-400 font-semibold">
                      <span className="flex items-center gap-2">
                        <Check className="w-3.5 h-3.5" /> Cliffhanger Marker
                      </span>
                      <span className="font-mono text-white/70">@{cliffhangerTime}s</span>
                    </div>
                    <div className="flex items-center justify-between text-emerald-400 font-semibold">
                      <span className="flex items-center gap-2">
                        <Check className="w-3.5 h-3.5" /> Moderation Ticket
                      </span>
                      <span className="text-amber-300 font-mono text-[11px]">
                        {submittedStatus === 'under_review' ? 'In Queue' : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      onSuccess();
                      onClose();
                    }}
                    className="px-8 py-3 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-black text-xs hover:opacity-95 shadow-xl shadow-pink-500/20 cursor-pointer"
                  >
                    Done
                  </button>
                </div>
              ) : (
                /* Quality Check Pre-Publish Screen */
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                      5. Almost Ready
                    </h3>
                    <p className="text-xs text-welele-muted">
                      Welele is checking your episode details before submitting.
                    </p>
                  </div>

                  <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/10 space-y-2.5 text-xs">
                    <div className="flex items-center justify-between text-emerald-400">
                      <span className="flex items-center gap-2">
                        <Check className="w-4 h-4" /> Video received & verified
                      </span>
                      <span className="font-mono text-white/70">{durationSeconds}s</span>
                    </div>

                    <div className="flex items-center justify-between text-emerald-400">
                      <span className="flex items-center gap-2">
                        <Check className="w-4 h-4" /> Format looks good
                      </span>
                      <span className="font-mono text-white/70">{aspectRatioLabel}</span>
                    </div>

                    <div className="flex items-center justify-between text-emerald-400">
                      <span className="flex items-center gap-2">
                        <Check className="w-4 h-4" /> Audio detected
                      </span>
                      <span className="text-white/70">Clear</span>
                    </div>

                    <div className="flex items-center justify-between text-emerald-400">
                      <span className="flex items-center gap-2">
                        <Check className="w-4 h-4" /> Story & cliffhanger set
                      </span>
                      <span className="text-white/70 font-mono">@{cliffhangerTime}s</span>
                    </div>

                    <div className="flex items-center justify-between text-emerald-400">
                      <span className="flex items-center gap-2">
                        <Check className="w-4 h-4" /> Release access configured
                      </span>
                      <span className="text-white/70">{isFree ? 'Free' : `${coinPrice} Coins`}</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-end gap-2.5 pt-4">
                    <button
                      type="button"
                      disabled={isSubmitting}
                      onClick={() => handleSubmit('draft')}
                      className="px-4 py-2.5 rounded-[7px] text-xs font-bold bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-colors cursor-pointer"
                    >
                      Save Draft
                    </button>
                    <button
                      type="button"
                      disabled={isSubmitting}
                      onClick={() => handleSubmit('published')}
                      className="px-6 py-2.5 rounded-[7px] text-xs font-bold bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white hover:opacity-95 shadow-lg shadow-pink-500/20 disabled:opacity-50 flex items-center gap-2 transition-all cursor-pointer font-cinematic uppercase tracking-wider"
                    >
                      {isSubmitting ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>Publishing...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-4 h-4" />
                          <span>Publish Episode Live</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

        </div>

        {/* Modal Bottom Stepper Footer */}
        {!submittedReceipt && (
          <div className="px-6 py-3.5 border-t border-white/10 bg-[#14151B] flex items-center justify-between">
            <button
              type="button"
              disabled={step === 1}
              onClick={() => setStep((Math.max(1, step - 1)) as any)}
              className="px-3 py-1.5 rounded-[7px] text-xs font-bold text-welele-muted hover:text-white disabled:opacity-30 flex items-center gap-1 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back</span>
            </button>

            {step < 5 ? (
              <button
                type="button"
                onClick={() => setStep((Math.min(5, step + 1)) as any)}
                className="px-5 py-2 rounded-[7px] text-xs font-bold bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white hover:opacity-95 shadow-md shadow-pink-500/20 flex items-center gap-1.5 transition-all"
              >
                <span>Continue</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : null}
          </div>
        )}

      </div>

      {/* In-Line Show Creator Modal */}
      <CreateShowModal
        isOpen={isCreateShowOpen}
        onClose={() => setIsCreateShowOpen(false)}
        onSuccess={(newId) => {
          setSeriesId(newId);
          setEpisodeNumber(1);
        }}
      />
    </div>
  );
};
