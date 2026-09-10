import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { WeleleLogo } from '../common/WeleleLogo';
import { Video, Lock, ArrowRight, ShieldCheck, AlertCircle, ArrowLeft } from 'lucide-react';
import confetti from 'canvas-confetti';
import { authApi } from '../../services/api';

export const CreatorStudioGate: React.FC = () => {
  const { login, setMode } = useApp();
  const [creatorId, setCreatorId] = useState<string>('creator_zola');
  const [studioPin, setStudioPin] = useState<string>('1234');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await authApi.creatorLogin(creatorId, studioPin);
      setIsLoading(false);
      login({
        id: res.user?.id || `usr_${creatorId}`,
        creator_id: res.user?.creator_id || creatorId,
        name: res.user?.name || 'Zola Dlamini',
        role: 'creator',
        city: 'Johannesburg, South Africa',
        token: res.access_token,
        permissions: ['series:create', 'episode:upload', 'ai:storyforge:execute', 'analytics:read:own'],
      });
      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.6 },
        colors: ['#FFA000', '#FF6B00', '#E6007A'],
      });
      setMode('creator');
    } catch (err: any) {
      setIsLoading(false);
      setErrorMessage(err.response?.data?.detail || 'Invalid Showrunner Studio PIN or credentials.');
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4 sm:p-6 animate-fade-in text-white">
      <div className="relative w-full max-w-md bg-welele-surface border border-white/10 rounded-[7px] shadow-2xl p-6 sm:p-8 overflow-hidden">
        {/* Ambient Glows */}
        <div className="absolute -top-10 -right-10 w-48 h-48 bg-welele-pink/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-48 h-48 bg-welele-magenta/15 rounded-full blur-3xl pointer-events-none" />

        {/* Back to Stream Button */}
        <button
          onClick={() => {
            if (typeof window !== 'undefined' && window.history.pushState) {
              window.history.pushState({}, '', '/');
            }
            setMode('viewer');
          }}
          className="inline-flex items-center gap-1.5 text-xs text-welele-muted hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Consumer Stream</span>
        </button>

        {/* Header Lockup */}
        <div className="flex flex-col items-center text-center space-y-2">
          <WeleleLogo variant="corporate" size="md" />
          <div className="pt-2">
            <span className="px-2.5 py-1 rounded-[7px] bg-welele-pink/10 border border-welele-pink/30 text-[11px] font-black uppercase tracking-wider text-welele-pink">
              Creator Operating System
            </span>
          </div>
          <h2 className="text-lg font-black font-cinematic uppercase tracking-wider text-white pt-1">
            Showrunner Studio Workstation
          </h2>
          <p className="text-xs text-welele-muted max-w-xs">
            Exclusive creative portal for African directors, writers, and microdrama production studios.
          </p>
        </div>

        {/* Error Alert Box */}
        {errorMessage && (
          <div className="mt-4 p-3 rounded-[7px] bg-red-950/80 border border-red-500/50 flex items-center gap-2 text-red-200 text-xs font-bold">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleLogin} className="mt-5 space-y-4">
          <div>
            <label className="text-[11px] font-bold text-white block mb-1">
              Studio ID / Showrunner Handle:
            </label>
            <input
              type="text"
              value={creatorId}
              onChange={(e) => setCreatorId(e.target.value)}
              placeholder="creator_zola"
              className="w-full bg-welele-surface-2 px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs font-bold text-white focus:border-welele-pink focus:outline-none"
              autoFocus
            />
          </div>

          <div>
            <label className="text-[11px] font-bold text-white block mb-1">
              Studio Security PIN / Passkey:
            </label>
            <input
              type="password"
              value={studioPin}
              onChange={(e) => setStudioPin(e.target.value)}
              placeholder="••••"
              className="w-full bg-welele-surface-2 px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs font-bold text-white focus:border-welele-pink focus:outline-none font-mono"
            />
            <span className="text-[10px] text-welele-muted mt-1 block">
              Default Demo PIN: <strong className="text-white font-mono">1234</strong>
            </span>
          </div>

          <button
            type="submit"
            disabled={isLoading || !creatorId.trim() || !studioPin.trim()}
            className="w-full py-3 rounded-[7px] font-bold text-xs bg-gradient-to-r from-welele-pink to-welele-magenta text-white shadow-lg shadow-pink-500/25 hover:opacity-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <span className="animate-pulse">Verifying Showrunner Credentials...</span>
            ) : (
              <>
                <Lock className="w-4 h-4" />
                <span>Authenticate & Launch Creator Studio</span>
              </>
            )}
          </button>

          {/* Quick 1-Tap Demo Showrunner */}
          <div className="pt-2 border-t border-white/10">
            <button
              type="button"
              onClick={() => {
                setCreatorId('creator_zola');
                setStudioPin('1234');
                handleLogin();
              }}
              className="w-full py-2 px-3 rounded-[7px] bg-welele-surface-2 hover:bg-white/10 text-left border border-white/5 text-xs font-semibold flex items-center justify-between transition-colors"
            >
              <span>🎬 Quick Demo: Zola Dlamini (Mzansi Epic Films)</span>
              <span className="text-[10px] text-welele-pink font-bold">1-Tap</span>
            </button>
          </div>
        </form>

        <div className="mt-5 pt-3 border-t border-white/10 flex items-center justify-center gap-1.5 text-[10px] text-welele-muted">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Tenant Boundary Isolation • Cryptographically Signed JWT</span>
        </div>
      </div>
    </div>
  );
};
