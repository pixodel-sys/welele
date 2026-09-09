import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { WeleleLogo } from './WeleleLogo';
import { X, Smartphone, ArrowRight, ShieldCheck, CheckCircle2, Sparkles, User, Lock } from 'lucide-react';
import confetti from 'canvas-confetti';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, setIsAuthModalOpen, login, userPhoneNumber, market } = useApp();
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [phoneInput, setPhoneInput] = useState<string>(userPhoneNumber || '082 891 2345');
  const [otpCode, setOtpCode] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  if (!isAuthModalOpen) return null;

  const handleSendOtp = (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneInput.trim()) return;
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setStep('otp');
      setOtpCode('5542'); // Auto-fill demo OTP code
    }, 800);
  };

  const handleVerifyOtp = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      login({
        id: 'user_joburg_77',
        name: market === 'ZA' ? 'Sipho Dlamini' : 'Temi Adebayo',
        phone: phoneInput,
        avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80',
        city: market === 'ZA' ? 'Johannesburg, South Africa' : 'Lagos, Nigeria',
      });
      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.6 },
        colors: ['#FFA000', '#FF6B00', '#E6007A'],
      });
      setIsAuthModalOpen(false);
      setStep('phone');
    }, 900);
  };

  const handleQuickDemoLogin = (userType: 'joburg' | 'lagos') => {
    login({
      id: userType === 'joburg' ? 'user_joburg_77' : 'user_lagos_99',
      name: userType === 'joburg' ? 'Sipho Dlamini' : 'Temi Adebayo',
      phone: userType === 'joburg' ? '082 891 2345' : '+234 803 123 4567',
      avatar:
        userType === 'joburg'
          ? 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80'
          : 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80',
      city: userType === 'joburg' ? 'Johannesburg, South Africa' : 'Lagos, Nigeria',
    });
    setIsAuthModalOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-sm bg-welele-surface border border-white/10 rounded-[7px] shadow-2xl p-6 overflow-hidden">
        {/* Glow */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-[#FF6B00]/15 rounded-circle blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-[#E6007A]/15 rounded-circle blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={() => {
            setIsAuthModalOpen(false);
            setStep('phone');
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

            {/* Divider */}
            <div className="relative flex items-center justify-center py-2">
              <div className="border-t border-white/10 w-full" />
              <span className="bg-welele-surface px-2 text-[10px] text-welele-muted uppercase font-bold tracking-wider">
                Or Quick Demo
              </span>
            </div>

            {/* Quick 1-Tap Logins */}
            <div className="space-y-1.5">
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('joburg')}
                className="w-full py-2.5 px-3 rounded-[7px] bg-welele-surface-2 hover:bg-white/10 text-left border border-white/5 text-xs font-semibold flex items-center justify-between transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span>🇿🇦</span>
                  <span className="text-white">Sipho Dlamini (Joburg VIP)</span>
                </div>
                <span className="text-[10px] text-emerald-400 font-bold">1-Tap</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickDemoLogin('lagos')}
                className="w-full py-2.5 px-3 rounded-[7px] bg-welele-surface-2 hover:bg-white/10 text-left border border-white/5 text-xs font-semibold flex items-center justify-between transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span>🇳🇬</span>
                  <span className="text-white">Temi Adebayo (Lagos VIP)</span>
                </div>
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
                  <span>Verify & Enter Welele</span>
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
          <span>Zero passwords needed • Linked to SIM Airtime</span>
        </div>
      </div>
    </div>
  );
};
