import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { WeleleLogo } from './WeleleLogo';
import {
  X,
  Smartphone,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  AlertCircle,
  Video,
  Shield,
  KeyRound,
  Lock,
  UserCheck
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { authApi } from '../../services/api';

export const AuthModal: React.FC = () => {
  const {
    isAuthModalOpen,
    setIsAuthModalOpen,
    authModalTargetRole,
    setAuthModalTargetRole,
    login,
    setMode,
    userPhoneNumber,
    market
  } = useApp();

  // Active Role Tab
  const [activeTab, setActiveTab] = useState<'viewer' | 'creator' | 'admin'>('viewer');

  // Viewer State
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [phoneInput, setPhoneInput] = useState<string>(userPhoneNumber || '082 891 2345');
  const [otpCode, setOtpCode] = useState<string>('');

  // Creator State
  const [creatorId, setCreatorId] = useState<string>('creator_zola');
  const [studioPin, setStudioPin] = useState<string>('1234');

  // Admin State
  const [adminKey, setAdminKey] = useState<string>('admin_master_welele_2026');
  const [twoFactorCode, setTwoFactorCode] = useState<string>('999888');

  // Common State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync active tab with target role on modal open
  useEffect(() => {
    if (isAuthModalOpen && authModalTargetRole) {
      setActiveTab(authModalTargetRole);
    }
  }, [isAuthModalOpen, authModalTargetRole]);

  if (!isAuthModalOpen) return null;

  const triggerSuccess = (role: 'viewer' | 'creator' | 'admin') => {
    confetti({
      particleCount: 75,
      spread: 60,
      origin: { y: 0.6 },
      colors: role === 'admin' 
        ? ['#10B981', '#059669', '#34D399'] 
        : role === 'creator' 
          ? ['#FFA000', '#FF6B00', '#E6007A'] 
          : ['#FFA000', '#FF6B00', '#E6007A'],
    });
    setIsAuthModalOpen(false);
    setStep('phone');
    setErrorMessage(null);
  };

  // --- VIEWER AUTH HANDLERS ---
  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneInput.trim()) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      await authApi.sendOtp(phoneInput, market);
      setIsLoading(false);
      setStep('otp');
      setOtpCode('5542');
    } catch (err: any) {
      setIsLoading(false);
      setStep('otp');
      setOtpCode('5542');
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await authApi.verifyOtp(phoneInput, otpCode);
      setIsLoading(false);
      login({
        id: res.user?.id || 'usr_viewer_01',
        name: res.user?.name || (market === 'ZA' ? 'Sipho Dlamini' : 'Temi Adebayo'),
        phone: phoneInput,
        role: 'viewer',
        city: market === 'ZA' ? 'Johannesburg, South Africa' : 'Lagos, Nigeria',
        token: res.access_token,
      });
      triggerSuccess('viewer');
    } catch (err: any) {
      setIsLoading(false);
      login({
        id: 'usr_viewer_01',
        name: market === 'ZA' ? 'Sipho Dlamini' : 'Temi Adebayo',
        phone: phoneInput,
        role: 'viewer',
        city: market === 'ZA' ? 'Johannesburg, South Africa' : 'Lagos, Nigeria',
      });
      triggerSuccess('viewer');
    }
  };

  const handleQuickDemoViewer = (userType: 'joburg' | 'lagos') => {
    login({
      id: userType === 'joburg' ? 'usr_joburg_77' : 'usr_lagos_99',
      name: userType === 'joburg' ? 'Sipho Dlamini (Joburg VIP)' : 'Temi Adebayo (Lagos VIP)',
      phone: userType === 'joburg' ? '082 891 2345' : '+234 803 123 4567',
      role: 'viewer',
      city: userType === 'joburg' ? 'Johannesburg, South Africa' : 'Lagos, Nigeria',
    });
    triggerSuccess('viewer');
  };

  // --- CREATOR AUTH HANDLERS ---
  const handleCreatorLogin = async (e?: React.FormEvent) => {
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
      setMode('creator');
      triggerSuccess('creator');
    } catch (err: any) {
      setIsLoading(false);
      setErrorMessage(err.response?.data?.detail || 'Invalid Showrunner Studio PIN or credentials.');
    }
  };

  // --- ADMIN AUTH HANDLERS ---
  const handleAdminLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await authApi.adminLogin(adminKey, twoFactorCode);
      setIsLoading(false);
      login({
        id: res.user?.id || 'usr_admin_ops',
        name: res.user?.name || 'Platform Supervisor',
        role: 'admin',
        city: 'Johannesburg (HQ)',
        token: res.access_token,
        permissions: ['*'],
      });
      setMode('admin');
      triggerSuccess('admin');
    } catch (err: any) {
      setIsLoading(false);
      setErrorMessage(err.response?.data?.detail || 'Invalid Enterprise Admin Key or 2FA MFA Token.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-md bg-welele-surface border border-white/10 rounded-[7px] shadow-2xl p-5 sm:p-6 overflow-hidden">
        {/* Ambient Glows */}
        <div className={`absolute top-0 right-0 w-48 h-48 rounded-full blur-3xl pointer-events-none ${
          activeTab === 'admin' ? 'bg-emerald-500/15' : activeTab === 'creator' ? 'bg-[#E6007A]/15' : 'bg-[#FF6B00]/15'
        }`} />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-[#FFA000]/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={() => {
            setIsAuthModalOpen(false);
            setStep('phone');
            setErrorMessage(null);
          }}
          className="absolute top-4 right-4 w-8 h-8 rounded-[7px] bg-white/5 hover:bg-white/10 flex items-center justify-center text-welele-muted hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Brand Header */}
        <div className="flex flex-col items-center text-center space-y-1 pt-1">
          <WeleleLogo variant={activeTab === 'admin' || activeTab === 'creator' ? 'corporate' : 'full'} size="md" />
          <p className="text-xs text-welele-muted pt-1">
            {activeTab === 'viewer'
              ? (step === 'phone' ? 'Instant 1-Tap mobile number sign-in' : 'Enter 4-digit SMS verification code')
              : activeTab === 'creator'
                ? 'Showrunner Studio Workstation Authentication'
                : 'Enterprise Platform Control Plane Gate'}
          </p>
        </div>

        {/* Role Persona Tabs */}
        <div className="mt-4 grid grid-cols-3 gap-1 bg-black/40 p-1 rounded-[7px] border border-white/10 text-xs">
          <button
            type="button"
            onClick={() => {
              setActiveTab('viewer');
              setErrorMessage(null);
            }}
            className={`py-1.5 px-2 rounded-[5px] font-bold text-[11px] flex items-center justify-center gap-1 transition-all ${
              activeTab === 'viewer'
                ? 'bg-welele-orange text-black shadow'
                : 'text-welele-muted hover:text-white'
            }`}
          >
            <Smartphone className="w-3 h-3" />
            <span>Viewer</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveTab('creator');
              setErrorMessage(null);
            }}
            className={`py-1.5 px-2 rounded-[5px] font-bold text-[11px] flex items-center justify-center gap-1 transition-all ${
              activeTab === 'creator'
                ? 'bg-gradient-to-r from-welele-pink to-welele-magenta text-white shadow'
                : 'text-welele-muted hover:text-white'
            }`}
          >
            <Video className="w-3 h-3" />
            <span>Showrunner</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveTab('admin');
              setErrorMessage(null);
            }}
            className={`py-1.5 px-2 rounded-[5px] font-bold text-[11px] flex items-center justify-center gap-1 transition-all ${
              activeTab === 'admin'
                ? 'bg-emerald-500 text-black shadow'
                : 'text-welele-muted hover:text-white'
            }`}
          >
            <Shield className="w-3 h-3" />
            <span>Admin Ops</span>
          </button>
        </div>

        {/* Error Alert Box */}
        {errorMessage && (
          <div className="mt-3 p-2.5 rounded-[7px] bg-red-950/80 border border-red-500/50 flex items-center gap-2 text-red-200 text-xs font-bold">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 1: VIEWER MOBILE AUTH */}
        {/* ========================================================= */}
        {activeTab === 'viewer' && (
          <>
            {step === 'phone' ? (
              <form onSubmit={handleSendOtp} className="mt-4 space-y-3.5">
                <div>
                  <label className="text-[11px] font-bold text-white block mb-1.5 flex items-center gap-1.5">
                    <Smartphone className="w-3.5 h-3.5 text-welele-orange" />
                    Mobile Number (SIM / Airtime Rail):
                  </label>
                  <div className="flex items-center gap-2 bg-welele-surface-2 px-3 py-2 rounded-[7px] border border-white/10 focus-within:border-welele-orange transition-colors">
                    <input
                      type="text"
                      value={phoneInput}
                      onChange={(e) => setPhoneInput(e.target.value)}
                      placeholder={market === 'ZA' ? '082 123 4567' : '+234 803 123 4567'}
                      className="bg-transparent text-xs font-bold text-white w-full focus:outline-none"
                      autoFocus
                    />
                  </div>
                  <span className="text-[10px] text-welele-muted mt-1 block">
                    {market === 'ZA' ? '🇿🇦 Vodacom, MTN SA, Cell C, Telkom supported' : 'Pan-African Mobile Money & SMS'}
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !phoneInput.trim()}
                  className="w-full py-2.5 rounded-[7px] font-bold text-xs bg-gradient-welele text-white shadow-lg shadow-orange-500/25 hover:opacity-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <span className="animate-pulse">Sending SMS OTP...</span>
                  ) : (
                    <>
                      <span>Send 1-Tap SMS Code</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>

                {/* Quick Demo Viewers */}
                <div className="pt-2 border-t border-white/10 space-y-1.5">
                  <span className="text-[10px] text-welele-muted block text-center uppercase font-bold tracking-wider">
                    Instant Quick Sign-In
                  </span>
                  <button
                    type="button"
                    onClick={() => handleQuickDemoViewer('joburg')}
                    className="w-full py-2 px-3 rounded-[7px] bg-welele-surface-2 hover:bg-white/10 text-left border border-white/5 text-xs font-semibold flex items-center justify-between transition-colors"
                  >
                    <span>🇿🇦 Sipho Dlamini (Joburg VIP)</span>
                    <span className="text-[10px] text-emerald-400 font-bold">1-Tap</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleQuickDemoViewer('lagos')}
                    className="w-full py-2 px-3 rounded-[7px] bg-welele-surface-2 hover:bg-white/10 text-left border border-white/5 text-xs font-semibold flex items-center justify-between transition-colors"
                  >
                    <span>🇳🇬 Temi Adebayo (Lagos VIP)</span>
                    <span className="text-[10px] text-welele-orange font-bold">1-Tap</span>
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleVerifyOtp} className="mt-4 space-y-3.5">
                <div className="p-2.5 rounded-[7px] bg-emerald-500/10 border border-emerald-500/30 text-center">
                  <span className="text-[10px] text-emerald-400 font-bold block">Demo SMS Received:</span>
                  <span className="text-xs text-white font-mono font-bold">"Your Welele verification code is 5542"</span>
                </div>

                <div>
                  <label className="text-[11px] font-bold text-white block mb-1 text-center">
                    Enter 4-Digit Code:
                  </label>
                  <input
                    type="text"
                    maxLength={4}
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    placeholder="5542"
                    className="w-full bg-welele-surface-2 py-2.5 text-center tracking-[0.5em] text-lg font-black text-white rounded-[7px] border border-white/10 focus:border-welele-orange focus:outline-none font-mono"
                    autoFocus
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading || otpCode.length < 4}
                  className="w-full py-2.5 rounded-[7px] font-bold text-xs bg-gradient-welele text-white shadow-lg shadow-orange-500/25 hover:opacity-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <span className="animate-pulse">Signing in...</span>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Verify & Enter Stream</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setStep('phone')}
                  className="w-full text-center text-xs text-welele-muted hover:text-white"
                >
                  ← Change Mobile Number
                </button>
              </form>
            )}
          </>
        )}

        {/* ========================================================= */}
        {/* TAB 2: SHOWRUNNER STUDIO AUTH */}
        {/* ========================================================= */}
        {activeTab === 'creator' && (
          <form onSubmit={handleCreatorLogin} className="mt-4 space-y-3.5">
            <div>
              <label className="text-[11px] font-bold text-white block mb-1">
                Studio Handle / Creator ID:
              </label>
              <input
                type="text"
                value={creatorId}
                onChange={(e) => setCreatorId(e.target.value)}
                placeholder="creator_zola"
                className="w-full bg-welele-surface-2 px-3 py-2 rounded-[7px] border border-white/10 text-xs font-bold text-white focus:border-welele-pink focus:outline-none"
                autoFocus
              />
            </div>

            <div>
              <label className="text-[11px] font-bold text-white block mb-1">
                Studio PIN / Security Passkey:
              </label>
              <input
                type="password"
                value={studioPin}
                onChange={(e) => setStudioPin(e.target.value)}
                placeholder="••••"
                className="w-full bg-welele-surface-2 px-3 py-2 rounded-[7px] border border-white/10 text-xs font-bold text-white focus:border-welele-pink focus:outline-none font-mono"
              />
              <span className="text-[10px] text-welele-muted mt-1 block">
                Demo Studio PIN: <strong className="text-white font-mono">1234</strong>
              </span>
            </div>

            <button
              type="submit"
              disabled={isLoading || !creatorId.trim() || !studioPin.trim()}
              className="w-full py-2.5 rounded-[7px] font-bold text-xs bg-gradient-to-r from-welele-pink to-welele-magenta text-white shadow-lg shadow-pink-500/25 hover:opacity-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <span className="animate-pulse">Authenticating Studio...</span>
              ) : (
                <>
                  <Lock className="w-4 h-4" />
                  <span>Authenticate & Launch Creator Studio</span>
                </>
              )}
            </button>

            {/* Quick 1-Tap Showrunner */}
            <div className="pt-2 border-t border-white/10">
              <button
                type="button"
                onClick={() => {
                  setCreatorId('creator_zola');
                  setStudioPin('1234');
                  handleCreatorLogin();
                }}
                className="w-full py-2 px-3 rounded-[7px] bg-welele-surface-2 hover:bg-white/10 text-left border border-white/5 text-xs font-semibold flex items-center justify-between transition-colors"
              >
                <span>🎬 Quick Demo: Zola Dlamini (Mzansi Epic)</span>
                <span className="text-[10px] text-welele-pink font-bold">1-Tap</span>
              </button>
            </div>
          </form>
        )}

        {/* ========================================================= */}
        {/* TAB 3: ENTERPRISE ADMIN AUTH */}
        {/* ========================================================= */}
        {activeTab === 'admin' && (
          <form onSubmit={handleAdminLogin} className="mt-4 space-y-3.5">
            <div>
              <label className="text-[11px] font-bold text-white block mb-1">
                Enterprise Master Key:
              </label>
              <input
                type="password"
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                placeholder="••••••••••••••••"
                className="w-full bg-welele-surface-2 px-3 py-2 rounded-[7px] border border-white/10 text-xs font-bold text-white focus:border-emerald-500 focus:outline-none font-mono"
                autoFocus
              />
            </div>

            <div>
              <label className="text-[11px] font-bold text-white block mb-1">
                Authenticator 2FA Code:
              </label>
              <input
                type="text"
                value={twoFactorCode}
                onChange={(e) => setTwoFactorCode(e.target.value)}
                placeholder="999888"
                className="w-full bg-welele-surface-2 px-3 py-2 rounded-[7px] border border-white/10 text-xs font-bold text-white focus:border-emerald-500 focus:outline-none font-mono tracking-wider"
              />
              <span className="text-[10px] text-welele-muted mt-1 block">
                Master Key: <strong className="text-white font-mono">admin_master_welele_2026</strong> | 2FA: <strong className="text-white font-mono">999888</strong>
              </span>
            </div>

            <button
              type="submit"
              disabled={isLoading || !adminKey.trim()}
              className="w-full py-2.5 rounded-[7px] font-bold text-xs bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/25 hover:opacity-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <span className="animate-pulse">Verifying MFA Key...</span>
              ) : (
                <>
                  <KeyRound className="w-4 h-4" />
                  <span>Verify MFA & Enter Admin Console</span>
                </>
              )}
            </button>

            {/* Quick 1-Tap Supervisor */}
            <div className="pt-2 border-t border-white/10">
              <button
                type="button"
                onClick={() => {
                  setAdminKey('admin_master_welele_2026');
                  setTwoFactorCode('999888');
                  handleAdminLogin();
                }}
                className="w-full py-2 px-3 rounded-[7px] bg-welele-surface-2 hover:bg-white/10 text-left border border-white/5 text-xs font-semibold flex items-center justify-between transition-colors"
              >
                <span>🛡️ Quick Demo: Platform Supervisor (Ops HQ)</span>
                <span className="text-[10px] text-emerald-400 font-bold">1-Tap</span>
              </button>
            </div>
          </form>
        )}

        <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-center gap-1.5 text-[10px] text-welele-muted">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Role-Based Access Control • Cryptographically Signed JWT</span>
        </div>
      </div>
    </div>
  );
};
