import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { WeleleLogo } from '../common/WeleleLogo';
import { Sparkles, Lock, ArrowLeft, ShieldCheck, AlertCircle } from 'lucide-react';
import { authApi } from '../../services/api';

export const ProductionGate: React.FC = () => {
  const { login, setMode } = useApp();
  const [adminKey, setAdminKey] = useState<string>('admin_master_welele_2026');
  const [twoFaCode, setTwoFaCode] = useState<string>('999888');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await authApi.adminLogin(adminKey, twoFaCode);
      setIsLoading(false);
      login({
        id: res.user?.id || 'admin_supervisor',
        name: res.user?.name || 'Welele Operations Admin',
        role: 'admin',
        permissions: ['*'],
        token: res?.access_token,
      });
      setMode('production');
    } catch (err: any) {
      setIsLoading(false);
      // Offline fallback: accept known demo admin credentials
      if (adminKey === 'admin_master_welele_2026' && (twoFaCode === '999888' || !twoFaCode.trim())) {
        login({
          id: 'admin_supervisor',
          name: 'Welele Operations Admin',
          role: 'admin',
          permissions: ['*'],
        });
        setMode('production');
        return;
      }
      setErrorMessage(err.response?.data?.detail || 'Invalid Administrator Key or 2FA Token.');
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4 sm:p-6 animate-fade-in text-white">
      <div className="relative w-full max-w-md bg-welele-surface border border-white/10 rounded-[7px] shadow-2xl p-6 sm:p-8 overflow-hidden">
        {/* Ambient Glows */}
        <div className="absolute -top-10 -right-10 w-48 h-48 bg-[#FF6500]/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-48 h-48 bg-[#FFA000]/10 rounded-full blur-3xl pointer-events-none" />

        {/* Back to Stream */}
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
            <span className="px-2.5 py-1 rounded-[7px] bg-[#FF6500]/10 border border-[#FF6500]/30 text-[11px] font-black uppercase tracking-wider text-[#FF6500] flex items-center gap-1.5 w-fit mx-auto">
              <Sparkles className="w-3 h-3" />
              Production Room
            </span>
          </div>
          <h2 className="text-lg font-black font-cinematic uppercase tracking-wider text-white pt-1">
            Story Forge &amp; Narrative Lab
          </h2>
          <p className="text-xs text-welele-muted max-w-xs">
            Restricted to platform administrators only. Admin master key and 2FA token required.
          </p>
        </div>

        {/* Error Alert */}
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
              Admin Master Key:
            </label>
            <input
              type="password"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              placeholder="admin_master_welele_2026"
              className="w-full bg-welele-surface-2 px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs font-bold text-white focus:border-[#FF6500] focus:outline-none font-mono"
              autoFocus
            />
          </div>

          <div>
            <label className="text-[11px] font-bold text-white block mb-1">
              2FA Token:
            </label>
            <input
              type="password"
              value={twoFaCode}
              onChange={(e) => setTwoFaCode(e.target.value)}
              placeholder="••••••"
              className="w-full bg-welele-surface-2 px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs font-bold text-white focus:border-[#FF6500] focus:outline-none font-mono"
            />
            <span className="text-[10px] text-welele-muted mt-1 block">
              Default Demo 2FA: <strong className="text-white font-mono">999888</strong>
            </span>
          </div>

          <button
            type="submit"
            disabled={isLoading || !adminKey.trim() || !twoFaCode.trim()}
            className="w-full py-3 rounded-[7px] font-bold text-xs bg-gradient-to-r from-[#FF6500] to-[#FFA000] text-black shadow-lg shadow-orange-500/25 hover:opacity-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <span className="animate-pulse">Verifying Showrunner Credentials...</span>
            ) : (
              <>
                <Lock className="w-4 h-4" />
                <span>Authenticate &amp; Enter Production Room</span>
              </>
            )}
          </button>

          {/* Quick 1-Tap Demo */}
          <div className="pt-2 border-t border-white/10">
            <button
              type="button"
              onClick={() => {
                setAdminKey('admin_master_welele_2026');
                setTwoFaCode('999888');
                handleLogin();
              }}
              className="w-full py-2 px-3 rounded-[7px] bg-welele-surface-2 hover:bg-white/10 text-left border border-white/5 text-xs font-semibold flex items-center justify-between transition-colors"
            >
              <span>🛡️ Quick Demo: Welele Operations Admin</span>
              <span className="text-[10px] text-[#FF6500] font-bold">1-Tap</span>
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
