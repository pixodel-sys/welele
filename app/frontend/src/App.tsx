import React, { useState, useEffect } from 'react';
import { useApp } from './context/AppContext';
import { Header } from './components/common/Header';
import { BottomNav } from './components/common/BottomNav';
import { CoinModal } from './components/common/CoinModal';
import { GiftModal } from './components/common/GiftModal';
import { AuthModal } from './components/common/AuthModal';
import { DesktopGateModal } from './components/common/DesktopGateModal';
import { SplashScreen } from './components/common/SplashScreen';
import { PWAInstallBanner } from './components/common/PWAInstallBanner';
import { HomeScreen } from './components/viewer/HomeScreen';
import { DiscoverScreen } from './components/viewer/DiscoverScreen';
import { VerticalPlayer } from './components/viewer/VerticalPlayer';
import { ProfileScreen } from './components/viewer/ProfileScreen';
import { Story, Episode } from './types';
import { Bookmark, Play, Star, Lock } from 'lucide-react';
import { useContentProtection } from './hooks/useContentProtection';
import { useSeoHead } from './hooks/useSeoHead';
import { telemetryService } from './services/telemetryService';

// Route-level lazy loading for operational surfaces to optimize initial viewer bundle
const CreatorStudioShell = React.lazy(() =>
  import('./components/creator/CreatorStudioShell').then((m) => ({ default: m.CreatorStudioShell }))
);
const CreatorStudioGate = React.lazy(() =>
  import('./components/creator/CreatorStudioGate').then((m) => ({ default: m.CreatorStudioGate }))
);
const ProductionRoom = React.lazy(() =>
  import('./components/production/ProductionRoom').then((m) => ({ default: m.ProductionRoom }))
);
const ProductionGate = React.lazy(() =>
  import('./components/production/ProductionGate').then((m) => ({ default: m.ProductionGate }))
);
const AdminDashboard = React.lazy(() =>
  import('./components/admin/AdminDashboard').then((m) => ({ default: m.AdminDashboard }))
);
const AdminGate = React.lazy(() =>
  import('./components/admin/AdminGate').then((m) => ({ default: m.AdminGate }))
);

const ModeLoadingFallback: React.FC = () => (
  <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3">
    <div className="w-8 h-8 border-2 border-welele-orange border-t-transparent rounded-full animate-spin" />
    <span className="text-xs text-welele-muted font-bold tracking-wider uppercase">Loading Workspace...</span>
  </div>
);

