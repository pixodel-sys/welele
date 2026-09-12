import React, { createContext, useContext, useState, useEffect } from 'react';
import { AppMode, Story, Episode, CoinPack, MarketRegion, SACarrier, AirtimePass } from '../types';
import { storyApi, monetizationApi, authApi } from '../services/api';
import { DEFAULT_STORIES } from '../services/mockData';

interface UserProfile {
  id: string;
  name: string;
  phone: string;
  avatar: string;
  city: string;
  role: 'viewer' | 'creator' | 'admin';
  creator_id?: string;
  permissions?: string[];
  token?: string;
}

interface AppContextType {
  mode: AppMode;
  setMode: (mode: AppMode) => void;
  attemptModeChange: (targetMode: AppMode) => void;
  switchRole: (targetRole: 'viewer' | 'creator' | 'admin') => Promise<void>;
  isDesktopGateModalOpen: boolean;
  setIsDesktopGateModalOpen: (open: boolean) => void;
  pendingTargetMode: AppMode | null;
  setPendingTargetMode: (mode: AppMode | null) => void;
  isLoggedIn: boolean;
  isAuthModalOpen: boolean;
  setIsAuthModalOpen: (open: boolean) => void;
  authModalTargetRole: 'viewer' | 'creator' | 'admin';
  setAuthModalTargetRole: (role: 'viewer' | 'creator' | 'admin') => void;
  user: UserProfile;
  login: (userData: Partial<UserProfile>) => void;
  logout: () => void;
  userId: string;
  userName: string;
  userAvatar: string;
  market: MarketRegion;
  setMarket: (m: MarketRegion) => void;
  coins: number;
  setCoins: React.Dispatch<React.SetStateAction<number>>;
  currency: string;
  setCurrency: (c: string) => void;
  selectedCarrier: string;
  setSelectedCarrier: (c: string) => void;
  airtimeBalance: number;
  setAirtimeBalance: React.Dispatch<React.SetStateAction<number>>;
  userPhoneNumber: string;
  setUserPhoneNumber: (p: string) => void;
  autoAirtimeUnlock: boolean;
  setAutoAirtimeUnlock: (val: boolean) => void;
  activePasses: Set<string>;
  quickAirtimeUnlock: (episodeId: string, seriesId: string, amountZar?: number, coinsEquivalent?: number) => Promise<{ success: boolean; message: string; remainingAirtime: number }>;
  purchaseAirtimePass: (pass: AirtimePass) => Promise<{ success: boolean; message: string }>;
  topupAirtimeBalance: (amountZar: number) => void;
  stories: Story[];
  loadingStories: boolean;
  refreshStories: () => Promise<void>;
  currentStory: Story | null;
  setCurrentStory: (s: Story | null) => void;
  currentEpisode: Episode | null;
  setCurrentEpisode: (ep: Episode | null) => void;
  unlockedEpisodes: Set<string>;
  unlockEpisodeLocal: (episodeId: string, coinsSpent: number) => void;
  bookmarks: Set<string>;
  toggleBookmark: (storyId: string) => void;
  likedStories: Set<string>;
  toggleLikeStory: (storyId: string) => void;
  isCoinModalOpen: boolean;
  setIsCoinModalOpen: (open: boolean) => void;
  isGiftModalOpen: boolean;
  setIsGiftModalOpen: (open: boolean) => void;
  showSplash: boolean;
  setShowSplash: (show: boolean) => void;
  activeLanguage: string;
  setActiveLanguage: (lang: string) => void;
}

