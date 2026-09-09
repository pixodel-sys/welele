import React from 'react';
import { useApp } from '../../context/AppContext';
import { WeleleLogo } from './WeleleLogo';
import { Monitor, X, Smartphone, ArrowRight, Video, ShieldCheck } from 'lucide-react';

export const DesktopGateModal: React.FC = () => {
  const { isDesktopGateModalOpen, setIsDesktopGateModalOpen } = useApp();

  if (!isDesktopGateModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-sm bg-welele-surface border border-white/10 rounded-[7px] p-6 text-center shadow-2xl space-y-4">
        {/* Glow */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-[#FFA000]/10 rounded-circle blur-3xl pointer-events-none" />

        <button
          onClick={() => setIsDesktopGateModalOpen(false)}
          className="absolute top-4 right-4 w-8 h-8 rounded-[7px] bg-white/5 hover:bg-white/10 flex items-center justify-center text-welele-muted hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="w-14 h-14 mx-auto rounded-[7px] bg-gradient-to-tr from-[#FFA000]/20 via-[#FF6B00]/20 to-[#E6007A]/20 border border-[#FF6B00]/40 flex items-center justify-center text-[#FF6B00]">
          <Monitor className="w-7 h-7" />
        </div>

        <div>
          <span className="text-[10px] font-extrabold uppercase tracking-widest text-[#FFA000] block">
            DESKTOP WORKSTATION REQUIRED
          </span>
          <h3 className="text-base font-black text-white mt-1 font-sans">
            Creator Hub & Admin Console
          </h3>
          <p className="text-xs text-welele-muted mt-2 leading-relaxed">
            The <b>Creator Studio</b> (4K vertical master uploads, AI multi-language subtitle timelines) and <b>Admin Moderation Console</b> are optimized for desktop workstations.
          </p>
        </div>

        <div className="p-3 rounded-[7px] bg-welele-surface-2 border border-white/5 text-[11px] text-white/90 text-left space-y-1.5">
          <div className="flex items-center gap-2">
            <Video className="w-4 h-4 text-welele-orange shrink-0" />
            <span>Studio video transcoding & subtitle timeline</span>
          </div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>AI content moderation queue & KYC verification</span>
          </div>
        </div>

        <button
          onClick={() => setIsDesktopGateModalOpen(false)}
          className="w-full py-3 rounded-[7px] font-bold text-xs bg-gradient-welele text-white shadow-lg shadow-orange-500/25 hover:opacity-95 transition-all flex items-center justify-center gap-2"
        >
          <Smartphone className="w-4 h-4" />
          <span>Continue Enjoying Mobile Stories</span>
        </button>
      </div>
    </div>
  );
};
