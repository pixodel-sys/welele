import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { WeleleLogo } from './WeleleLogo';
import {
  X,
  Smartphone,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  AlertCircle
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { authApi } from '../../services/api';

export const AuthModal: React.FC = () => {
  const {
    isAuthModalOpen,
    setIsAuthModalOpen,
    login,
    userPhoneNumber,
    market
  } = useApp();

  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [phoneInput, setPhoneInput] = useState<string>(userPhoneNumber || '082 891 2345');
  const [otpCode, setOtpCode] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isAuthModalOpen) return null;

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
      triggerSuccess();
    } catch (err: any) {
      setIsLoading(false);
      login({
        id: 'usr_viewer_01',
        name: market === 'ZA' ? 'Sipho Dlamini' : 'Temi Adebayo',
        phone: phoneInput,
        role: 'viewer',
        city: market === 'ZA' ? 'Johannesburg, South Africa' : 'Lagos, Nigeria',
      });
      triggerSuccess();
    }
  };

  const handleQuickDemoLogin = (userType: 'joburg' | 'lagos') => {
    login({
      id: userType === 'joburg' ? 'usr_joburg_77' : 'usr_lagos_99',
      name: userType === 'joburg' ? 'Sipho Dlamini (Joburg VIP)' : 'Temi Adebayo (Lagos VIP)',
      phone: userType === 'joburg' ? '082 891 2345' : '+234 803 123 4567',
      role: 'viewer',
      city: userType === 'joburg' ? 'Johannesburg, South Africa' : 'Lagos, Nigeria',
    });
    triggerSuccess();
  };

  const triggerSuccess = () => {
    confetti({
      particleCount: 70,
      spread: 60,
      origin: { y: 0.6 },
      colors: ['#FFA000', '#FF6B00', '#E6007A'],
    });
    setIsAuthModalOpen(false);
    setStep('phone');
    setErrorMessage(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-sm bg-welele-surface border border-white/10 rounded-[7px] shadow-2xl p-6 overflow-hidden">
        {/* Ambient Glows */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-[#FF6B00]/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-[#E6007A]/15 rounded-full blur-3xl pointer-events-none" />

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
        <div className="flex flex-col items-center text-center space-y-2 pt-2">
          <WeleleLogo variant="full" size="md" />
          <p className="text-xs text-welele-muted pt-1">
            {step === 'phone'
              ? 'Enter your mobile number for instant 1-tap sign-in'
              : 'Enter the 4-digit SMS verification code'}
          </p>
        </div>

        {/* Error Alert Box */}
        {errorMessage && (
          <div className="mt-3 p-3 rounded-[7px] bg-red-950/80 border border-red-500/50 flex items-center gap-2 text-red-200 text-xs font-bold">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Step 1: Phone Input Form */}
        {step === 'phone' ? (
          <form onSubmit={handleSendOtp} className="mt-5 space-y-3.5">
            <div>
              <label className="text-[11px] font-bold text-white block mb-1.5 flex items-center gap-1.5">
                <Smartphone className="w-3.5 h-3.5 text-welele-orange" />
                Mobile Number (SIM / Airtime Rail):
              </label>
              <div className="flex items-center gap-2 bg-welele-surface-2 px-3 py-2.5 rounded-[7px] border border-white/10 focus-within:border-welele-orange transition-colors">
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
              className="w-full py-3 rounded-[7px] font-bold text-xs bg-gradient-welele text-white shadow-lg shadow-orange-500/25 hover:opacity-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
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
                onClick={() => handleQuickDemoLogin('joburg')}
                className="w-full py-2 px-3 rounded-[7px] bg-welele-surface-2 hover:bg-white/10 text-left border border-white/5 text-xs font-semibold flex items-center justify-between transition-colors"
              >
                <span>🇿🇦 Sipho Dlamini (Joburg VIP)</span>
                <span className="text-[10px] text-emerald-400 font-bold">1-Tap</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickDemoLogin('lagos')}
                className="w-full py-2 px-3 rounded-[7px] bg-welele-surface-2 hover:bg-white/10 text-left border border-white/5 text-xs font-semibold flex items-center justify-between transition-colors"
              >
                <span>🇳🇬 Temi Adebayo (Lagos VIP)</span>
                <span className="text-[10px] text-welele-orange font-bold">1-Tap</span>
              </button>
            </div>
          </form>
        ) : (
          /* Step 2: OTP Verification */
          <form onSubmit={handleVerifyOtp} className="mt-5 space-y-4">
            <div className="p-3 rounded-[7px] bg-emerald-500/10 border border-emerald-500/30 text-center">
              <span className="text-[10px] text-emerald-400 font-bold block">Demo SMS Received:</span>
              <span className="text-xs text-white font-mono font-bold">"Your Welele verification code is 5542"</span>
            </div>

            <div>
              <label className="text-[11px] font-bold text-white block mb-1.5 text-center">
                Enter 4-Digit Code:
              </label>
              <input
                type="text"
                maxLength={4}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                placeholder="5542"
                className="w-full bg-welele-surface-2 py-3 text-center tracking-[0.5em] text-lg font-black text-white rounded-[7px] border border-white/10 focus:border-welele-orange focus:outline-none font-mono"
                autoFocus
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || otpCode.length < 4}
              className="w-full py-3 rounded-[7px] font-bold text-xs bg-gradient-welele text-white shadow-lg shadow-orange-500/25 hover:opacity-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
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

        <div className="mt-5 pt-3 border-t border-white/10 flex items-center justify-center gap-1.5 text-[10px] text-welele-muted">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Friction-Free Stream • Linked to SIM Airtime</span>
        </div>
      </div>
    </div>
  );
};
