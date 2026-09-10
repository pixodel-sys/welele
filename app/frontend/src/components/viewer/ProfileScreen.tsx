import React from 'react';
import { useApp } from '../../context/AppContext';
import { MarketRegion } from '../../types';
import {
  Bookmark,
  Globe,
  Smartphone,
  Sparkles,
  Signal,
  Zap,
  PhoneCall,
  CheckCircle2,
  Ticket,
  ChevronRight,
  ShieldCheck,
  User,
  LogOut,
  LogIn
} from 'lucide-react';

export const ProfileScreen: React.FC = () => {
  const {
    userName,
    userAvatar,
    coins,
    setIsCoinModalOpen,
    bookmarks,
    stories,
    market,
    setMarket,
    selectedCarrier,
    setSelectedCarrier,
    airtimeBalance,
    topupAirtimeBalance,
    userPhoneNumber,
    autoAirtimeUnlock,
    setAutoAirtimeUnlock,
    activePasses,
    activeLanguage,
    setActiveLanguage,
    attemptModeChange,
    isLoggedIn,
    setIsAuthModalOpen,
    logout,
    user,
    setShowSplash,
  } = useApp();

  const savedStories = stories.filter((s) => bookmarks.has(s.id));

  const carrierLabels: Record<string, { name: string; color: string; icon: string }> = {
    vodacom_airtime: { name: 'Vodacom SA (LTE/5G)', color: 'text-red-400', icon: '🔴' },
    mtn_sa_airtime: { name: 'MTN South Africa (5G)', color: 'text-yellow-300', icon: '🟡' },
    cellc_airtime: { name: 'Cell C Mobile (4G)', color: 'text-white', icon: '⚫' },
    telkom_airtime: { name: 'Telkom Mobile (LTE)', color: 'text-blue-400', icon: '🔵' },
  };

  const languages = [
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
    <div className="space-y-5 pb-24 max-w-lg mx-auto">
      {/* Profile Card */}
      <div className="relative p-6 rounded-[7px] bg-gradient-to-b from-welele-surface-2 to-welele-surface border border-white/10 shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between relative z-10">
          <div className="flex items-center gap-4">
            <img
              src={userAvatar}
              alt={userName}
              className="w-16 h-16 rounded-[7px] object-cover border-2 border-welele-orange shadow-lg"
            />
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-black text-white">{userName}</h2>
                <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-bold bg-welele-orange/20 text-welele-orange border border-welele-orange/30">
                  {market === 'ZA' ? '🇿🇦 MZANSI VIP' : 'VIP VIEWER'}
                </span>
              </div>
              <p className="text-xs text-welele-muted">
                {user.city || (market === 'ZA' ? 'Johannesburg, South Africa' : 'Lagos, Nigeria')} • {userPhoneNumber}
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsAuthModalOpen(true)}
            className="p-2 rounded-[7px] bg-white/5 hover:bg-white/10 text-welele-muted hover:text-white transition-colors"
            title="Switch Account / Sign In"
          >
            <User className="w-4 h-4 text-welele-orange" />
          </button>
        </div>

        {/* Coin Balance Wallet Card */}
        <div className="mt-5 p-4 rounded-[7px] bg-gradient-welele text-white shadow-xl shadow-orange-500/20 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold tracking-wider uppercase text-white/80">
              Welele Coin Balance
            </span>
            <div className="text-2xl font-black font-cinematic flex items-center gap-1.5 mt-0.5">
              <span>🪙 {coins}</span>
              <span className="text-xs font-semibold opacity-90">Coins</span>
            </div>
          </div>

          <button
            onClick={() => setIsCoinModalOpen(true)}
            className="px-4 py-2 rounded-[7px] bg-black/40 hover:bg-black/60 backdrop-blur-md text-white font-bold text-xs border border-white/20 transition-all active:scale-95"
          >
            + Top Up Airtime / Coins
          </button>
        </div>
      </div>

      {/* Mzansi Mobile Airtime Hub (South Africa Customisation) */}
      <div className="p-5 rounded-[7px] bg-gradient-to-br from-emerald-950/60 via-welele-surface-2 to-teal-950/50 border border-emerald-500/30 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-[7px] bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Signal className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-1.5">
                Mzansi SIM & Airtime Wallet
                <span className="text-[9px] px-1.5 py-0.2 rounded-[7px] bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                  🇿🇦 ZA Rail
                </span>
              </h3>
              <p className="text-[10px] text-emerald-400/80">
                Carrier: {carrierLabels[selectedCarrier]?.name || 'Vodacom SA'}
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsCoinModalOpen(true)}
            className="text-[11px] font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-0.5"
          >
            Manage <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Live Airtime Balance Widget */}
        <div className="flex items-center justify-between p-3.5 rounded-[7px] bg-black/40 border border-white/5">
          <div>
            <span className="text-[10px] text-welele-muted block font-medium">SIM Airtime Available</span>
            <div className="text-2xl font-black text-emerald-300 font-cinematic">
              R{airtimeBalance.toFixed(2)}
            </div>
            <span className="text-[10px] text-welele-muted">Number: {userPhoneNumber}</span>
          </div>

          <div className="flex flex-col items-end gap-1.5">
            <span className="text-[10px] font-bold text-emerald-400">Quick Recharge:</span>
            <div className="flex gap-1">
              {[10, 25, 50].map((amt) => (
                <button
                  key={amt}
                  onClick={() => topupAirtimeBalance(amt)}
                  className="px-2 py-1 rounded-[7px] bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-[10px] font-bold text-emerald-300 transition-colors"
                >
                  +R{amt}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Carrier Quick Switcher */}
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-welele-muted uppercase tracking-wider block">
            Select Active Mobile Network:
          </label>
          <div className="grid grid-cols-4 gap-1.5">
            {[
              { id: 'vodacom_airtime', label: 'Vodacom', icon: '🔴' },
              { id: 'mtn_sa_airtime', label: 'MTN SA', icon: '🟡' },
              { id: 'cellc_airtime', label: 'Cell C', icon: '⚫' },
              { id: 'telkom_airtime', label: 'Telkom', icon: '🔵' },
            ].map((c) => (
              <button
                key={c.id}
                onClick={() => setSelectedCarrier(c.id)}
                className={`py-1.5 px-2 rounded-[7px] text-[11px] font-bold border transition-all flex items-center justify-center gap-1 ${
                  selectedCarrier === c.id
                    ? 'border-emerald-400 bg-emerald-500/20 text-white shadow'
                    : 'border-white/10 bg-black/20 text-welele-muted hover:text-white'
                }`}
              >
                <span>{c.icon}</span>
                <span className="truncate">{c.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 1-Tap Auto Unlock Toggle */}
        <div className="flex items-center justify-between pt-2 border-t border-white/5">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-emerald-400" />
            <div>
              <div className="text-xs font-bold text-white">1-Tap Airtime Auto-Unlock</div>
              <p className="text-[10px] text-welele-muted">
                Auto-deduct R3 from airtime at cliffhangers for non-stop bingeing
              </p>
            </div>
          </div>

          <input
            type="checkbox"
            checked={autoAirtimeUnlock}
            onChange={(e) => setAutoAirtimeUnlock(e.target.checked)}
            className="w-4 h-4 accent-emerald-500 rounded-[7px] cursor-pointer"
          />
        </div>

        {/* Active Passes Count */}
        {activePasses.size > 0 && (
          <div className="p-2.5 rounded-[7px] bg-emerald-500/15 border border-emerald-500/30 flex items-center gap-2 text-emerald-300 text-xs font-medium">
            <Ticket className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Active Mzansi Airtime Passes ({activePasses.size}) active!</span>
          </div>
        )}
      </div>

      {/* Saved Bookmarks */}
      <div className="p-5 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
            <Bookmark className="w-4 h-4 text-welele-gold" />
            My Saved Series ({savedStories.length})
          </h3>
        </div>

        {savedStories.length === 0 ? (
          <p className="text-xs text-welele-muted py-2">
            No saved stories yet. Tap the bookmark icon while watching any episode to save it here!
          </p>
        ) : (
          <div className="grid grid-cols-3 gap-2.5">
            {savedStories.map((story) => (
              <div key={story.id} className="rounded-[7px] overflow-hidden aspect-[9/16] relative group">
                <img
                  src={story.vertical_poster}
                  alt={story.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent flex items-end p-1.5">
                  <span className="text-[10px] font-bold text-white line-clamp-1">{story.title}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Account Preferences & Region Switcher */}
      <div className="p-5 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-3 text-xs">
        <h3 className="font-bold text-white uppercase tracking-wider mb-2">Account & Regional Settings</h3>

        {/* Market Region */}
        <div className="flex items-center justify-between py-2 border-b border-white/5">
          <span className="text-welele-muted flex items-center gap-2">
            <Globe className="w-4 h-4 text-welele-orange" /> Regional Market
          </span>
          <select
            value={market}
            onChange={(e) => setMarket(e.target.value as MarketRegion)}
            className="bg-welele-surface-2 border border-white/10 px-2 py-1 rounded-[7px] text-white font-bold text-xs focus:outline-none cursor-pointer"
          >
            <option value="ZA" className="bg-welele-surface text-white">🇿🇦 South Africa (ZAR)</option>
            <option value="NG" className="bg-welele-surface text-white">🇳🇬 Nigeria (NGN)</option>
            <option value="KE" className="bg-welele-surface text-white">🇰🇪 Kenya (KES)</option>
            <option value="GHS" className="bg-welele-surface text-white">🇬🇭 Ghana (GHS)</option>
            <option value="GLOBAL" className="bg-welele-surface text-white">🌍 Global (USD)</option>
          </select>
        </div>

        {/* Subtitle Language */}
        <div className="flex items-center justify-between py-2 border-b border-white/5">
          <span className="text-welele-muted flex items-center gap-2">
            <Globe className="w-4 h-4 text-welele-gold" /> Subtitle Language
          </span>
          <select
            value={activeLanguage}
            onChange={(e) => setActiveLanguage(e.target.value)}
            className="bg-welele-surface-2 border border-white/10 px-2 py-1 rounded-[7px] text-white font-bold text-xs focus:outline-none cursor-pointer"
          >
            {languages.map((lang) => (
              <option key={lang} value={lang} className="bg-welele-surface text-white">
                {lang}
              </option>
            ))}
          </select>
        </div>

        {/* Verified Creator Portal Shortcut (Only visible to authenticated Showrunners & Admins) */}
        {(user?.role === 'creator' || user?.role === 'admin') && (
          <button
            onClick={() => attemptModeChange('creator')}
            className="w-full mt-2 py-3 rounded-[7px] bg-gradient-to-r from-welele-pink to-welele-magenta text-white font-bold text-xs shadow-lg shadow-pink-500/20 hover:opacity-90 flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4" /> Open Creator Studio™ Workstation
          </button>
        )}

        {/* Replay Brand Splash Screen Intro */}
        <button
          onClick={() => setShowSplash(true)}
          className="w-full py-2.5 rounded-[7px] bg-white/5 hover:bg-white/10 text-welele-muted hover:text-white font-semibold text-xs border border-white/10 flex items-center justify-center gap-2"
        >
          <Sparkles className="w-3.5 h-3.5 text-[#FFA000]" />
          <span>Replay Brand Intro Screen</span>
        </button>

        {/* Auth Sign In / Switch Account */}
        <button
          onClick={() => setIsAuthModalOpen(true)}
          className="w-full py-2.5 rounded-[7px] bg-white/5 hover:bg-white/10 text-white font-semibold text-xs border border-white/10 flex items-center justify-center gap-2"
        >
          <LogIn className="w-3.5 h-3.5 text-welele-orange" />
          <span>Switch Account / Phone Login</span>
        </button>
      </div>
    </div>
  );
};
