import React, { useState, useEffect, useRef } from 'react';
import Hls from 'hls.js';
import { useApp } from '../../context/AppContext';
import { useChat } from '../../context/ChatContext';
import { EpisodeDrawer } from './EpisodeDrawer';
import { FloatingReactions } from './FloatingReactions';
import { episodesApi, monetizationApi } from '../../services/api';
import confetti from 'canvas-confetti';
import {
  Heart,
  Bookmark,
  MessageCircle,
  Flame,
  List,
  Volume2,
  VolumeX,
  Lock,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  Play,
  Pause,
  Subtitles,
  Zap,
  Signal,
  CheckCircle2,
  SlidersHorizontal,
  ShieldCheck,
  Maximize,
  Minimize,
  ChevronRight,
} from 'lucide-react';
import { useContentProtection } from '../../hooks/useContentProtection';
import { mediaStore } from '../../services/mediaStore';

const IDENT_STORAGE_KEY = 'welele_last_brand_ident_time';
const IDENT_FREQ_MS = 15 * 60 * 1000; // 15-minute frequency cap across binge session
const BRAND_IDENT_URL = '/videos/welele_ident.mp4';

const checkShouldPlayIdent = () => {
  try {
    const lastPlayed = sessionStorage.getItem(IDENT_STORAGE_KEY);
    if (!lastPlayed) return true;
    const diff = Date.now() - parseInt(lastPlayed, 10);
    return isNaN(diff) || diff > IDENT_FREQ_MS;
  } catch {
    return true;
  }
};

interface VerticalPlayerProps {
  onBack?: () => void;
}

