import React from 'react';
import { ExperienceSection, SlotItem } from '../../types/experience';
import { Sparkles, Zap, ArrowRight, Smartphone } from 'lucide-react';

interface EditorialBannerSectionProps {
  section: ExperienceSection;
  onOpenPaymentModal: () => void;
}

export const EditorialBannerSection: React.FC<EditorialBannerSectionProps> = ({
  section,
  onOpenPaymentModal,
}) => {
  const item: SlotItem | undefined = section.items[0];
  if (!item || item.is_active === false) return null;

  const headline = item.headline_override || 'Unlock 50 Coins for R15 with Vodacom & MTN Airtime';
  const subheadline = item.subheadline_override || 'Instant one-tap checkout. No credit card required.';
  const badge = item.badge || 'MZANSI FLASH DROP';
  const ctaText = item.cta_text || 'Claim Special Pack';

  return (
    <div className="relative overflow-hidden rounded-[7px] p-5 sm:p-7 bg-gradient-to-r from-orange-950/70 via-welele-surface-2 to-amber-950/50 border border-welele-orange/30 shadow-2xl">
      {/* Background Decorative Glow */}
      <div className="absolute top-0 right-0 w-60 h-60 bg-welele-orange/15 rounded-circle blur-3xl pointer-events-none" />

      <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-[7px] text-[9px] font-black uppercase bg-welele-orange text-black flex items-center gap-1 shadow-md shrink-0">
              <Zap className="w-2.5 h-2.5 fill-black" />
              {badge}
            </span>
            <span className="text-[10px] text-welele-muted flex items-center gap-1 truncate">
              <Smartphone className="w-3 h-3 text-emerald-400 shrink-0" />
              Direct Carrier Billing
            </span>
          </div>

          <h3 className="text-base sm:text-xl font-black text-[#FFF8F0] tracking-tight font-sans leading-snug break-words">
            {headline}
          </h3>

          <p className="text-xs text-welele-muted leading-relaxed line-clamp-2">
            {subheadline}
          </p>
        </div>

        {/* CTA Button */}
        <button
          onClick={onOpenPaymentModal}
          className="w-full sm:w-auto px-5 py-3 rounded-[7px] bg-gradient-to-r from-welele-orange to-amber-500 hover:from-orange-600 hover:to-amber-600 text-black font-extrabold text-xs shadow-xl flex items-center justify-center gap-1.5 transform active:scale-95 transition-all cursor-pointer shrink-0"
        >
          <span>{ctaText}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
