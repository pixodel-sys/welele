import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { Story, Episode } from '../../types';
import { WeleleLogo } from '../common/WeleleLogo';
import { Search, Globe, Sparkles, Play, Heart, Flame, Users, Volume2 } from 'lucide-react';

interface DiscoverScreenProps {
  onOpenPlayer: (story: Story, episode: Episode) => void;
}

export const DiscoverScreen: React.FC<DiscoverScreenProps> = ({ onOpenPlayer }) => {
  const { stories } = useApp();
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedGenre, setSelectedGenre] = useState<string>('All');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('All');
  const [playingSonic, setPlayingSonic] = useState<boolean>(false);

  const genres = ['All', 'Dynasty & Thriller', 'Crime & Action', 'Romance & Drama', 'Comedy', 'Afrofuturism'];
  const languages = ['All', 'isiZulu', 'isiXhosa', 'Afrikaans', 'Sesotho', 'English', 'Yoruba', 'Swahili', 'Pidgin', 'French'];

  const filteredStories = stories.filter((story) => {
    const matchesSearch =
      story.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      story.synopsis.toLowerCase().includes(searchQuery.toLowerCase()) ||
      story.creator_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      story.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesGenre =
      selectedGenre === 'All' ||
      story.genre.toLowerCase().includes(selectedGenre.toLowerCase());

    const matchesLanguage =
      selectedLanguage === 'All' ||
      story.available_languages.some((l) => l.toLowerCase() === selectedLanguage.toLowerCase());

    return matchesSearch && matchesGenre && matchesLanguage;
  });

  const handlePlaySonicIdentity = () => {
    setPlayingSonic(true);
    // Audio synthesis or visual chime
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(329.63, audioCtx.currentTime); // E4
    osc.frequency.exponentialRampToValueAtTime(659.25, audioCtx.currentTime + 0.4); // E5
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 1.2);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 1.2);

    setTimeout(() => setPlayingSonic(false), 1200);
  };

  return (
    <div className="space-y-6 pb-24 max-w-5xl mx-auto">
      {/* Brand Essence Header Card */}
      <div className="relative rounded-[7px] p-6 bg-gradient-to-br from-welele-surface-2 via-welele-surface to-[#1F171A] border border-white/10 shadow-2xl overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-[#FFA000]/15 via-[#FF6B00]/10 to-[#E6007A]/15 rounded-circle blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
          <div className="space-y-2 max-w-xl">
            <WeleleLogo variant="full" size="md" />

            <h2 className="text-xl sm:text-2xl font-black text-white font-sans mt-3 leading-tight">
              WE CONNECT. WE TELL STORIES. <span className="text-gradient-warm">WE MOVE HEARTS.</span>
            </h2>

            <p className="text-xs text-welele-muted leading-relaxed">
              We celebrate African stories and voices. We champion creators. We build communities. We believe every story has the power to bring us closer together.
            </p>

            {/* Core Brand Value Badges */}
            <div className="flex flex-wrap gap-2 pt-2">
              {[
                { label: 'Connection', icon: '👥' },
                { label: 'Emotion', icon: '❤️' },
                { label: 'Story', icon: '🎬' },
                { label: 'Warmth', icon: '🔥' },
                { label: 'Wonder', icon: '✨' },
              ].map((val) => (
                <span
                  key={val.label}
                  className="px-2.5 py-1 rounded-[7px] text-[10px] font-bold bg-white/5 border border-white/10 text-white flex items-center gap-1.5"
                >
                  <span>{val.icon}</span>
                  <span>{val.label}</span>
                </span>
              ))}
            </div>
          </div>

          {/* Sonic Identity Audio Button */}
          <div className="shrink-0 p-4 rounded-[7px] bg-black/40 border border-white/10 text-center space-y-2 w-full md:w-auto">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-[#FFA000] block">
              SONIC IDENTITY
            </span>
            <button
              onClick={handlePlaySonicIdentity}
              className={`w-full px-4 py-2.5 rounded-[7px] text-xs font-black flex items-center justify-center gap-2 transition-all ${
                playingSonic
                  ? 'bg-gradient-welele text-white scale-105 shadow-lg shadow-orange-500/30'
                  : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
            >
              <Volume2 className={`w-4 h-4 ${playingSonic ? 'animate-bounce' : ''}`} />
              <span>{playingSonic ? '"Weleleeee..." 🎶' : 'Hear "Welele..." Sound'}</span>
            </button>
            <p className="text-[9px] text-welele-muted">Warm African Instrumentation</p>
          </div>
        </div>
      </div>

      {/* Search Header */}
      <div className="relative">
        <Search className="w-4 h-4 text-welele-muted absolute left-3.5 top-3.5" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search microdramas, African creators, Mzansi stories..."
          className="w-full bg-welele-surface-2 pl-10 pr-4 py-3 rounded-[7px] border border-white/10 text-xs text-white placeholder-welele-muted focus:outline-none focus:border-welele-orange shadow-inner"
        />
      </div>

      {/* African Language Selector Filter Pills */}
      <div>
        <div className="flex items-center gap-1.5 text-xs text-welele-muted mb-2 font-semibold">
          <Globe className="w-3.5 h-3.5 text-welele-orange" />
          <span>African Language / Subtitles:</span>
        </div>
        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1">
          {languages.map((lang) => (
            <button
              key={lang}
              onClick={() => setSelectedLanguage(lang)}
              className={`px-3 py-1.5 rounded-[7px] text-xs font-semibold whitespace-nowrap transition-all ${
                selectedLanguage === lang
                  ? 'bg-gradient-welele text-white font-bold shadow'
                  : 'bg-welele-surface-2 text-welele-muted hover:text-white border border-white/5'
              }`}
            >
              {lang}
            </button>
          ))}
        </div>
      </div>

      {/* Genre Filter Pills */}
      <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1">
        {genres.map((genre) => (
          <button
            key={genre}
            onClick={() => setSelectedGenre(genre)}
            className={`px-3.5 py-1.5 rounded-[7px] text-xs font-semibold whitespace-nowrap transition-all ${
              selectedGenre === genre
                ? 'bg-gradient-welele text-white shadow-md'
                : 'bg-welele-surface-2 text-welele-muted hover:text-white border border-white/5'
            }`}
          >
            {genre}
          </button>
        ))}
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between text-xs text-welele-muted">
        <span>Showing {filteredStories.length} storytelling series</span>
        {(selectedGenre !== 'All' || selectedLanguage !== 'All' || searchQuery) && (
          <button
            onClick={() => {
              setSelectedGenre('All');
              setSelectedLanguage('All');
              setSearchQuery('');
            }}
            className="text-welele-orange hover:underline font-medium"
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Stories Grid */}
      {filteredStories.length === 0 ? (
        <div className="text-center py-16 bg-welele-surface-2/40 rounded-[7px] border border-white/5">
          <Sparkles className="w-8 h-8 text-welele-orange mx-auto mb-2 opacity-60" />
          <h4 className="text-sm font-bold text-white">No stories match your filters</h4>
          <p className="text-xs text-welele-muted mt-1">Try selecting another genre or African language.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3.5">
          {filteredStories.map((story) => (
            <div
              key={story.id}
              onClick={() => {
                if (story.episodes.length > 0) {
                  onOpenPlayer(story, story.episodes[0]);
                }
              }}
              className="group relative rounded-[7px] overflow-hidden bg-welele-surface-2 border border-white/5 cursor-pointer hover:border-welele-orange/50 transition-all hover:shadow-xl"
            >
              <div className="aspect-[9/16] w-full relative">
                <img
                  src={story.vertical_poster}
                  alt={story.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-welele-black via-transparent to-transparent opacity-90" />

                <div className="absolute top-2.5 left-2.5">
                  <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-bold bg-black/70 backdrop-blur-md text-welele-orange border border-white/10">
                    {story.genre}
                  </span>
                </div>

                <div className="absolute bottom-2.5 left-2.5 right-2.5">
                  <h3 className="text-xs font-bold text-white truncate group-hover:text-welele-orange">
                    {story.title}
                  </h3>
                  <p className="text-[10px] text-welele-muted truncate">{story.creator_name}</p>
                  <div className="flex items-center justify-between mt-1 text-[9px] text-welele-gold font-bold">
                    <span>★ {story.rating}</span>
                    <span>{story.episodes?.length || story.total_episodes || 1} eps</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