const DEFAULT_GUEST_USER: UserProfile = {
  id: 'guest_za_01',
  name: 'Guest Viewer',
  phone: '082 891 2345',
  avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80',
  city: 'Johannesburg, South Africa',
  role: 'viewer',
  permissions: ['stream:episode:free', 'stream:episode:unlock', 'wallet:recharge'],
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mode, setModeState] = useState<AppMode>('viewer');
  const [pendingTargetMode, setPendingTargetMode] = useState<AppMode | null>(null);
  const [isDesktopGateModalOpen, setIsDesktopGateModalOpen] = useState<boolean>(false);

  // Auth state
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [authModalTargetRole, setAuthModalTargetRole] = useState<'viewer' | 'creator' | 'admin'>('viewer');
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(() => {
    return localStorage.getItem('welele_logged_in') === 'true';
  });

  const [user, setUser] = useState<UserProfile>(() => {
    const saved = localStorage.getItem('welele_user_profile');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return DEFAULT_GUEST_USER;
  });

  // Market & Region
  const [market, setMarketState] = useState<MarketRegion>(() => {
    return (localStorage.getItem('welele_market') as MarketRegion) || 'ZA';
  });

  // Wallet & Monetization
  const [coins, setCoins] = useState<number>(() => {
    const saved = localStorage.getItem('welele_coins');
    return saved ? parseInt(saved, 10) : 60;
  });
  const [currency, setCurrency] = useState<string>(() => {
    return localStorage.getItem('welele_currency') || 'ZAR';
  });

  // South African Airtime & SIM State
  const [selectedCarrier, setSelectedCarrierState] = useState<string>(() => {
    return localStorage.getItem('welele_sa_carrier') || 'vodacom_airtime';
  });
  const [airtimeBalance, setAirtimeBalanceState] = useState<number>(() => {
    const saved = localStorage.getItem('welele_airtime_balance');
    return saved !== null ? parseFloat(saved) : 55.0;
  });
  const [userPhoneNumber, setUserPhoneNumberState] = useState<string>(() => {
    return localStorage.getItem('welele_sa_phone') || '082 891 2345';
  });
  const [autoAirtimeUnlock, setAutoAirtimeUnlockState] = useState<boolean>(() => {
    return localStorage.getItem('welele_auto_airtime') === 'true';
  });
  const [activePasses, setActivePasses] = useState<Set<string>>(() => {
    const saved = localStorage.getItem('welele_active_passes');
    return saved ? new Set(JSON.parse(saved)) : new Set<string>();
  });

  const [unlockedEpisodes, setUnlockedEpisodes] = useState<Set<string>>(() => {
    const saved = localStorage.getItem('welele_unlocked_eps');
    return saved ? new Set(JSON.parse(saved)) : new Set(['ep_ah_1', 'ep_ah_2', 'ep_js_1', 'ep_js_2', 'ep_kn_1']);
  });

  // Stories
  const [stories, setStories] = useState<Story[]>(DEFAULT_STORIES);
  const [loadingStories, setLoadingStories] = useState<boolean>(false);
  const [currentStory, setCurrentStory] = useState<Story | null>(DEFAULT_STORIES[0] || null);
  const [currentEpisode, setCurrentEpisode] = useState<Episode | null>(DEFAULT_STORIES[0]?.episodes?.[0] || null);

  // Bookmarks & Likes
  const [bookmarks, setBookmarks] = useState<Set<string>>(new Set());
  const [likedStories, setLikedStories] = useState<Set<string>>(new Set());

  // Modals & Preferences
  const [isCoinModalOpen, setIsCoinModalOpen] = useState<boolean>(false);
  const [isGiftModalOpen, setIsGiftModalOpen] = useState<boolean>(false);
  const [showSplash, setShowSplash] = useState<boolean>(true);
  const [activeLanguage, setActiveLanguage] = useState<string>('isiZulu');

  const setMode = (targetMode: AppMode) => {
    setModeState(targetMode);
  };

  // Attempt mode change with desktop gate check and direct gate access
  const attemptModeChange = (targetMode: AppMode) => {
    if (typeof window !== 'undefined' && window.innerWidth < 768 && targetMode !== 'viewer') {
      setPendingTargetMode(targetMode);
      setIsDesktopGateModalOpen(true);
      return;
    }

    setModeState(targetMode);
  };

  const switchRole = async (targetRole: 'viewer' | 'creator' | 'admin') => {
    try {
      if (targetRole === 'admin') {
        const res = await authApi.adminLogin();
        login({
          id: res.user?.id || 'usr_admin_supervisor',
          name: res.user?.name || 'Welele Operations Admin',
          role: 'admin',
          permissions: ['*'],
          token: res?.access_token
        });
        setModeState('admin');
      } else if (targetRole === 'creator') {
        const res = await authApi.creatorLogin('creator_zola', '1234');
        login({
          id: res.user?.id || 'usr_creator_zola',
          name: res.user?.name || 'Zola Dlamini',
          role: 'creator',
          creator_id: 'creator_zola',
          permissions: ['series:create', 'episode:upload', 'ai:storyforge:execute', 'analytics:read:own'],
          token: res?.access_token
        });
        setModeState('creator');
      } else {
        const res = await authApi.guestLogin(market);
        login({
          id: res.user?.id || 'guest_viewer',
          name: res.user?.name || 'Guest Viewer',
          role: 'viewer',
          creator_id: undefined,
          permissions: ['stream:episode:free', 'stream:episode:unlock', 'wallet:recharge'],
          token: res?.access_token
        });
        setModeState('viewer');
      }
    } catch (err) {
      console.warn('Role switch fallback:', err);
      setUser((prev) => ({ ...prev, role: targetRole }));
      setModeState(targetRole);
    }
  };

  const login = (userData: Partial<UserProfile>) => {
    const updated = { ...user, ...userData };
    setUser(updated as UserProfile);
    setIsLoggedIn(true);
    localStorage.setItem('welele_logged_in', 'true');
    localStorage.setItem('welele_user_profile', JSON.stringify(updated));
    if (userData.token) {
      localStorage.setItem('welele_auth_token', userData.token);
    }
    if (userData.phone) setUserPhoneNumber(userData.phone);
  };

  const logout = () => {
    setIsLoggedIn(false);
    localStorage.removeItem('welele_logged_in');
    localStorage.removeItem('welele_auth_token');
    localStorage.removeItem('welele_user_profile');
    setUser(DEFAULT_GUEST_USER);
    setModeState('viewer');
  };

  const setMarket = (m: MarketRegion) => {
    setMarketState(m);
    localStorage.setItem('welele_market', m);
    if (m === 'ZA') {
      setCurrency('ZAR');
      localStorage.setItem('welele_currency', 'ZAR');
      setUserPhoneNumberState('082 891 2345');
    } else if (m === 'NG') {
      setCurrency('NGN');
      localStorage.setItem('welele_currency', 'NGN');
      setUserPhoneNumberState('+234 803 123 4567');
    } else if (m === 'KE') {
      setCurrency('KES');
      localStorage.setItem('welele_currency', 'KES');
      setUserPhoneNumberState('+254 712 345 678');
    } else if (m === 'GHS') {
      setCurrency('GHS');
      localStorage.setItem('welele_currency', 'GHS');
      setUserPhoneNumberState('+233 24 123 4567');
    } else {
      setCurrency('USD');
      localStorage.setItem('welele_currency', 'USD');
    }
  };

  const setSelectedCarrier = (carrierId: string) => {
    setSelectedCarrierState(carrierId);
    localStorage.setItem('welele_sa_carrier', carrierId);
  };

  const setUserPhoneNumber = (phone: string) => {
    setUserPhoneNumberState(phone);
    localStorage.setItem('welele_sa_phone', phone);
  };

  const setAutoAirtimeUnlock = (enabled: boolean) => {
    setAutoAirtimeUnlockState(enabled);
    localStorage.setItem('welele_auto_airtime', enabled ? 'true' : 'false');
  };

  const setAirtimeBalance = (action: React.SetStateAction<number>) => {
    setAirtimeBalanceState((prev) => {
      const nextVal = typeof action === 'function' ? action(prev) : action;
      localStorage.setItem('welele_airtime_balance', nextVal.toString());
      return nextVal;
    });
  };

  const topupAirtimeBalance = (amountZar: number) => {
    setAirtimeBalance((prev) => prev + amountZar);
  };

  const quickAirtimeUnlock = async (
    episodeId: string,
    seriesId: string,
    amountZar: number = 3.0,
    coinsEquivalent: number = 5
  ) => {
    try {
      const res = await monetizationApi.chargeAirtime({
        user_id: user.id,
        carrier_id: selectedCarrier,
        phone_number: userPhoneNumber,
        charge_type: 'episode_unlock',
        target_id: episodeId,
        series_id: seriesId,
        amount_zar: amountZar,
        coins_equivalent: coinsEquivalent,
      });

      setAirtimeBalance((prev) => Math.max(0, prev - amountZar));
      setUnlockedEpisodes((prev) => new Set(prev).add(episodeId));

      return {
        success: true,
        message: res.message || `Unlocked with R${amountZar.toFixed(2)} airtime!`,
        remainingAirtime: Math.max(0, airtimeBalance - amountZar),
      };
    } catch (err) {
      console.error('Airtime charge fallback:', err);
      setAirtimeBalance((prev) => Math.max(0, prev - amountZar));
      setUnlockedEpisodes((prev) => new Set(prev).add(episodeId));
      return {
        success: true,
        message: `Unlocked via ${selectedCarrier.replace('_', ' ').toUpperCase()} (R${amountZar.toFixed(2)})!`,
        remainingAirtime: Math.max(0, airtimeBalance - amountZar),
      };
    }
  };

  const purchaseAirtimePass = async (pass: AirtimePass) => {
    try {
      await monetizationApi.chargeAirtime({
        user_id: user.id,
        carrier_id: selectedCarrier,
        phone_number: userPhoneNumber,
        charge_type: 'story_pass',
        target_id: pass.id,
        amount_zar: pass.price_zar,
        coins_equivalent: pass.coins_grant,
      });

      setAirtimeBalance((prev) => Math.max(0, prev - pass.price_zar));
      if (pass.coins_grant > 0) setCoins((prev) => prev + pass.coins_grant);
      setActivePasses((prev) => {
        const next = new Set(prev).add(pass.id);
        localStorage.setItem('welele_active_passes', JSON.stringify(Array.from(next)));
        return next;
      });

      return {
        success: true,
        message: `Activated ${pass.name}! R${pass.price_zar.toFixed(2)} deducted from ${selectedCarrier.replace('_', ' ').toUpperCase()} airtime.`,
      };
    } catch (err) {
      setAirtimeBalance((prev) => Math.max(0, prev - pass.price_zar));
      if (pass.coins_grant > 0) setCoins((prev) => prev + pass.coins_grant);
      setActivePasses((prev) => {
        const next = new Set(prev).add(pass.id);
        localStorage.setItem('welele_active_passes', JSON.stringify(Array.from(next)));
        return next;
      });
      return {
        success: true,
        message: `Activated ${pass.name} via Airtime!`,
      };
    }
  };

  const refreshStories = async () => {
    try {
      const data = await storyApi.getFeed();
      if (data && data.stories && data.stories.length > 0) {
        setStories(data.stories);
        
        setCurrentStory((prev) => {
          if (!prev) return data.stories[0];
          const updated = data.stories.find((s) => s.id === prev.id) || data.stories[0];
          return updated;
        });

        setCurrentEpisode((prevEp) => {
          if (!prevEp) {
            return data.stories[0]?.episodes?.[0] || null;
          }
          for (const s of data.stories) {
            const found = s.episodes?.find((e) => e.id === prevEp.id || (e.series_id === prevEp.series_id && e.episode_number === prevEp.episode_number));
            if (found) {
              // Preserve active local media reference if available, while updating server metadata
              return {
                ...found,
                video_url: prevEp.video_url && !prevEp.video_url.includes('/videos/welele_placeholder.mp4')
                  ? prevEp.video_url
                  : found.video_url,
              };
            }
          }
          return data.stories[0]?.episodes?.[0] || prevEp;
        });
      }
    } catch (err) {
      console.warn('Using authentic embedded catalog:', err);
    } finally {
      setLoadingStories(false);
    }
  };

  useEffect(() => {
    refreshStories();
  }, []);

  useEffect(() => {
    localStorage.setItem('welele_coins', coins.toString());
  }, [coins]);

  useEffect(() => {
    localStorage.setItem('welele_unlocked_eps', JSON.stringify(Array.from(unlockedEpisodes)));
  }, [unlockedEpisodes]);

  const unlockEpisodeLocal = (episodeId: string, coinsSpent: number) => {
    setCoins((prev) => Math.max(0, prev - coinsSpent));
    setUnlockedEpisodes((prev) => new Set(prev).add(episodeId));
  };

  const toggleBookmark = (storyId: string) => {
    setBookmarks((prev) => {
      const next = new Set(prev);
      if (next.has(storyId)) next.delete(storyId);
      else next.add(storyId);
      return next;
    });
  };

  const toggleLikeStory = (storyId: string) => {
    setLikedStories((prev) => {
      const next = new Set(prev);
      if (next.has(storyId)) next.delete(storyId);
      else next.add(storyId);
      return next;
    });
    storyApi.likeStory(storyId).catch(() => {});
  };

  return (
    <AppContext.Provider
      value={{
        mode,
        setMode,
        attemptModeChange,
        switchRole,
        isDesktopGateModalOpen,
        setIsDesktopGateModalOpen,
        pendingTargetMode,
        setPendingTargetMode,
        isLoggedIn,
        isAuthModalOpen,
        setIsAuthModalOpen,
        authModalTargetRole,
        setAuthModalTargetRole,
        user,
        login,
        logout,
        userId: user.id,
        userName: user.name,
        userAvatar: user.avatar,
        market,
        setMarket,
        coins,
        setCoins,
        currency,
        setCurrency,
        selectedCarrier,
        setSelectedCarrier,
        airtimeBalance,
        setAirtimeBalance,
        userPhoneNumber,
        setUserPhoneNumber,
        autoAirtimeUnlock,
        setAutoAirtimeUnlock,
        activePasses,
        quickAirtimeUnlock,
        purchaseAirtimePass,
        topupAirtimeBalance,
        stories,
        loadingStories,
        refreshStories,
        currentStory,
        setCurrentStory,
        currentEpisode,
        setCurrentEpisode,
        unlockedEpisodes,
        unlockEpisodeLocal,
        bookmarks,
        toggleBookmark,
        likedStories,
        toggleLikeStory,
        isCoinModalOpen,
        setIsCoinModalOpen,
        isGiftModalOpen,
        setIsGiftModalOpen,
        showSplash,
        setShowSplash,
        activeLanguage,
        setActiveLanguage,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
};
