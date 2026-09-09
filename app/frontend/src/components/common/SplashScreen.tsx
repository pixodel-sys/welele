import React, { useState, useEffect } from 'react';
import { WeleleLogo } from './WeleleLogo';
import { Sparkles, Heart, Play, Users } from 'lucide-react';

interface SplashScreenProps {
  onComplete: () => void;
  durationMs?: number;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete, durationMs = 2800 }) => {
  const [progress, setProgress] = useState<number>(0);
  const [isFadingOut, setIsFadingOut] = useState<boolean>(false);
  const [hasPlayedSound, setHasPlayedSound] = useState<boolean>(false);

  // Play warm storytelling acoustic harmonic chime
  const playSonicChime = () => {
    if (hasPlayedSound) return;
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(329.63, audioCtx.currentTime); // E4
      osc.frequency.exponentialRampToValueAtTime(659.25, audioCtx.currentTime + 0.35); // E5

      gain.gain.setValueAtTime(0.01, audioCtx.currentTime);
      gain.gain.linearRampToValueAtTime(0.25, audioCtx.currentTime + 0.2);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 1.4);

      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 1.5);
      setHasPlayedSound(true);
    } catch (e) {
      // Ignore if user hasn't interacted
    }
  };

  useEffect(() => {
    playSonicChime();

    const interval = 25;
    const step = 100 / (durationMs / interval);

    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + step;
        if (next >= 100) {
          clearInterval(timer);
          setTimeout(() => {
            setIsFadingOut(true);
            setTimeout(() => {
              onComplete();
            }, 650);
          }, 250);
          return 100;
        }
        return next;
      });
    }, interval);

    return () => clearInterval(timer);
  }, [durationMs, onComplete]);

  return (
    <div
      onClick={playSonicChime}
      className={`fixed inset-0 z-50 bg-[#0B0C0E] flex flex-col items-center justify-between p-6 select-none transition-all duration-700 overflow-hidden ${
        isFadingOut ? 'opacity-0 scale-105 pointer-events-none' : 'opacity-100 scale-100'
      }`}
    >
      {/* Modern Cinematic Ambient Gradient Backdrop (No logo duplication) */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        {/* Deep Multi-Tone Dark Base */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#0F1116] via-[#090A0D] to-[#050608]" />

        {/* Central Ambient Sunset Glow Behind Logo */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[580px] h-[580px] bg-gradient-to-tr from-[#FFA000]/15 via-[#FF6500]/18 to-[#D8005A]/12 rounded-full blur-[110px] animate-pulse-slow" />

        {/* Top-Right Warm Ember Atmosphere */}
        <div className="absolute -top-24 -right-24 w-[400px] h-[400px] bg-gradient-to-br from-[#FF6500]/10 via-[#FFA000]/06 to-transparent rounded-full blur-[100px]" />

        {/* Bottom-Left Deep Magenta Accent */}
        <div className="absolute -bottom-24 -left-24 w-[420px] h-[420px] bg-gradient-to-tr from-[#D8005A]/08 via-[#2A1020]/20 to-transparent rounded-full blur-[120px]" />

        {/* Subtle Cinematic Vignette */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,rgba(5,6,8,0.75)_100%)]" />
      </div>

      {/* Top Header / Skip Button */}
      <div className="w-full flex items-center justify-between z-10 max-w-lg mx-auto px-1">
        <span className="text-[9px] sm:text-[10px] font-extrabold tracking-widest text-[#FFA000] uppercase flex items-center gap-1.5">
          <Sparkles className="w-3 h-3 text-[#FFA000]" />
          <span>AFRICAN STORYTELLING PLATFORM</span>
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsFadingOut(true);
            setTimeout(onComplete, 300);
          }}
          className="text-xs font-bold text-[#FFF8F0] hover:text-white px-3 sm:px-3.5 py-1 sm:py-1.5 rounded-[7px] bg-black/40 hover:bg-black/60 border border-white/15 backdrop-blur-md transition-colors"
        >
          Skip
        </button>
      </div>

      {/* Center Translucent Glass Card Framing the Identity (20% Less Translucent, Responsive Mobile) */}
      <div className="relative z-10 w-[94%] sm:w-full max-w-md sm:max-w-xl mx-auto p-6 sm:p-10 md:p-12 rounded-[7px] bg-[#12141A]/85 backdrop-blur-2xl border border-white/15 shadow-[0_25px_60px_rgba(0,0,0,0.85)] flex flex-col items-center text-center space-y-5 sm:space-y-7 my-auto">
        {/* Glowing Ember Depth Behind Card */}
        <div className="absolute -inset-1 bg-gradient-to-r from-orange-500/15 via-pink-500/10 to-amber-500/15 rounded-[7px] blur-2xl -z-10 pointer-events-none" />

        {/* 100% Increased Size Logo */}
        <div className="relative group flex items-center justify-center py-1 sm:py-2">
          <div className="absolute -inset-8 sm:-inset-10 bg-gradient-to-tr from-[#FFA000] via-[#FF6500] to-[#D8005A] rounded-circle blur-3xl opacity-40 animate-pulse" />
          <div className="relative">
            <WeleleLogo variant="stacked" size="splash" showTagline={true} />
          </div>
        </div>

        {/* 3 Core Pillars Pill Badges */}
        <div className="flex items-center gap-2 sm:gap-2.5 pt-1 flex-wrap justify-center">
          <span className="flex items-center gap-1 text-[10px] sm:text-[11px] text-[#FFA000] font-bold bg-white/5 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-[7px] border border-white/10 backdrop-blur-md">
            <Users className="w-3 sm:w-3.5 h-3 sm:h-3.5" /> Connection
          </span>
          <span className="flex items-center gap-1 text-[10px] sm:text-[11px] text-[#FF6500] font-bold bg-white/5 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-[7px] border border-white/10 backdrop-blur-md">
            <Heart className="w-3 sm:w-3.5 h-3 sm:h-3.5" /> Emotion
          </span>
          <span className="flex items-center gap-1 text-[10px] sm:text-[11px] text-[#D8005A] font-bold bg-white/5 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-[7px] border border-white/10 backdrop-blur-md">
            <Play className="w-3 sm:w-3.5 h-3 sm:h-3.5 fill-current" /> Story
          </span>
        </div>

        {/* Integrated Sunset Progress Bar */}
        <div className="w-full max-w-[220px] sm:max-w-xs pt-1 space-y-2">
          <div className="w-full h-1.5 bg-black/60 rounded-[7px] overflow-hidden p-0.5 border border-white/10 backdrop-blur-md">
            <div
              className="h-full bg-gradient-welele rounded-[7px] transition-all duration-75 shadow-sm shadow-orange-500/60"
              style={{ width: `${Math.min(100, progress)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Bottom Corporate Parent Signature (Upright Text, Responsive) */}
      <div className="w-full max-w-xs flex flex-col items-center z-10 pb-1">
        <div className="flex items-center gap-2 text-[10px] sm:text-[11px] text-[#A8A5A1] bg-black/50 px-3.5 sm:px-4 py-1.5 rounded-[7px] border border-white/10 backdrop-blur-md">
          <span className="font-extrabold text-[#FFF8F0] tracking-wide">WELELE MEDIA™</span>
          <span className="text-welele-orange">•</span>
          <span className="text-white/90">It's about connection.</span>
        </div>
      </div>
    </div>
  );
};