export const VerticalPlayer: React.FC<VerticalPlayerProps> = ({ onBack }) => {
  const {
    currentStory,
    currentEpisode,
    setCurrentEpisode,
    unlockedEpisodes,
    unlockEpisodeLocal,
    coins,
    selectedCarrier,
    quickAirtimeUnlock,
    likedStories,
    toggleLikeStory,
    bookmarks,
    toggleBookmark,
    setIsCoinModalOpen,
    setIsGiftModalOpen,
    userId,
    activeLanguage,
    setActiveLanguage,
  } = useApp();

  const { isSecurityAlertActive, securityMessage } = useContentProtection({
    enabled: true,
    watermarkText: `Welele DRM • ${userId || 'ZA_STREAM'}`,
  });

  const { triggerReaction, loadEpisodeComments, comments, addComment } = useChat();

  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const identVideoRef = useRef<HTMLVideoElement>(null);
  const identTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const nextVideoPreloadRef = useRef<HTMLVideoElement>(null);

  const [isIdentPlaying, setIsIdentPlaying] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(80);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [isChatDrawerOpen, setIsChatDrawerOpen] = useState<boolean>(false);
  const [newCommentText, setNewCommentText] = useState<string>('');
  const [showCliffhangerPrompt, setShowCliffhangerPrompt] = useState<boolean>(false);
  const [isUnlocking, setIsUnlocking] = useState<boolean>(false);
  const [isAirtimeUnlocking, setIsAirtimeUnlocking] = useState<boolean>(false);
  const [showSubtitleMenu, setShowSubtitleMenu] = useState<boolean>(false);
  const [showQualityMenu, setShowQualityMenu] = useState<boolean>(false);
  const [qualityMode, setQualityMode] = useState<'AUTO' | '1080P' | '720P' | '480P_DATA_SAVER'>('AUTO');
  const [activeSubtitleText, setActiveSubtitleText] = useState<string>('');
  const [airtimeToast, setAirtimeToast] = useState<string | null>(null);
  const [resolvedVideoUrl, setResolvedVideoUrl] = useState<string>(currentEpisode?.video_url || '');
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [storedDbKeys, setStoredDbKeys] = useState<string[]>([]);
  const [resolvedSourceKey, setResolvedSourceKey] = useState<string>('');
  const [showDebugHud, setShowDebugHud] = useState<boolean>(true);

  // Welele Immersive Viewing Law: 5-second auto-hide timer for unencumbered story watching
  const [showControls, setShowControls] = useState<boolean>(true);
  const [showPlayStateFlash, setShowPlayStateFlash] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(Boolean(document.fullscreenElement));
  const controlsTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flashTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleBrowserFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        if (document.documentElement.requestFullscreen) {
          await document.documentElement.requestFullscreen();
        }
      } else {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
        }
      }
    } catch (e) {
      console.warn('[VerticalPlayer] Fullscreen toggle error:', e);
    }
  };

  const episodeId = currentEpisode?.id;
  const isUnlocked =
    currentEpisode?.is_free || (episodeId ? unlockedEpisodes.has(episodeId) : true);

  // Active interaction gate: Keeps controls alive when user actively interacts with drawers/menus
  const isUserActivelyInteracting =
    isDrawerOpen ||
    isChatDrawerOpen ||
    showQualityMenu ||
    showSubtitleMenu ||
    showCliffhangerPrompt ||
    !isUnlocked ||
    !isPlaying;

  const resetControlsTimer = () => {
    if (controlsTimerRef.current) {
      clearTimeout(controlsTimerRef.current);
      controlsTimerRef.current = null;
    }
    setShowControls(true);

    if (!isUserActivelyInteracting) {
      controlsTimerRef.current = setTimeout(() => {
        setShowControls(false);
      }, 5000);
    }
  };

  // Sync controls visibility whenever interaction states change
  useEffect(() => {
    if (isUserActivelyInteracting) {
      if (controlsTimerRef.current) {
        clearTimeout(controlsTimerRef.current);
        controlsTimerRef.current = null;
      }
      setShowControls(true);
    } else {
      resetControlsTimer();
    }
    return () => {
      if (controlsTimerRef.current) clearTimeout(controlsTimerRef.current);
    };
  }, [isUserActivelyInteracting, episodeId]);

  const handleScreenTap = () => {
    if (!showControls) {
      // Tap reveals the controls without pausing playback
      resetControlsTimer();
    } else {
      // Controls already visible: toggle play/pause with visual flash indicator
      if (videoRef.current) {
        if (isPlaying) {
          videoRef.current.pause();
          setIsPlaying(false);
        } else {
          videoRef.current.play().catch(() => {});
          setIsPlaying(true);
        }
        setShowPlayStateFlash(true);
        if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
        flashTimerRef.current = setTimeout(() => {
          setShowPlayStateFlash(false);
        }, 700);
      }
      resetControlsTimer();
    }
  };

  // Canonical Video Stream Mounting Helper (HLS / Native / Direct MP4)
  const attachVideoStream = (videoEl: HTMLVideoElement, url: string, isHlsManifest: boolean) => {
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    if (isHlsManifest) {
      if (Hls.isSupported()) {
        const hls = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
        });
        hls.loadSource(url);
        hls.attachMedia(videoEl);
        hlsRef.current = hls;
      } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
        videoEl.src = url;
        videoEl.load();
      } else {
        videoEl.src = url;
        videoEl.load();
      }
    } else {
      videoEl.src = url;
      videoEl.load();
    }
  };

  // Cleanup HLS on unmount
  useEffect(() => {
    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, []);

  // Strict Separation: Canonical Production vs Local/Dev Media Resolution Pipeline
  useEffect(() => {
    if (!currentEpisode) return;
    let isCancelled = false;

    const resolveMedia = async () => {
      setMediaError(null);
      const sId = currentEpisode.series_id || currentStory?.id || '';
      const epId = currentEpisode.id;
      const epNum = currentEpisode.episode_number;

      // Authoritative Playback Invariant: In production, episodesApi.getStream() is authoritative.
      // blob: URLs must never hijack the production media decision.
      const isExplicitLocalDevDraft =
        Boolean(currentEpisode.id?.startsWith('ep_local_')) ||
        Boolean(currentEpisode.series_id?.startsWith('story_local_'));

      const resolutionMode: 'PRODUCTION_CANONICAL' | 'LOCAL_DEV' = isExplicitLocalDevDraft
        ? 'LOCAL_DEV'
        : 'PRODUCTION_CANONICAL';


      let finalUrl = '';
      let streamType = '';
      let mediaSource = '';
      let decisionReason = '';
      let mediaAssetId = currentEpisode.media_asset_id || `media_${epId}`;
      let storageKey = currentEpisode.storage_key || `masters/${sId}/${epId}.mp4`;
      let isHls = false;

      if (resolutionMode === 'LOCAL_DEV') {
        // ==========================================
        // 1. LOCAL / DEV RESOLUTION PATH
        // ==========================================
        try {
          const allKeys = await mediaStore.getAllStoredKeys();
          if (!isCancelled) setStoredDbKeys(allKeys);

          const cached = await mediaStore.findEpisodeMedia({
            seriesId: sId,
            seriesTitle: currentStory?.title,
            episodeNumber: epNum,
            episodeId: epId,
            title: currentEpisode.title,
            videoUrl: currentEpisode.video_url,
          });

          if (cached) {
            finalUrl = cached;
            streamType = 'LOCAL_INDEXED_DB_BLOB';
            mediaSource = 'mediaStore.findEpisodeMedia (LOCAL_DEV)';
            decisionReason = 'Resolved from local IndexedDB binary store for in-session creator draft / local dev';
          } else {
            setMediaError('Local/Dev asset not found in IndexedDB. Please re-attach the video master.');
            decisionReason = 'Local session blob expired with no matching binary in IndexedDB';
          }
        } catch (dbErr: any) {
          setMediaError(`IndexedDB query failed: ${dbErr?.message || dbErr}`);
          decisionReason = 'IndexedDB query threw an exception in local/dev mode';
        }
      } else {
        // ==========================================
        // 2. CANONICAL PRODUCTION RESOLUTION PATH
        // (Episode -> MediaAsset -> Storage -> AuthorisedStream)
        // ==========================================
        try {
          const streamData = await episodesApi.getStream(sId, epId, userId);
          if (streamData && streamData.stream) {
            const streamObj = streamData.stream;
            mediaAssetId = streamData.media_asset_id || mediaAssetId;
            storageKey = streamData.storage_key || storageKey;

            const primaryUrl = streamObj.primary_url;
            const hlsUrl = streamObj.hls_manifest;

            if (primaryUrl && !primaryUrl.includes('/videos/welele_placeholder.mp4')) {
              finalUrl = primaryUrl;
              isHls = false;
              streamType = 'CANONICAL_CDN_STREAM';
              mediaSource = 'episodesApi.getStream';
              decisionReason = streamData.is_unlocked
                ? 'Authorised canonical production stream resolved from backend'
                : 'Canonical production preview stream resolved from backend';
            } else if (hlsUrl && !hlsUrl.includes('/videos/welele_placeholder')) {
              finalUrl = hlsUrl;
              isHls = true;
              streamType = 'HLS_MANIFEST';
              mediaSource = 'episodesApi.getStream (HLS)';
              decisionReason = 'Authorised canonical HLS manifest resolved from backend';
            } else {
              finalUrl = primaryUrl || '/videos/welele_placeholder.mp4';
              streamType = 'DEFAULT_CATALOG_ASSET';
              mediaSource = 'episodesApi.getStream';
              decisionReason = 'Canonical backend stream returned default catalog asset';
            }
          } else {
            setMediaError('Production media resolution failed: Backend stream endpoint returned empty payload.');
            decisionReason = 'Backend stream endpoint returned no stream object';
          }
        } catch (apiErr: any) {
          console.error('[VerticalPlayer] Production stream contract error:', apiErr);
          setMediaError(`Production stream resolution failed: ${apiErr?.message || 'Server error'}. IndexedDB fallback rejected in production.`);
          decisionReason = 'Backend stream endpoint failed (HTTP error/network error). IndexedDB fallback blocked in production.';
        }
      }

      if (isCancelled) return;

      // Full Lineage Diagnostic Logging (Episode -> MediaAsset -> Storage -> Stream -> Video)
      console.log(
        `%c[VerticalPlayer:MediaDecision] ${currentEpisode.title} (Ep #${epNum})`,
        'background: #111; color: #00E676; font-weight: bold; padding: 2px 6px; border-radius: 4px;',
        {
          episodeId: epId,
          seriesId: sId,
          isUnlocked: Boolean(isUnlocked),
          returnedStreamUrl: finalUrl,
          mediaAssetId,
          storageKey,
          resolutionMode,
          streamType,
          mediaSource,
          decisionReason,
        }
      );

      setResolvedVideoUrl(finalUrl);
      setResolvedSourceKey(`${resolutionMode} • ${streamType}`);

      if (videoRef.current && finalUrl) {
        if (videoRef.current.src !== finalUrl && !videoRef.current.src.endsWith(finalUrl)) {
          attachVideoStream(videoRef.current, finalUrl, isHls);
          if (isPlaying && !isIdentPlaying) {
            videoRef.current.play().catch((err) => {
              console.warn('[VerticalPlayer] Autoplay error:', err);
            });
          }
        }
      }
    };

    resolveMedia();

    return () => {
      isCancelled = true;
    };
  }, [currentEpisode, currentStory, userId, isUnlocked, isPlaying, isIdentPlaying]);

  // Synchronize video element when resolvedVideoUrl updates
  useEffect(() => {
    if (videoRef.current && resolvedVideoUrl) {
      if (videoRef.current.src !== resolvedVideoUrl && !videoRef.current.src.endsWith(resolvedVideoUrl)) {
        attachVideoStream(videoRef.current, resolvedVideoUrl, resolvedVideoUrl.endsWith('.m3u8'));
        if (isPlaying && !isIdentPlaying) {
          videoRef.current.play().catch(() => {});
        }
      }
    }
  }, [resolvedVideoUrl, isPlaying, isIdentPlaying]);

  // Next episode calculation for chunked buffer preloading (Pillar 4 / Sec 4.2)
  const currentIndex = currentStory?.episodes.findIndex((e) => e.id === currentEpisode?.id) ?? -1;
  const nextEpisode = (currentStory && currentIndex >= 0 && currentIndex < currentStory.episodes.length - 1)
    ? currentStory.episodes[currentIndex + 1]
    : null;

  // Brand Ident completion handler & seamless handoff to episode video
  const handleIdentFinished = () => {
    if (identTimeoutRef.current) {
      clearTimeout(identTimeoutRef.current);
      identTimeoutRef.current = null;
    }
    setIsIdentPlaying(false);
    try {
      sessionStorage.setItem(IDENT_STORAGE_KEY, Date.now().toString());
    } catch (e) {
      console.warn('[VerticalPlayer] Ident storage write error:', e);
    }
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play().catch((err) => {
        console.warn('[VerticalPlayer] Autoplay episode transition error:', err);
      });
    }
    resetControlsTimer();
  };

  // Failsafe timer for Brand Ident (max ~5.8s)
  useEffect(() => {
    if (isIdentPlaying) {
      identTimeoutRef.current = setTimeout(() => {
        handleIdentFinished();
      }, 5800);
      return () => {
        if (identTimeoutRef.current) {
          clearTimeout(identTimeoutRef.current);
          identTimeoutRef.current = null;
        }
      };
    }
  }, [isIdentPlaying]);

  // Load comments & reset playback whenever episode changes
  useEffect(() => {
    if (episodeId) {
      loadEpisodeComments(episodeId);
      setProgress(0);
      setCurrentTime(0);
      setShowCliffhangerPrompt(false);
      setIsPlaying(true);

      const shouldPlayIdent = checkShouldPlayIdent();
      setIsIdentPlaying(shouldPlayIdent);

      if (videoRef.current) {
        videoRef.current.currentTime = 0;
        if (!shouldPlayIdent) {
          videoRef.current.play().catch(() => {});
        }
      }
    }
  }, [episodeId]);

  // Video time updates, adaptive quality, and cliffhanger trigger
  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const curr = videoRef.current.currentTime;
    const dur = videoRef.current.duration || duration;
    setCurrentTime(curr);
    setProgress((curr / dur) * 100);

    // Dynamic subtitle lines localized to South Africa & Pan-African languages
    if (curr < 6) {
      if (activeLanguage === 'isiZulu' || activeLanguage === 'Zulu') {
        setActiveSubtitleText('Wacabanga ukuthi imfihlo yangcwatshwa nesihlalo sobukhosi baseGoli...');
      } else if (activeLanguage === 'isiXhosa') {
        setActiveSubtitleText('Wayecinga ukuba imfihlelo yangcwatywa netrone yamandulo...');
      } else if (activeLanguage === 'Afrikaans') {
        setActiveSubtitleText('Hy het gedink die geheim is saam met die antieke troon begrawe...');
      } else if (activeLanguage === 'Sesotho') {
        setActiveSubtitleText('O ne a nahana hore lekunutu le patiloe le terone ea khale...');
      } else if (activeLanguage === 'Yoruba') {
        setActiveSubtitleText('O ro pe a sin asiri naa pelu ite atijo...');
      } else if (activeLanguage === 'Swahili') {
        setActiveSubtitleText('Alidhani siri hiyo ilizikwa na kiti cha kale...');
      } else {
        setActiveSubtitleText('He thought the secret was buried with the ancient throne...');
      }
    } else if (curr < 14) {
      if (activeLanguage === 'isiZulu' || activeLanguage === 'Zulu') {
        setActiveSubtitleText('Kwaze kwaba yilapho engena ngamasango asebukhosini egqoke itshe legolide...');
      } else if (activeLanguage === 'isiXhosa') {
        setActiveSubtitleText('Wada wangena emasangweni obukhosi enxibe ilitye legolide elingcwele...');
      } else if (activeLanguage === 'Afrikaans') {
        setActiveSubtitleText('Totdat sy deur die koninklike hekke gestap het met die heilige goudsteen.');
      } else if (activeLanguage === 'Sesotho') {
        setActiveSubtitleText('Ho fihlela a kena ka liheke tsa borena a apere lejoe le halalelang.');
      } else if (activeLanguage === 'Yoruba') {
        setActiveSubtitleText('Titi o fi wole gba awon enu-bode oba pelu okuta iyebiye...');
      } else if (activeLanguage === 'Swahili') {
        setActiveSubtitleText('Hadi alipoingia kwenye malango ya kifalme na jiwe takatifu...');
      } else {
        setActiveSubtitleText('Until she walked through the royal gates wearing the sacred amber stone.');
      }
    } else if (curr > (currentEpisode?.cliffhanger_time || 65) && !showCliffhangerPrompt) {
      setShowCliffhangerPrompt(true);
    }
  };

  const handleNextEpisode = () => {
    if (!currentStory || !currentEpisode) return;
    if (currentIndex < currentStory.episodes.length - 1) {
      setCurrentEpisode(currentStory.episodes[currentIndex + 1]);
    }
  };

  const handlePrevEpisode = () => {
    if (!currentStory || !currentEpisode) return;
    if (currentIndex > 0) {
      setCurrentEpisode(currentStory.episodes[currentIndex - 1]);
    }
  };

  const handleUnlockWithCoins = async () => {
    if (!currentStory || !currentEpisode) return;
    const cost = currentEpisode.coin_price || 5;

    if (coins < cost) {
      setIsCoinModalOpen(true);
      return;
    }

    setIsUnlocking(true);
    try {
      // 1. Call canonical unlock endpoint with double-entry ledger verification
      await episodesApi.unlock(currentStory.id, currentEpisode.id, userId, 'COINS');
      unlockEpisodeLocal(currentEpisode.id, cost);

      confetti({
        particleCount: 60,
        spread: 60,
        origin: { y: 0.5 },
        colors: ['#FF9D00', '#FFC400', '#39D353'],
      });

      // 2. Immediately request the authoritative stream from canonical endpoint
      try {
        const streamData = await episodesApi.getStream(currentStory.id, currentEpisode.id, userId);
        if (streamData && streamData.stream) {
          const canonicalUrl = streamData.stream.primary_url || streamData.stream.hls_manifest;
          const mediaAssetId = streamData.media_asset_id || `media_${currentEpisode.id}`;
          const storageKey = streamData.storage_key || `masters/${currentStory.id}/${currentEpisode.id}.mp4`;
          const isHls = Boolean(canonicalUrl?.endsWith('.m3u8'));

          if (canonicalUrl && !canonicalUrl.includes('/videos/welele_placeholder.mp4')) {
            console.log(
              `%c[VerticalPlayer:MediaDecision:PostUnlock] ${currentEpisode.title} (Ep #${currentEpisode.episode_number})`,
              'background: #00E676; color: #000; font-weight: bold; padding: 2px 6px;',
              {
                episodeId: currentEpisode.id,
                seriesId: currentStory.id,
                isUnlocked: true,
                returnedStreamUrl: canonicalUrl,
                mediaAssetId,
                storageKey,
                resolutionMode: 'PRODUCTION_CANONICAL',
                streamType: isHls ? 'HLS_MANIFEST' : 'CANONICAL_CDN_STREAM',
                mediaSource: 'episodesApi.getStream (POST-UNLOCK)',
                decisionReason: 'Immediately resolved from canonical backend stream endpoint after successful coin unlock',
              }
            );
            setResolvedVideoUrl(canonicalUrl);
            setResolvedSourceKey(`PRODUCTION_CANONICAL • ${isHls ? 'HLS_MANIFEST' : 'CANONICAL_CDN_STREAM'}`);
            if (videoRef.current) {
              attachVideoStream(videoRef.current, canonicalUrl, isHls);
              if (isPlaying && !isIdentPlaying) {
                videoRef.current.play().catch(() => {});
              }
            }
          }
        }
      } catch (streamErr) {
        console.warn('[VerticalPlayer] Error retrieving stream post-coin-unlock:', streamErr);
      }
    } catch (err) {
      console.error('Episode unlock failed:', err);
      // Fallback
      await monetizationApi.unlockEpisode({
        user_id: userId,
        episode_id: currentEpisode.id,
        series_id: currentStory.id,
        coins: cost,
      });
      unlockEpisodeLocal(currentEpisode.id, cost);
    } finally {
      setIsUnlocking(false);
    }
  };

  // South African 1-Tap Direct Airtime Unlock
  const handleQuickAirtimeUnlock = async () => {
    if (!currentStory || !currentEpisode) return;
    setIsAirtimeUnlocking(true);

    try {
      // 1. Deduct airtime and establish entitlement
      await quickAirtimeUnlock(currentEpisode.id, currentStory.id, 3.0, 5);

      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.5 },
        colors: ['#00E676', '#FFD600', '#FF3D00'],
      });

      setAirtimeToast(`✨ R3.00 deducted from ${selectedCarrier.replace('_', ' ').toUpperCase()} Airtime. Unlocked!`);
      setTimeout(() => setAirtimeToast(null), 4000);

      // 2. Immediately request the authoritative stream from canonical endpoint
      try {
        const streamData = await episodesApi.getStream(currentStory.id, currentEpisode.id, userId);
        if (streamData && streamData.stream) {
          const canonicalUrl = streamData.stream.primary_url || streamData.stream.hls_manifest;
          const mediaAssetId = streamData.media_asset_id || `media_${currentEpisode.id}`;
          const storageKey = streamData.storage_key || `masters/${currentStory.id}/${currentEpisode.id}.mp4`;
          const isHls = Boolean(canonicalUrl?.endsWith('.m3u8'));

          if (canonicalUrl && !canonicalUrl.includes('/videos/welele_placeholder.mp4')) {
            console.log(
              `%c[VerticalPlayer:MediaDecision:PostUnlock] ${currentEpisode.title} (Ep #${currentEpisode.episode_number})`,
              'background: #00E676; color: #000; font-weight: bold; padding: 2px 6px;',
              {
                episodeId: currentEpisode.id,
                seriesId: currentStory.id,
                isUnlocked: true,
                returnedStreamUrl: canonicalUrl,
                mediaAssetId,
                storageKey,
                resolutionMode: 'PRODUCTION_CANONICAL',
                streamType: isHls ? 'HLS_MANIFEST' : 'CANONICAL_CDN_STREAM',
                mediaSource: 'episodesApi.getStream (POST-AIRTIME-UNLOCK)',
                decisionReason: 'Immediately resolved from canonical backend stream endpoint after successful airtime unlock',
              }
            );
            setResolvedVideoUrl(canonicalUrl);
            setResolvedSourceKey(`PRODUCTION_CANONICAL • ${isHls ? 'HLS_MANIFEST' : 'CANONICAL_CDN_STREAM'}`);
            if (videoRef.current) {
              attachVideoStream(videoRef.current, canonicalUrl, isHls);
              if (isPlaying && !isIdentPlaying) {
                videoRef.current.play().catch(() => {});
              }
            }
          }
        }
      } catch (streamErr) {
        console.warn('[VerticalPlayer] Error retrieving stream post-airtime-unlock:', streamErr);
      }
    } catch (err) {
      console.error('Quick airtime unlock failed:', err);
    } finally {
      setIsAirtimeUnlocking(false);
    }
  };

  const handleSendComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCommentText.trim() || !currentEpisode) return;
    await addComment(
      currentEpisode.id,
      newCommentText,
      'Sipho Dlamini',
      'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=100&q=80'
    );
    setNewCommentText('');
  };

  if (!currentStory || !currentEpisode) {
    return (
      <div className="flex items-center justify-center h-[70vh] text-welele-muted">
        Loading story stream...
      </div>
    );
  }

  const isLiked = likedStories.has(currentStory.id);
  const isBookmarked = bookmarks.has(currentStory.id);

  const saLanguages = [
    'isiZulu',
    'isiXhosa',
    'Afrikaans',
    'Sesotho',
    'English',
    'Swahili',
    'Yoruba',
    'Pidgin',
    'French',
  ];

  return (
    <div
      onMouseMove={resetControlsTimer}
      onTouchStart={resetControlsTimer}
      className="relative w-full max-w-sm md:max-w-md mx-auto aspect-[9/16] max-h-[82vh] sm:max-h-[86vh] bg-black rounded-[7px] overflow-hidden shadow-2xl border border-white/10 select-none group"
    >
      {/* Background Preload of next episode for zero-latency auto-advancement (Pillar 4 / Sec 4.2) */}
      {nextEpisode && (
        <video
          ref={nextVideoPreloadRef}
          src={nextEpisode.video_url}
          preload="auto"
          className="hidden"
          muted
        />
      )}

      {/* Floating Reaction Burst particles */}
      <FloatingReactions />

      {/* Airtime Deduction Toast */}
      {airtimeToast && (
        <div className="absolute top-16 left-4 right-4 z-40 bg-emerald-950/90 border border-emerald-500/50 p-2.5 rounded-[7px] shadow-xl backdrop-blur-md flex items-center gap-2 text-emerald-200 text-xs font-semibold animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{airtimeToast}</span>
        </div>
      )}

      {/* Content Protection Padlock Indicator */}
      {isSecurityAlertActive && (
        <div className="absolute top-5 left-1/2 -translate-x-1/2 z-50 p-3.5 rounded-full bg-black/85 backdrop-blur-md border border-white/20 shadow-2xl text-amber-400 flex items-center justify-center animate-fade-in pointer-events-none transition-all">
          <Lock className="w-6 h-6 stroke-[2.2]" />
        </div>
      )}

      {/* Video Element & DRM Transparent Protective Shield */}
      {isUnlocked ? (
        <div className="relative w-full h-full bg-black overflow-hidden">
          {/* Episode Video (Plays actual resolved URL directly) */}
          <video
            ref={videoRef}
            src={resolvedVideoUrl}
            className="w-full h-full object-cover"
            playsInline
            autoPlay
            loop
            muted={isMuted}
            preload="auto"
            controlsList="nodownload noplaybackrate noremoteplayback"
            disablePictureInPicture
            disableRemotePlayback
            onContextMenu={(e) => e.preventDefault()}
            onDragStart={(e) => e.preventDefault()}
            onTimeUpdate={handleTimeUpdate}
            onPlay={() => setMediaError(null)}
            onError={(e) => {
              const err = e.currentTarget.error;
              const errMsg = err
                ? `HTML5 Media Error Code ${err.code}: ${err.message || 'Format unsupported or stream unavailable'}`
                : 'Playback error';
              console.error('[VerticalPlayer] Native Video Error:', errMsg, 'Src:', e.currentTarget.src);
              setMediaError(errMsg);
            }}
          />

          {/* Real-time Diagnostics HUD */}
          {(mediaError || !resolvedVideoUrl) && (
            <div className="absolute inset-0 z-40 bg-black/90 p-6 flex flex-col items-center justify-center text-center space-y-4 animate-fade-in text-white">
              <div className="w-12 h-12 rounded-full bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400">
                <SlidersHorizontal className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-sm font-black uppercase text-red-400 font-cinematic">
                  Playback Diagnostics
                </h3>
                <p className="text-xs text-welele-muted mt-1 max-w-sm">
                  {mediaError || 'No video binary found in IndexedDB for this episode.'}
                </p>
              </div>

              <div className="p-3 bg-white/5 rounded-[7px] border border-white/10 text-[10px] font-mono text-left max-w-xs w-full space-y-1 text-white/80">
                <div><b>Episode:</b> {currentEpisode?.title} (EP {currentEpisode?.episode_number})</div>
                <div><b>Series:</b> {currentEpisode?.series_id}</div>
                <div className="break-all"><b>Source:</b> {resolvedVideoUrl || 'Empty'}</div>
                <div className="break-all"><b>IndexedDB Keys:</b> {storedDbKeys.length > 0 ? storedDbKeys.join(', ') : 'No keys found'}</div>
              </div>

              {/* Direct Attach Button */}
              <label className="cursor-pointer px-4 py-2.5 rounded-[7px] bg-gradient-welele text-white text-xs font-bold shadow-xl shadow-orange-500/20 flex items-center gap-2 hover:opacity-95 transition-all">
                <Zap className="w-4 h-4" />
                <span>Select & Play Video File Now</span>
                <input
                  type="file"
                  accept="video/mp4,video/quicktime,video/webm"
                  className="hidden"
                  onChange={async (e) => {
                    if (e.target.files && e.target.files[0] && currentEpisode) {
                      const file = e.target.files[0];
                      const newUrl = await mediaStore.saveEpisodeMedia({
                        seriesId: currentEpisode.series_id || currentStory?.id,
                        seriesTitle: currentStory?.title,
                        episodeNumber: currentEpisode.episode_number,
                        episodeId: currentEpisode.id,
                        title: currentEpisode.title,
                      }, file);
                      setResolvedVideoUrl(newUrl);
                      setMediaError(null);
                      const updatedKeys = await mediaStore.getAllStoredKeys();
                      setStoredDbKeys(updatedKeys);
                      if (videoRef.current) {
                        videoRef.current.src = newUrl;
                        videoRef.current.load();
                        videoRef.current.play().catch(() => {});
                      }
                    }
                  }}
                />
              </label>
            </div>
          )}

          {/* Transparent DRM Gesture Shield: Tap to reveal controls / toggle play state */}
          {!isIdentPlaying && (
            <div
              className="absolute inset-0 z-10 cursor-pointer"
              onContextMenu={(e) => e.preventDefault()}
              onDragStart={(e) => e.preventDefault()}
              onClick={handleScreenTap}
            />
          )}

          {/* Brief Play / Pause State Flash Indicator */}
          {!isIdentPlaying && showPlayStateFlash && (
            <div className="absolute inset-0 flex items-center justify-center z-20 pointer-events-none animate-fade-in">
              <div className="w-14 h-14 rounded-full bg-black/75 backdrop-blur-md border border-white/20 flex items-center justify-center text-white shadow-2xl">
                {isPlaying ? <Play className="w-7 h-7 fill-current ml-0.5" /> : <Pause className="w-7 h-7 fill-current" />}
              </div>
            </div>
          )}

          {/* Dynamic Floating Forensic DRM Watermark */}
          {!isIdentPlaying && (
            <div className="absolute z-20 pointer-events-none select-none text-[10px] font-mono tracking-widest text-white/30 px-2 py-0.5 rounded-[7px] bg-black/20 backdrop-blur-[1px] animate-drm-watermark border border-white/5">
              🔒 WELELE DRM • {userId || 'USER_ZA'} • {currentEpisode.id}
            </div>
          )}

          {/* Persistent DRM Protection Badge */}
          {!isIdentPlaying && (
            <div
              className={`absolute top-3 left-3 z-20 flex items-center gap-1 text-[9px] font-mono text-white/40 pointer-events-none bg-black/40 backdrop-blur-sm px-2 py-0.5 rounded-[7px] transition-opacity duration-500 ${
                showControls ? 'opacity-100' : 'opacity-0'
              }`}
            >
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              <span>DRM ENCRYPTED</span>
            </div>
          )}
        </div>
      ) : (
        /* Locked Episode Paywall Overlay with South African Airtime Customisation */
        <div className="relative w-full h-full">
          <img
            src={currentEpisode.thumbnail_url}
            alt={currentEpisode.title}
            className="w-full h-full object-cover filter blur-md brightness-50"
          />
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center bg-black/65 backdrop-blur-md z-30">
            <div className="w-16 h-16 rounded-[7px] bg-gradient-welele flex items-center justify-center text-white shadow-xl shadow-orange-500/30 mb-3 animate-bounce">
              <Lock className="w-8 h-8" />
            </div>
            <span className="text-[11px] font-extrabold text-welele-orange tracking-wider uppercase mb-1">
              Cliffhanger Locked 🔒
            </span>
            <h3 className="text-xl font-black text-white font-cinematic mb-1">
              {currentEpisode.title}
            </h3>
            <p className="text-xs text-welele-muted max-w-xs mb-5">
              Unlock the next dramatic turn of <b>{currentStory.title}</b>!
            </p>

            {/* South African 1-Tap Airtime Unlock Button (Zero Coins Needed) */}
            <div className="w-full max-w-xs space-y-2.5">
              <button
                onClick={handleQuickAirtimeUnlock}
                disabled={isAirtimeUnlocking}
                className="w-full py-3.5 rounded-[7px] font-black text-xs bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600 text-white shadow-xl shadow-emerald-500/30 hover:opacity-95 transition-all flex items-center justify-center gap-2 border border-emerald-400/40"
              >
                {isAirtimeUnlocking ? (
                  <span className="animate-pulse">Authorizing SIM Airtime...</span>
                ) : (
                  <>
                    <Zap className="w-4 h-4 fill-current text-yellow-300" />
                    <span>⚡ 1-Tap Unlock with Airtime (R3.00)</span>
                  </>
                )}
              </button>

              {/* Standard Coin Unlock Button */}
              <button
                onClick={handleUnlockWithCoins}
                disabled={isUnlocking}
                className="w-full py-2.5 rounded-[7px] font-bold text-xs bg-welele-surface-2 hover:bg-white/10 text-white border border-white/10 transition-all flex items-center justify-center gap-2"
              >
                {isUnlocking ? (
                  <span className="animate-pulse">Unlocking Episode...</span>
                ) : (
                  <>
                    <span>🪙 Unlock for {currentEpisode.coin_price || 5} Coins</span>
                    <span className="text-[11px] text-welele-muted">(Bal: {coins})</span>
                  </>
                )}
              </button>
            </div>

            {/* Airtime SIM & Coin Topup Link */}
            <div className="mt-4 flex items-center justify-center gap-2">
              <button
                onClick={() => setIsCoinModalOpen(true)}
                className="text-xs font-bold text-welele-gold hover:underline flex items-center gap-1"
              >
                <Signal className="w-3.5 h-3.5 text-emerald-400" />
                <span>Manage Airtime Passes & Coins (Vodacom/MTN)</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Top Gradient Overlay & Controls (Immersive 5s Auto-Fade) */}
      {!isIdentPlaying && (
        <div
          className={`absolute top-0 left-0 right-0 p-3 sm:p-4 bg-gradient-to-b from-black/90 via-black/40 to-transparent z-20 flex items-center justify-between transition-all duration-500 ease-in-out ${
            showControls
              ? 'opacity-100 pointer-events-auto translate-y-0'
              : 'opacity-0 pointer-events-none -translate-y-2'
          }`}
        >
          <div className="flex items-center gap-2 pointer-events-auto min-w-0 pr-2">
            {onBack && (
              <button
                onClick={onBack}
                className="w-7 h-7 rounded-[7px] bg-black/60 hover:bg-black/90 backdrop-blur-md flex items-center justify-center text-white border border-white/10 transition-transform active:scale-95 shrink-0"
                title="Back to Feed"
                aria-label="Back to Feed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            )}
            <img
              src={currentStory.creator_avatar}
              alt={currentStory.creator_name}
              className="w-7 h-7 sm:w-8 sm:h-8 rounded-full border border-welele-orange object-cover shrink-0"
            />
            <div className="min-w-0">
              <h4 className="text-xs font-bold text-white leading-tight flex items-center gap-1.5 truncate">
                <span className="truncate">{currentStory.title}</span>
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-welele-orange/20 text-welele-orange border border-welele-orange/30 shrink-0">
                  EP {currentEpisode.episode_number}/{currentStory.episodes?.length || currentStory.total_episodes || 1}
                </span>
              </h4>
              <p className="text-[10px] text-welele-muted truncate max-w-[130px] sm:max-w-[150px]">
                by {currentStory.creator_name}
              </p>
            </div>
          </div>

          {/* Top Controls: Adaptive Bitrate, Subtitles, Sound */}
          <div className="flex items-center gap-1.5 sm:gap-2 pointer-events-auto shrink-0">
            {/* Adaptive Bitrate Selector (Pillar 4 / Sec 4.2) */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowQualityMenu(!showQualityMenu);
                  setShowSubtitleMenu(false);
                }}
                className="px-2 py-1 rounded-[7px] bg-black/60 backdrop-blur-md flex items-center gap-1 text-[10px] font-bold text-white/90 hover:text-white border border-white/10"
                title="Adaptive Bitrate Quality"
              >
                <SlidersHorizontal className="w-3 h-3 text-emerald-400" />
                <span>{qualityMode === '480P_DATA_SAVER' ? 'Data-Saver' : qualityMode}</span>
              </button>

              {showQualityMenu && (
                <div className="absolute right-0 top-9 w-40 bg-welele-surface border border-white/10 rounded-[7px] p-1.5 shadow-2xl z-40 text-xs">
                  <div className="text-[9px] font-extrabold text-welele-muted px-2 py-1 uppercase tracking-wider">
                    Adaptive Streaming
                  </div>
                  {[
                    { id: 'AUTO', label: 'Auto (Network Adaptive)' },
                    { id: '1080P', label: '1080p HD (Wi-Fi/5G)' },
                    { id: '720P', label: '720p Mobile Standard' },
                    { id: '480P_DATA_SAVER', label: '480p Data-Saver (3G)' },
                  ].map((q) => (
                    <button
                      key={q.id}
                      onClick={() => {
                        setQualityMode(q.id as any);
                        setShowQualityMenu(false);
                      }}
                      className={`w-full text-left px-2.5 py-1.5 rounded-[7px] text-[11px] font-semibold transition-colors ${
                        qualityMode === q.id
                          ? 'bg-emerald-500 text-black font-bold'
                          : 'text-white hover:bg-white/5'
                      }`}
                    >
                      {q.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Subtitle Selector */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowSubtitleMenu(!showSubtitleMenu);
                  setShowQualityMenu(false);
                }}
                className="w-7 h-7 rounded-[7px] bg-black/60 backdrop-blur-md flex items-center justify-center text-white/80 hover:text-white border border-white/10"
                title="Subtitles & Language"
              >
                <Subtitles className="w-3.5 h-3.5 text-welele-orange" />
              </button>

              {showSubtitleMenu && (
                <div className="absolute right-0 top-9 w-36 bg-welele-surface border border-white/10 rounded-[7px] p-1.5 shadow-2xl z-40 text-xs">
                  <div className="text-[9px] font-extrabold text-welele-muted px-2 py-1 uppercase tracking-wider">
                    Mzansi Subtitles
                  </div>
                  {saLanguages.map((lang) => (
                    <button
                      key={lang}
                      onClick={() => {
                        setActiveLanguage(lang);
                        setShowSubtitleMenu(false);
                      }}
                      className={`w-full text-left px-2.5 py-1.5 rounded-[7px] text-[11px] font-semibold transition-colors ${
                        activeLanguage === lang
                          ? 'bg-welele-orange text-black font-bold'
                          : 'text-white hover:bg-white/5'
                      }`}
                    >
                      {lang}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Mute Toggle */}
            <button
              onClick={() => setIsMuted(!isMuted)}
              className="w-7 h-7 rounded-[7px] bg-black/60 backdrop-blur-md flex items-center justify-center text-white/80 hover:text-white border border-white/10 cursor-pointer"
              title={isMuted ? "Unmute Audio" : "Mute Audio"}
            >
              {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
            </button>

            {/* Immersive Browser Fullscreen Toggle (Hides Address Bar & Chrome on Mobile) */}
            <button
              onClick={toggleBrowserFullscreen}
              className="w-7 h-7 rounded-[7px] bg-black/60 backdrop-blur-md flex items-center justify-center text-white/80 hover:text-white border border-white/10 cursor-pointer"
              title={isFullscreen ? "Exit Fullscreen" : "Immersive Fullscreen (Hide Browser Bar)"}
            >
              {isFullscreen ? <Minimize className="w-3.5 h-3.5 text-welele-orange" /> : <Maximize className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      )}

      {/* Subtitles Overlay (Cinematic Bottom-Center with Comfortable Padding above Progress Bar) */}
      {!isIdentPlaying && isUnlocked && activeSubtitleText && (
        <div className="absolute bottom-5 left-4 right-4 z-20 pointer-events-none flex justify-center text-center">
          <span className="inline-block max-w-[92%] px-3.5 py-1.5 rounded-[7px] bg-black/85 backdrop-blur-md text-white text-xs font-medium leading-relaxed border border-white/10 shadow-2xl drop-shadow-md">
            {activeSubtitleText}
          </span>
        </div>
      )}

      {/* Right Sidebar Floating Interaction Buttons (Immersive 5s Auto-Fade) */}
      {!isIdentPlaying && (
        <div
          className={`absolute right-3 bottom-16 z-20 flex flex-col items-center gap-3.5 pointer-events-auto transition-all duration-500 ease-in-out ${
            showControls
              ? 'opacity-100 pointer-events-auto translate-x-0'
              : 'opacity-0 pointer-events-none translate-x-3'
          }`}
        >
          {/* Like Button */}
          <button
            onClick={() => toggleLikeStory(currentStory.id)}
            className="flex flex-col items-center group cursor-pointer"
          >
            <div
              className={`w-10 h-10 rounded-circle flex items-center justify-center backdrop-blur-md border transition-all ${
                isLiked
                  ? 'bg-welele-red/30 border-welele-red text-welele-red scale-110'
                  : 'bg-black/50 border-white/10 text-white hover:bg-black/80'
              }`}
            >
              <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
            </div>
            <span className="text-[10px] font-bold text-white mt-1 shadow-sm">
              {((currentStory?.total_likes || 0) + (isLiked ? 1 : 0)).toLocaleString()}
            </span>
          </button>

          {/* Welele Chat Comments */}
          <button
            onClick={() => setIsChatDrawerOpen(true)}
            className="flex flex-col items-center group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-circle bg-black/50 hover:bg-black/80 border border-white/10 flex items-center justify-center text-white backdrop-blur-md transition-transform group-hover:scale-105">
              <MessageCircle className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-bold text-white mt-1">
              {comments.length}
            </span>
          </button>

          {/* Gift Creator Button */}
          <button
            onClick={() => setIsGiftModalOpen(true)}
            className="flex flex-col items-center group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-circle bg-gradient-welele flex items-center justify-center text-white shadow-lg shadow-orange-500/30 transition-transform group-hover:scale-110">
              <Flame className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-bold text-welele-orange mt-1">Gift</span>
          </button>

          {/* Bookmark */}
          <button
            onClick={() => toggleBookmark(currentStory.id)}
            className="flex flex-col items-center group cursor-pointer"
          >
            <div
              className={`w-10 h-10 rounded-circle flex items-center justify-center backdrop-blur-md border transition-all ${
                isBookmarked
                  ? 'bg-welele-gold/30 border-welele-gold text-welele-gold'
                  : 'bg-black/50 border-white/10 text-white hover:bg-black/80'
              }`}
            >
              <Bookmark className={`w-5 h-5 ${isBookmarked ? 'fill-current' : ''}`} />
            </div>
            <span className="text-[10px] font-bold text-white mt-1">Save</span>
          </button>

          {/* Episodes Drawer Toggle */}
          <button
            onClick={() => setIsDrawerOpen(true)}
            className="flex flex-col items-center group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-circle bg-black/50 hover:bg-black/80 border border-white/10 flex items-center justify-center text-white backdrop-blur-md transition-transform group-hover:scale-105">
              <List className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-bold text-white mt-1">Episodes</span>
          </button>
        </div>
      )}

      {/* Floating Reaction Quick Bar (Immersive 5s Auto-Fade) */}
      {!isIdentPlaying && (
        <div
          className={`absolute left-4 bottom-10 z-20 flex items-center gap-1.5 bg-black/60 backdrop-blur-md p-1.5 rounded-[7px] border border-white/10 pointer-events-auto transition-all duration-500 ease-in-out ${
            showControls
              ? 'opacity-100 pointer-events-auto translate-y-0'
              : 'opacity-0 pointer-events-none translate-y-3'
          }`}
        >
          {['🔥', '👑', '😱', '👏', '⚡'].map((emoji) => (
            <button
              key={emoji}
              onClick={() => triggerReaction(currentEpisode.id, emoji)}
              className="w-7 h-7 rounded-[7px] hover:bg-white/20 flex items-center justify-center text-base transition-transform active:scale-130 cursor-pointer"
            >
              {emoji}
            </button>
          ))}
        </div>
      )}

      {/* Up/Down Episode Switchers (Immersive 5s Auto-Fade) */}
      {!isIdentPlaying && (
        <div
          className={`absolute right-3 top-18 z-20 flex flex-col gap-2 pointer-events-auto transition-all duration-500 ease-in-out ${
            showControls
              ? 'opacity-100 pointer-events-auto translate-x-0'
              : 'opacity-0 pointer-events-none translate-x-3'
          }`}
        >
          <button
            onClick={handlePrevEpisode}
            aria-label="Previous Episode"
            className="w-7 h-7 rounded-[7px] bg-black/60 backdrop-blur-md border border-white/10 flex items-center justify-center text-white/80 hover:text-white cursor-pointer"
          >
            <ChevronUp className="w-4 h-4" />
          </button>
          <button
            onClick={handleNextEpisode}
            aria-label="Next Episode"
            className="w-7 h-7 rounded-[7px] bg-black/60 backdrop-blur-md border border-white/10 flex items-center justify-center text-white/80 hover:text-white cursor-pointer"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Subtle Bottom Playback Progress Bar (Subtle & Restrained) */}
      {!isIdentPlaying && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/15 z-30 pointer-events-none">
          <div
            className="h-full bg-gradient-welele transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Episode Drawer */}
      <EpisodeDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        story={currentStory}
        currentEpisode={currentEpisode}
        onSelectEpisode={(ep) => setCurrentEpisode(ep)}
      />

      {/* Chat Drawer */}
      {isChatDrawerOpen && (
        <div className="absolute inset-0 z-40 bg-black/85 backdrop-blur-md p-4 flex flex-col animate-fade-in">
          <div className="flex items-center justify-between pb-2 border-b border-white/10">
            <h4 className="text-sm font-bold text-white flex items-center gap-1.5">
              <MessageCircle className="w-4 h-4 text-welele-orange" />
              Story Chat (EP {currentEpisode.episode_number})
            </h4>
            <button
              onClick={() => setIsChatDrawerOpen(false)}
              className="text-xs text-welele-muted hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2.5 my-3 pr-1 text-xs">
            {comments.map((c) => (
              <div key={c.id} className="p-2 rounded-[7px] bg-welele-surface-2 border border-white/5">
                <div className="flex items-center gap-2 mb-1">
                  <img
                    src={c.avatar}
                    alt={c.user_name}
                    className="w-5 h-5 rounded-circle object-cover"
                  />
                  <span className="font-bold text-welele-orange text-[11px]">{c.user_name}</span>
                  <span className="text-[10px] text-welele-muted ml-auto">{c.time_ago}</span>
                </div>
                <p className="text-white/90 text-[11px]">{c.text}</p>
              </div>
            ))}
          </div>

          <form onSubmit={handleSendComment} className="flex gap-2">
            <input
              type="text"
              value={newCommentText}
              onChange={(e) => setNewCommentText(e.target.value)}
              placeholder="Drop your reaction to this cliffhanger..."
              className="flex-1 bg-welele-surface-2 px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-welele-orange"
            />
            <button
              type="submit"
              className="px-4 py-2 rounded-[7px] bg-welele-orange font-bold text-xs text-black"
            >
              Post
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
