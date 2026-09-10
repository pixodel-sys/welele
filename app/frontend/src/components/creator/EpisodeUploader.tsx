import React, { useState, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { creatorApi, aiApi, storageApi } from '../../services/api';
import { mediaStore } from '../../services/mediaStore';
import {
  UploadCloud,
  Sparkles,
  CheckCircle,
  Video,
  Languages,
  Zap,
  ArrowLeft,
  Clock,
  ShieldCheck,
  Server,
} from 'lucide-react';

interface EpisodeUploaderProps {
  onBack: () => void;
  onSuccess: () => void;
}

export const EpisodeUploader: React.FC<EpisodeUploaderProps> = ({ onBack, onSuccess }) => {
  const { stories, refreshStories } = useApp();

  const [selectedSeriesId, setSelectedSeriesId] = useState<string>(
    stories[0]?.id || 'story_amber_heir'
  );
  const [episodeNumber, setEpisodeNumber] = useState<number>(7);
  const [title, setTitle] = useState<string>('The Queen Mother’s Ultimatum');
  const [synopsis, setSynopsis] = useState<string>(
    'The ancient council convenes at midnight in the royal estate to deliver their final decision on the amber throne.'
  );
  const [videoUrl, setVideoUrl] = useState<string>(
    '/videos/welele_placeholder.mp4'
  );
  const [thumbnailUrl, setThumbnailUrl] = useState<string>(
    'https://images.unsplash.com/photo-1509967419530-da38b4704bc6?auto=format&fit=crop&w=600&q=80'
  );
  const [durationSeconds, setDurationSeconds] = useState<number>(85);
  const [cliffhangerTime, setCliffhangerTime] = useState<number>(72);
  const [isFree, setIsFree] = useState<boolean>(false);
  const [coinPrice, setCoinPrice] = useState<number>(5);

  // Object Storage (Pillar 4) Pre-signed Upload State
  const [presignedInfo, setPresignedInfo] = useState<any>(null);
  const [isRequestingPresigned, setIsRequestingPresigned] = useState<boolean>(false);

  // Welele AI Processing States
  const [isAnalyzingAI, setIsAnalyzingAI] = useState<boolean>(false);
  const [aiAnalysisResult, setAiAnalysisResult] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleGetPresignedUpload = async () => {
    setIsRequestingPresigned(true);
    try {
      const res = await storageApi.getPresignedUploadUrl(
        selectedSeriesId,
        Number(episodeNumber),
        'master_9_16_raw.mp4'
      );
      setPresignedInfo(res.upload);
      if (res.upload?.playback_url) {
        setVideoUrl(res.upload.playback_url);
      }
    } catch (err) {
      console.error('Failed to request presigned upload URL:', err);
    } finally {
      setIsRequestingPresigned(false);
    }
  };

  const handleRunWeleleAI = async () => {
    setIsAnalyzingAI(true);
    try {
      // Call Python backend Welele AI™ endpoint
      const res = await aiApi.analyzeVideo(videoUrl, title, synopsis);
      setAiAnalysisResult(res);
      if (res.cliffhanger_suggested_timestamp) {
        setCliffhangerTime(res.cliffhanger_suggested_timestamp);
      }
    } catch (err) {
      console.error('AI analysis error:', err);
    } finally {
      setIsAnalyzingAI(false);
    }
  };

  const [videoFile, setVideoFile] = useState<File | null>(null);

  const handleVideoFileChange = async (file: File) => {
    setVideoFile(file);
    const targetStory = stories.find((s) => s.id === selectedSeriesId);
    const blobUrl = await mediaStore.saveEpisodeMedia({
      seriesId: selectedSeriesId,
      seriesTitle: targetStory?.title,
      episodeNumber: Number(episodeNumber),
      title: title.trim(),
    }, file);
    setVideoUrl(blobUrl);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const targetStory = stories.find((s) => s.id === selectedSeriesId);
      if (videoFile) {
        await mediaStore.saveEpisodeMedia({
          seriesId: selectedSeriesId,
          seriesTitle: targetStory?.title,
          episodeNumber: Number(episodeNumber),
          title: title.trim(),
        }, videoFile);
      }

      const res = await creatorApi.addEpisode({
        series_id: selectedSeriesId,
        episode_number: Number(episodeNumber),
        title,
        synopsis,
        video_url: videoUrl,
        thumbnail_url: thumbnailUrl,
        duration_seconds: Number(durationSeconds),
        is_free: isFree,
        coin_price: isFree ? 0 : Number(coinPrice),
        cliffhanger_time: Number(cliffhangerTime),
      });

      if (videoFile && res?.episode?.id) {
        await mediaStore.saveEpisodeMedia({
          seriesId: selectedSeriesId,
          seriesTitle: targetStory?.title,
          episodeNumber: Number(res.episode.episode_number || episodeNumber),
          episodeId: res.episode.id,
          title: title.trim(),
        }, videoFile);
      }

      await refreshStories();
      setSuccessMessage('Episode successfully published to Welele™!');
      setTimeout(() => {
        onSuccess();
      }, 1800);
    } catch (err) {
      console.error('Failed to publish episode:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 pb-24 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          aria-label="Go Back"
          className="w-9 h-9 rounded-[7px] bg-welele-surface-2 hover:bg-welele-surface-3 flex items-center justify-center text-white border border-white/10"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h2 className="text-xl font-black text-white font-cinematic">
            Upload & Publish Vertical Episode
          </h2>
          <p className="text-xs text-welele-muted">
            9:16 Canonical Vertical micro-drama format with Object Storage CDN Direct Upload
          </p>
        </div>
      </div>

      <form onSubmit={handleUploadSubmit} className="space-y-5">
        {/* Series Selection */}
        <div className="p-5 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            1. Series & Episode Info
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-welele-muted block mb-1">Target Series</label>
              <select
                value={selectedSeriesId}
                onChange={(e) => setSelectedSeriesId(e.target.value)}
                className="w-full bg-welele-surface px-3 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-welele-orange"
              >
                {stories.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs text-welele-muted block mb-1">Episode Number</label>
              <input
                type="number"
                value={episodeNumber}
                onChange={(e) => setEpisodeNumber(Number(e.target.value))}
                className="w-full bg-welele-surface px-3 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-welele-orange"
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-welele-muted block mb-1">Episode Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-welele-surface px-3 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-welele-orange"
              placeholder="e.g., The Secret Coronation"
            />
          </div>

          <div>
            <label className="text-xs text-welele-muted block mb-1">Cliffhanger Synopsis</label>
            <textarea
              rows={2}
              value={synopsis}
              onChange={(e) => setSynopsis(e.target.value)}
              className="w-full bg-welele-surface px-3 py-2.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-welele-orange"
              placeholder="Describe the dramatic tension..."
            />
          </div>
        </div>

        {/* Media & Object Storage CDN Pipeline (Pillar 4) */}
        <div className="p-5 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Server className="w-4 h-4 text-welele-orange" />
              2. Object Storage & Direct Ingestion (Pillar 4)
            </h3>

            <button
              type="button"
              onClick={handleGetPresignedUpload}
              disabled={isRequestingPresigned}
              className="px-3 py-1.5 rounded-[7px] bg-white/10 hover:bg-white/20 text-white text-xs font-bold border border-white/10 flex items-center gap-1.5 transition-all"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              {isRequestingPresigned ? 'Generating Presigned URL...' : 'Request Presigned R2/S3 URL'}
            </button>
          </div>

          {presignedInfo && (
            <div className="p-3.5 rounded-[7px] bg-black/40 border border-emerald-500/30 text-[11px] space-y-1.5">
              <div className="text-emerald-300 font-bold flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" />
                Direct CDN Pre-signed Ingestion Key Resolved
              </div>
              <div className="text-welele-muted font-mono break-all text-[10px]">
                Key: {presignedInfo.storage_key}
              </div>
              <div className="text-[10px] text-welele-gold">
                Format standard: {presignedInfo.format_requirement} (Max {presignedInfo.max_duration_seconds}s)
              </div>
            </div>
          )}

          <div>
            <label className="text-xs text-welele-muted block mb-1">Upload Local Video Master (MP4 9:16)</label>
            <div className="flex items-center gap-3">
              <label className="cursor-pointer px-4 py-2.5 rounded-[7px] bg-welele-orange/20 hover:bg-welele-orange/30 border border-welele-orange/40 text-welele-orange text-xs font-bold flex items-center gap-2 transition-all">
                <UploadCloud className="w-4 h-4" />
                <span>{videoFile ? videoFile.name : 'Select Video File'}</span>
                <input
                  type="file"
                  accept="video/mp4,video/quicktime,video/webm"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleVideoFileChange(e.target.files[0]);
                    }
                  }}
                />
              </label>
              {videoFile && (
                <span className="text-[11px] text-emerald-400 font-bold flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> Indexed & Ready
                </span>
              )}
            </div>
          </div>

          <div>
            <label className="text-xs text-welele-muted block mb-1">Video Stream Pointer URL</label>
            <input
              type="text"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              className="w-full bg-welele-surface px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-welele-muted block mb-1">Duration (Seconds)</label>
              <input
                type="number"
                value={durationSeconds}
                onChange={(e) => setDurationSeconds(Number(e.target.value))}
                className="w-full bg-welele-surface px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs text-welele-muted block mb-1">
                Cliffhanger Drop (Seconds)
              </label>
              <input
                type="number"
                value={cliffhangerTime}
                onChange={(e) => setCliffhangerTime(Number(e.target.value))}
                className="w-full bg-welele-surface px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white"
              />
            </div>
          </div>

          <div className="pt-2 border-t border-white/5 flex items-center justify-between">
            <span className="text-xs text-welele-muted">Welele AI™ Cliffhanger & Aspect Verification</span>
            <button
              type="button"
              onClick={handleRunWeleleAI}
              disabled={isAnalyzingAI}
              className="px-3 py-1.5 rounded-[7px] bg-welele-orange/20 hover:bg-welele-orange/30 text-welele-orange text-xs font-bold border border-welele-orange/30 flex items-center gap-1.5 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {isAnalyzingAI ? 'Analyzing...' : 'Run Welele AI™ Analysis'}
            </button>
          </div>

          {/* AI Result Card */}
          {aiAnalysisResult && (
            <div className="p-4 rounded-[7px] bg-gradient-to-r from-welele-surface to-welele-surface-3 border border-welele-orange/30 space-y-2 animate-fade-in text-xs">
              <div className="flex items-center justify-between text-welele-gold font-bold">
                <span className="flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                  Welele AI™ Pipeline Verified
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-300">
                  {aiAnalysisResult.aspect_ratio}
                </span>
              </div>
              <p className="text-white/80 text-[11px]">
                Safety Score: <b>{aiAnalysisResult.content_safety_rating}</b> | Suggested Cliffhanger: <b>{aiAnalysisResult.cliffhanger_suggested_timestamp}s</b>
              </p>
              <div className="flex flex-wrap gap-1 mt-1">
                {aiAnalysisResult.african_cultural_context_tags.map((tag: string) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 rounded-[7px] bg-black/40 text-[9px] text-welele-orange border border-white/5"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Pricing & Monetization */}
        <div className="p-5 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            3. Monetization & Coin Price
          </h3>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer text-xs text-white">
              <input
                type="radio"
                name="isFree"
                checked={isFree}
                onChange={() => setIsFree(true)}
                className="accent-welele-orange"
              />
              <span>Free Episode (Viewer Acquisition)</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer text-xs text-white">
              <input
                type="radio"
                name="isFree"
                checked={!isFree}
                onChange={() => setIsFree(false)}
                className="accent-welele-orange"
              />
              <span>Gated Cliffhanger (Coins Required)</span>
            </label>
          </div>

          {!isFree && (
            <div className="w-48">
              <label className="text-xs text-welele-muted block mb-1">Coin Price</label>
              <div className="flex items-center gap-2 bg-welele-surface px-3 py-2 rounded-[7px] border border-white/10">
                <span>🪙</span>
                <input
                  type="number"
                  value={coinPrice}
                  onChange={(e) => setCoinPrice(Number(e.target.value))}
                  className="w-full bg-transparent text-xs text-white focus:outline-none"
                />
                <span className="text-[10px] text-welele-muted">Coins</span>
              </div>
            </div>
          )}
        </div>

        {/* Success Alert */}
        {successMessage && (
          <div className="p-3.5 rounded-[7px] bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold text-center">
            {successMessage}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3.5 rounded-[7px] bg-gradient-welele text-white font-bold text-xs shadow-xl shadow-orange-500/20 hover:opacity-95 transition-all flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <span className="animate-pulse">Publishing to Welele Africa...</span>
          ) : (
            <>
              <UploadCloud className="w-4 h-4" />
              <span>Publish Episode to Feed</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
