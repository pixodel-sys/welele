import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Story, Episode } from '../../types';
import { StoryDetailModal } from './StoryDetailModal';
import { ExperiencePageRenderer } from '../experience/ExperiencePageRenderer';
import {
  Play,
  Flame,
  Star,
  Plus,
  Info,
  Clock,
  Check,
  MessageCircle,
  Sparkles,
  Smartphone,
  ChevronLeft,
  ChevronRight,
  Eye,
} from 'lucide-react';

interface HomeScreenProps {
  onOpenPlayer: (story: Story, episode: Episode) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ onOpenPlayer }) => {
  const { stories, loadingStories, bookmarks, toggleBookmark, setMode, setIsCoinModalOpen } = useApp();
  const [selectedStoryForDetail, setSelectedStoryForDetail] = useState<Story | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>('All');
  const [activeHeroIndex, setActiveHeroIndex] = useState<number>(0);
  const [isHeroHovered, setIsHeroHovered] = useState<boolean>(false);

  const heroContainerRef = useRef<HTMLDivElement>(null);

  const categories = ['All', 'Drama', 'Romance', 'Crime', 'Comedy', 'Township', 'Action', 'Thriller'];

  // 1. Top Featured Titles for Hero Carousel Rotation & Ken Burns
  const featuredHeroStories = [
    stories.find((s) => s.id === 'story_blood_ties'),
    stories.find((s) => s.id === 'story_queen_of_jozi'),
    stories.find((s) => s.id === 'story_ceo_wife'),
    stories.find((s) => s.id === 'story_umembeso'),
    stories.find((s) => s.id === 'story_lagos_confidential'),
  ].filter((s): s is Story => Boolean(s));

  const activeHeroStory = featuredHeroStories[activeHeroIndex] || stories[0] || null;
  const isBookmarked = activeHeroStory ? bookmarks.has(activeHeroStory.id) : false;

  // 2. Slow, Subtle Carousel Auto-Advance (8s interval, pauses on interaction/hover)
  useEffect(() => {
    if (featuredHeroStories.length <= 1 || isHeroHovered) return;
    const interval = setInterval(() => {
      setActiveHeroIndex((prev) => (prev + 1) % featuredHeroStories.length);
    }, 8000);
    return () => clearInterval(interval);
  }, [featuredHeroStories.length, isHeroHovered]);

  // 3. Selection handler: Brings any selected story directly into Hero focus
  const handleSelectHeroStory = (story: Story, shouldScroll = false) => {
    const idx = featuredHeroStories.findIndex((s) => s.id === story.id);
    if (idx !== -1) {
      setActiveHeroIndex(idx);
    }
    if (shouldScroll && heroContainerRef.current) {
      heroContainerRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleNextHero = () => {
    setActiveHeroIndex((prev) => (prev + 1) % featuredHeroStories.length);
  };

  const handlePrevHero = () => {
    setActiveHeroIndex((prev) => (prev - 1 + featuredHeroStories.length) % featuredHeroStories.length);
  };

  if (loadingStories && stories.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-welele-muted animate-pulse">
        Loading African stories...
      </div>
    );
  }

  // Curated Content Rows (Complete Rich Catalog of African Micro-Dramas)
  const trendingNow = stories.filter((s) =>
    ['story_queen_of_jozi', 'story_ceo_wife', 'story_heist_game', 'story_barrio_billionaire', 'story_lagos_confidential'].includes(s.id)
  );

  const spotlightOriginals = stories.filter((s) =>
    ['story_blood_ties', 'story_umembeso', 'story_durban_heat', 'story_the_hustlers'].includes(s.id)
  );

  const newReleases = stories.filter((s) =>
    ['story_zulu_love', 'story_broken_vows', 'story_the_spaza_king', 'story_campus_royals', 'story_heist_game'].includes(s.id)
  );

  const continueWatching = stories.slice(0, 3);

  // Filtered stories if a specific category is active (other than 'All')
  const categoryFilteredStories =
    activeCategory === 'All'
      ? []
      : stories.filter((s) => s.genre.toLowerCase().includes(activeCategory.toLowerCase()));

  return (
    <div className="space-y-7 pb-28">
      {/* Category Pills Header */}
      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-4 py-1.5 rounded-[7px] text-xs font-bold transition-all shrink-0 ${
              activeCategory === cat
                ? 'bg-gradient-welele text-white shadow-md shadow-orange-500/20'
                : 'bg-welele-surface-2 text-welele-muted hover:text-white border border-white/5 hover:border-white/20'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Dynamic Category Filter Results View (when a specific category is selected) */}
      {activeCategory !== 'All' && (
        <section className="space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <h2 className="text-sm sm:text-base font-extrabold text-[#FFF8F0] tracking-tight">
              {activeCategory} Micro-Dramas ({categoryFilteredStories.length})
            </h2>
            <button
              onClick={() => setActiveCategory('All')}
              className="text-xs text-welele-orange font-bold hover:underline"
            >
              Show All Feeds
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
            {categoryFilteredStories.map((story) => (
              <div
                key={story.id}
                onClick={() => {
                  handleSelectHeroStory(story, true);
                }}
                className="group relative rounded-[7px] overflow-hidden bg-welele-surface-2 border border-white/5 cursor-pointer hover:border-welele-orange/50 transition-all hover:shadow-xl hover:shadow-orange-500/10"
              >
                <div className="aspect-[9/16] w-full relative">
                  <img
                    src={story.vertical_poster}
                    alt={story.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 filter brightness-90"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-welele-black via-transparent to-transparent opacity-95" />
                  <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded-[7px] bg-black/60 backdrop-blur-md text-[9px] font-bold text-welele-gold">
                    ★ {story.rating}
                  </div>
                  <div className="absolute bottom-2.5 left-2.5 right-2.5">
                    <h3 className="text-xs font-black text-white leading-snug truncate group-hover:text-welele-orange transition-colors">
                      {story.title}
                    </h3>
                    <span className="text-[10px] text-welele-muted block">
                      S1 • E{story.total_episodes} • {story.genre.split('•')[0].trim()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* WEE (Welele Experience Engine) Dynamic Master Surface Renderer */}
      {activeCategory === 'All' && (
        <ExperiencePageRenderer
          pageId="home"
          onOpenPlayer={onOpenPlayer}
          onOpenStoryDetail={(story) => setSelectedStoryForDetail(story)}
          onOpenPaymentModal={() => setIsCoinModalOpen(true)}
          bookmarks={bookmarks}
          onToggleBookmark={toggleBookmark}
        />
      )}

      {/* ========================================================================= */}
      {/* 4. Continue Watching (With Progress Bars) */}
      {/* ========================================================================= */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm sm:text-base font-extrabold text-[#FFF8F0] tracking-tight flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-welele-orange" />
            Continue Watching
          </h2>
          <span className="text-xs text-welele-orange font-bold cursor-pointer hover:underline">
            History
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {continueWatching.map((story, i) => (
            <div
              key={story.id}
              onClick={() => {
                if (story.episodes.length > 0) {
                  onOpenPlayer(story, story.episodes[0]);
                }
              }}
              className="p-3 rounded-[7px] bg-welele-surface-2 border border-white/5 hover:border-white/20 transition-all cursor-pointer group"
            >
              <div className="flex items-center gap-3">
                <img
                  src={story.vertical_poster}
                  alt={story.title}
                  className="w-14 h-18 rounded-[7px] object-cover"
                />
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-bold text-white truncate group-hover:text-welele-orange">
                    {story.title}
                  </h4>
                  <span className="text-[10px] text-welele-muted">
                    S1 • E{i + 1}
                  </span>
                  {/* Progress Bar */}
                  <div className="w-full h-1 bg-white/10 rounded-[7px] mt-2.5 overflow-hidden">
                    <div
                      className="h-full bg-gradient-welele rounded-[7px]"
                      style={{ width: `${60 - i * 15}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. Brand Showcase Feature Banners (Bottom Grid from Official Identity) */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 pt-4 border-t border-white/10">
        {/* Welele Chat */}
        <div className="p-4 rounded-[7px] bg-gradient-to-br from-welele-surface-2 to-black border border-white/10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-[7px] bg-orange-500/10 border border-orange-500/30 flex items-center justify-center text-welele-orange shrink-0">
            <MessageCircle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
              Welele Chat
              <span className="text-[9px] px-1.5 py-0.2 rounded-[7px] bg-orange-500/20 text-welele-orange font-bold">
                +3.2K
              </span>
            </h4>
            <p className="text-[11px] text-welele-muted">
              Join the conversation around your favorite stories.
            </p>
          </div>
        </div>

        {/* Create. Share. Earn. */}
        <div
          onClick={() => setMode('creator')}
          className="p-4 rounded-[7px] bg-gradient-to-br from-welele-surface-2 to-black border border-white/10 flex items-center gap-3 cursor-pointer hover:border-welele-orange/50 transition-colors"
        >
          <div className="w-10 h-10 rounded-[7px] bg-pink-500/10 border border-pink-500/30 flex items-center justify-center text-welele-pink shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-white">Create. Share. Earn.</h4>
            <p className="text-[11px] text-welele-muted">
              Monetize your stories with Welele Creator Hub.
            </p>
          </div>
        </div>

        {/* Watch Anywhere */}
        <div className="p-4 rounded-[7px] bg-gradient-to-br from-welele-surface-2 to-black border border-white/10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-[7px] bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-welele-gold shrink-0">
            <Smartphone className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-white">Watch Anywhere</h4>
            <p className="text-[11px] text-welele-muted">
              On your phone, tablet, or smart TV.
            </p>
          </div>
        </div>
      </div>

      {/* Story Details Modal */}
      <StoryDetailModal
        story={selectedStoryForDetail}
        onClose={() => setSelectedStoryForDetail(null)}
        onPlayEpisode={(s, ep) => onOpenPlayer(s, ep)}
      />
    </div>
  );
};
