import React from 'react';
import { useApp } from '../../context/AppContext';
import { AppMode, MarketRegion } from '../../types';
import { WeleleLogo } from './WeleleLogo';
import { Sparkles, Shield, Video, Smartphone, Globe, Signal, User, LogIn, LogOut } from 'lucide-react';

export const Header: React.FC = () => {
  const {
    mode,
    attemptModeChange,
    coins,
    market,
    setMarket,
    airtimeBalance,
    selectedCarrier,
    setIsCoinModalOpen,
    isLoggedIn,
    setIsAuthModalOpen,
    user,
    logout,
    activeLanguage,
    setActiveLanguage,
  } = useApp();

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

  const carrierShortNames: Record<string, string> = {
    vodacom_airtime: 'Vodacom',
    mtn_sa_airtime: 'MTN SA',
    cellc_airtime: 'Cell C',
    telkom_airtime: 'Telkom',
  };

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-white/10 px-3 sm:px-4 py-2.5 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-2">
        {/* Canonical Welele Brand Lockup */}
        <div className="flex items-center gap-2">
          <div
            className="cursor-pointer flex items-center group transition-transform active:scale-95"
            onClick={() => attemptModeChange('viewer')}
            title="Welele - Stories That Move You"
          >
            {mode === 'creator' || mode === 'admin' ? (
              <WeleleLogo variant="corporate" size="sm" />
            ) : (
              <WeleleLogo variant="horizontal" size="md" />
            )}
          </div>
        </div>

        {/* Right Section: Market Selector, Airtime Badge, Coin Pill, Auth */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          {/* Market Region Selector */}
          <div className="flex items-center bg-welele-surface-2 px-2 py-1 rounded-[7px] border border-white/10 text-xs">
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value as MarketRegion)}
              aria-label="Select Market Region"
              className="bg-transparent text-white text-xs font-bold focus:outline-none cursor-pointer"
            >
              <option value="ZA" className="bg-welele-surface text-white">🇿🇦 ZA</option>
              <option value="NG" className="bg-welele-surface text-white">🇳🇬 NG</option>
              <option value="KE" className="bg-welele-surface text-white">🇰🇪 KE</option>
              <option value="GHS" className="bg-welele-surface text-white">🇬🇭 GH</option>
              <option value="GLOBAL" className="bg-welele-surface text-white">🌍 Global</option>
            </select>
          </div>

          {/* South African Airtime Balance Indicator (if ZA market) */}
          {market === 'ZA' && (
            <button
              onClick={() => setIsCoinModalOpen(true)}
              title="Click to manage SIM Airtime & Passes"
              className="hidden sm:flex items-center gap-1 bg-emerald-950/60 hover:bg-emerald-900/80 border border-emerald-500/40 text-emerald-300 px-2.5 py-1.5 rounded-[7px] text-xs font-semibold transition-all"
            >
              <Signal className="w-3 h-3 text-emerald-400 animate-pulse" />
              <span className="text-[11px] text-emerald-200">{carrierShortNames[selectedCarrier] || 'Airtime'}:</span>
              <span className="font-extrabold text-emerald-300">R{airtimeBalance.toFixed(2)}</span>
            </button>
          )}

          {/* Language Selector (Desktop) */}
          <div className="hidden lg:flex items-center gap-1 bg-welele-surface-2 px-2.5 py-1.5 rounded-[7px] border border-white/10 text-xs">
            <Globe className="w-3.5 h-3.5 text-welele-muted" />
            <select
              value={activeLanguage}
              onChange={(e) => setActiveLanguage(e.target.value)}
              aria-label="Select Application Language"
              className="bg-transparent text-white text-xs focus:outline-none cursor-pointer font-medium"
            >
              {languages.map((lang) => (
                <option key={lang} value={lang} className="bg-welele-surface text-white">
                  {lang}
                </option>
              ))}
            </select>
          </div>

          {/* Coin Pill */}
          <button
            onClick={() => setIsCoinModalOpen(true)}
            className="flex items-center gap-1.5 bg-gradient-to-r from-amber-500/20 via-orange-500/20 to-pink-500/20 hover:from-amber-500/30 hover:to-pink-500/30 border border-welele-gold/40 px-2.5 sm:px-3 py-1.5 rounded-[7px] transition-all group shadow-sm"
          >
            <div className="w-5 h-5 rounded-[7px] bg-gradient-to-tr from-amber-500 to-yellow-300 flex items-center justify-center text-[10px] text-black font-bold shadow">
              🪙
            </div>
            <span className="font-bold text-xs text-welele-gold">{coins}</span>
            <span className="hidden sm:inline text-[11px] text-welele-muted font-medium">Coins</span>
            <span className="w-4 h-4 rounded-[7px] bg-welele-orange/30 text-welele-orange flex items-center justify-center text-xs font-bold ml-0.5 group-hover:scale-110 transition-transform">
              +
            </span>
          </button>

          {/* User Sign In / Profile Avatar & Role Badge */}
          {isLoggedIn && user.role !== 'viewer' ? (
            <div className="flex items-center gap-1.5 bg-welele-surface-2 p-1 rounded-[7px] border border-white/10">
              <div className="flex items-center gap-1.5 px-2 py-0.5">
                <span className={`w-2 h-2 rounded-full ${user.role === 'admin' ? 'bg-emerald-400' : 'bg-welele-pink'} animate-pulse`} />
                <span className="text-[10px] font-bold text-white uppercase tracking-wider hidden sm:inline">
                  {user.role === 'admin' ? 'Admin' : 'Creator'}
                </span>
              </div>
              <button
                onClick={logout}
                className="px-2 py-1 rounded-[7px] bg-red-950/60 hover:bg-red-900 border border-red-500/30 text-red-300 text-[10px] font-bold flex items-center gap-1 transition-colors"
                title="Log Out and Lock Surface"
              >
                <LogOut className="w-3 h-3" />
                <span>Exit</span>
              </button>
            </div>
          ) : isLoggedIn ? (
            <button
              onClick={() => setIsAuthModalOpen(true)}
              className="w-8 h-8 rounded-[7px] border border-welele-orange/50 overflow-hidden hover:scale-105 transition-transform"
              title={`Logged in as ${user.name}`}
            >
              <img src={user.avatar} alt={user.name} className="w-full h-full object-cover" />
            </button>
          ) : (
            <button
              onClick={() => {
                setIsAuthModalOpen(true);
              }}
              className="px-3 py-1.5 rounded-[7px] bg-gradient-welele text-white text-xs font-bold shadow flex items-center gap-1 hover:opacity-95"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