export const App: React.FC = () => {
  const appRenderCount = React.useRef<number>(0);
  appRenderCount.current += 1;

  const {
    mode,
    setMode,
    user,
    stories,
    bookmarks,
    setCurrentStory,
    setCurrentEpisode,
    showSplash,
    setShowSplash,
    userId,
  } = useApp();

  console.debug(
    `[App Instrumentation] Render #${appRenderCount.current} | showSplash=${showSplash} | mode='${mode}' | stories=${stories.length}`
  );

  // Sync URL Path with Operational Surface
  useEffect(() => {
    const handleLocation = () => {
      const path = window.location.pathname.toLowerCase();
      const params = new URLSearchParams(window.location.search);
      const portal = params.get('portal');
      if (path === '/production' || path.startsWith('/production/') || portal === 'production') {
        setMode('production');
      } else if (path === '/creator' || path.startsWith('/creator/') || portal === 'creator') {
        setMode('creator');
      } else if (path === '/admin' || path.startsWith('/admin/') || portal === 'admin') {
        setMode('admin');
      } else if (path === '/' || path === '') {
        setMode('viewer');
      }
    };
    handleLocation();
    window.addEventListener('popstate', handleLocation);
    // Phase 3A: Track initial APP_OPEN
    telemetryService.trackAppOpen();
    return () => window.removeEventListener('popstate', handleLocation);
  }, [setMode]);

  // Right-click / DRM protection is strictly scoped to the Viewer section.
  // Admin and Production (and Creator) sections have standard browser context menus enabled for workflow & spellcheck.
  const isViewerMode = mode === 'viewer';

  const { isSecurityAlertActive, securityMessage } = useContentProtection({
    enabled: isViewerMode,
    watermarkText: `Welele DRM • ${userId || 'ZA_STREAM'}`,
  });

  // Enable native browser spell-checking across all creator/admin text inputs and textareas
  useEffect(() => {
    if (mode === 'viewer') return;

    const enableSpellCheck = () => {
      const editableFields = document.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>(
        'input[type="text"], input:not([type]), textarea'
      );
      editableFields.forEach((field) => {
        if (!field.hasAttribute('spellcheck') || field.getAttribute('spellcheck') === 'false') {
          field.setAttribute('spellcheck', 'true');
        }
      });
    };

    enableSpellCheck();
    const observer = new MutationObserver(() => {
      enableSpellCheck();
    });

    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [mode]);

  const [activeViewerTab, setActiveViewerTab] = useState<'home' | 'discover' | 'foryou' | 'mylist' | 'profile'>('home');
  const [isWatchingFullscreen, setIsWatchingFullscreen] = useState<boolean>(false);

  const handleOpenPlayer = (story: Story, episode?: Episode) => {
    setCurrentStory(story);
    let targetEpisode = episode;
    if (!targetEpisode && story.episodes && story.episodes.length > 0) {
      try {
        const saved = localStorage.getItem(`welele_resume_${story.id}`);
        if (saved) {
          const parsed = JSON.parse(saved);
          const found = story.episodes.find((e) => e.id === parsed.episodeId);
          if (found) targetEpisode = found;
        }
      } catch (e) {}
      if (!targetEpisode) targetEpisode = story.episodes[0];
    }
    setCurrentEpisode(targetEpisode || null);
    setIsWatchingFullscreen(true);
  };

  const handleSplashComplete = React.useCallback(() => {
    setShowSplash(false);
  }, [setShowSplash]);

  // Dynamic SEO metadata based on current operating surface & viewer tab
  const getSeoMetadata = () => {
    if (mode === 'creator') {
      return {
        title: 'Creator Studio | Welele™ Creator OS',
        description: 'Publish, script, and monetize high-impact African micro-dramas with the Welele Creator Studio.',
        url: '/creator',
      };
    }
    if (mode === 'production') {
      return {
        title: 'Production Room & Story Forge | Welele™',
        description: 'AI-augmented African narrative engineering and story packaging workflow.',
        url: '/production',
      };
    }
    if (mode === 'admin') {
      return {
        title: 'Enterprise Control Plane | Welele™ Admin',
        description: 'Operations, catalog governance, and creator payout management.',
        url: '/admin',
      };
    }
    if (activeViewerTab === 'discover') {
      return {
        title: 'Discover African Micro-Dramas | Welele™',
        description: 'Explore trending South African dramas, Nollywood romances, township thrillers, and comedies in 1-minute episodes.',
        url: '/discover',
      };
    }
    if (activeViewerTab === 'mylist') {
      return {
        title: 'My Saved Stories | Welele™',
        description: 'Your personal bookmarked African micro-drama watchlist on Welele.',
        url: '/mylist',
      };
    }
    return {
      title: 'Welele™ | Stories That Move You',
      description: "Africa's premier vertical micro-drama storytelling platform. Binge 1-minute African drama series anytime, anywhere.",
      url: '/',
    };
  };

  const seoMeta = getSeoMetadata();
  useSeoHead({
    title: seoMeta.title,
    description: seoMeta.description,
    url: seoMeta.url,
  });

  const bookmarkedStories = stories.filter((s) => bookmarks.has(s.id));

  return (
    <div className="min-h-[100dvh] cinematic-app-bg text-[#FFF5EA] flex flex-col font-sans selection:bg-[#FF6B00] selection:text-black overflow-x-hidden select-none relative">
      {/* Ambient Atmospheric Cinematic Background Layers */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        {/* Top-center warm amber / orange glow */}
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[700px] sm:w-[950px] h-[550px] bg-gradient-to-b from-[#FF6500]/12 via-[#D8005A]/06 to-transparent rounded-full blur-[120px] opacity-70" />
        
        {/* Mid-right deep magenta / purple depth */}
        <div className="absolute top-[35%] -right-40 w-[550px] h-[550px] bg-gradient-to-br from-[#D8005A]/08 via-[#2A1020]/20 to-transparent rounded-full blur-[130px] opacity-60" />
        
        {/* Bottom-left warm golden ember glow */}
        <div className="absolute top-[70%] -left-32 w-[600px] h-[600px] bg-gradient-to-tr from-[#FFA000]/07 via-[#FF6500]/04 to-transparent rounded-full blur-[140px] opacity-50" />
      </div>

      {/* Animated Brand Splash Screen on Initial App Load */}
      {showSplash && <SplashScreen onComplete={handleSplashComplete} durationMs={2400} />}

      {/* Content Protection Padlock Indicator */}
      {isSecurityAlertActive && (
        <div className="fixed top-5 left-1/2 -translate-x-1/2 z-[9999] p-3.5 rounded-full bg-black/85 backdrop-blur-md border border-white/20 shadow-2xl text-amber-400 flex items-center justify-center animate-fade-in pointer-events-none transition-all">
          <Lock className="w-6 h-6 stroke-[2.2]" />
        </div>
      )}

      {/* Universal Top Brand Header */}
      <Header />

      {/* Main App Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-5 relative">
        {/* MODE: VIEWER */}
        {mode === 'viewer' && (
          <div className="w-full">
            {isWatchingFullscreen || activeViewerTab === 'foryou' ? (
              <div className="w-full">
                <VerticalPlayer
                  onBack={() => {
                    setIsWatchingFullscreen(false);
                    if (activeViewerTab === 'foryou') setActiveViewerTab('home');
                  }}
                />
              </div>
            ) : (
              <div>
                {activeViewerTab === 'home' && (
                  <HomeScreen onOpenPlayer={handleOpenPlayer} />
                )}
                {activeViewerTab === 'discover' && (
                  <DiscoverScreen onOpenPlayer={handleOpenPlayer} />
                )}
                {activeViewerTab === 'mylist' && (
                  <div className="space-y-4 max-w-4xl mx-auto pb-20">
                    <div className="flex items-center gap-2">
                      <Bookmark className="w-5 h-5 text-welele-orange fill-current" />
                      <h1 className="text-xl font-black text-white">My Saved List</h1>
                    </div>

                    {bookmarkedStories.length === 0 ? (
                      <div className="text-center py-16 p-6 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-3">
                        <Bookmark className="w-10 h-10 text-welele-muted mx-auto" />
                        <h3 className="text-sm font-bold text-white">Your list is empty</h3>
                        <p className="text-xs text-welele-muted max-w-xs mx-auto">
                          Explore trending African micro-dramas and tap 'Save' to keep your favorites here.
                        </p>
                        <button
                          onClick={() => setActiveViewerTab('home')}
                          className="px-4 py-2 rounded-[7px] bg-gradient-welele text-white text-xs font-bold shadow"
                        >
                          Explore Stories
                        </button>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                        {bookmarkedStories.map((story) => (
                          <div
                            key={story.id}
                            onClick={() => {
                              if (story.episodes.length > 0) {
                                handleOpenPlayer(story, story.episodes[0]);
                              }
                            }}
                            className="group relative rounded-2xl overflow-hidden bg-welele-surface-2 border border-white/5 cursor-pointer hover:border-welele-orange/50 transition-all"
                          >
                            <div className="aspect-[9/16] w-full relative">
                              <img src={story.vertical_poster} alt={story.title} className="w-full h-full object-cover" />
                              <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-90" />
                              <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded bg-black/60 text-[9px] font-bold text-welele-gold">
                                ★ {story.rating}
                              </div>
                              <div className="absolute bottom-2.5 left-2.5 right-2.5">
                                <h3 className="text-xs font-bold text-white leading-snug truncate group-hover:text-welele-orange">
                                  {story.title}
                                </h3>
                                <span className="text-[10px] text-welele-muted block">{story.genre}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {activeViewerTab === 'profile' && <ProfileScreen />}
              </div>
            )}
          </div>
        )}

        {/* MODE: CREATOR STUDIO (Creator Operating System: /creator) */}
        {mode === 'creator' && (
          <React.Suspense fallback={<ModeLoadingFallback />}>
            {user?.role === 'creator' || user?.role === 'admin' ? (
              <CreatorStudioShell />
            ) : (
              <CreatorStudioGate />
            )}
          </React.Suspense>
        )}

        {/* MODE: PRODUCTION ROOM (Story Forge & Narrative Packaging: /production) */}
        {mode === 'production' && (
          <React.Suspense fallback={<ModeLoadingFallback />}>
            {user?.role === 'admin' ? (
              <ProductionRoom />
            ) : (
              <ProductionGate />
            )}
          </React.Suspense>
        )}

        {/* MODE: ADMIN CONSOLE (Enterprise Control Plane: /admin) */}
        {mode === 'admin' && (
          <React.Suspense fallback={<ModeLoadingFallback />}>
            {user?.role === 'admin' ? (
              <AdminDashboard />
            ) : (
              <AdminGate />
            )}
          </React.Suspense>
        )}
      </main>

      {/* Viewer Bottom Mobile Navigation Bar */}
      {mode === 'viewer' && !isWatchingFullscreen && activeViewerTab !== 'foryou' && (
        <BottomNav
          activeTab={activeViewerTab}
          setActiveTab={setActiveViewerTab}
          onOpenCreate={() => {
            setMode('creator');
          }}
        />
      )}

      {/* PWA 1-Tap Homescreen Install Banner */}
      <PWAInstallBanner />

      {/* Global Modals */}
      <CoinModal />
      <GiftModal />
      <AuthModal />
      <DesktopGateModal />
    </div>
  );
};
export default App;
