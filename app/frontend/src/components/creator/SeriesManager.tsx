import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { creatorApi } from '../../services/api';
import { PlusCircle, ArrowLeft, Video, Check } from 'lucide-react';

interface SeriesManagerProps {
  onBack: () => void;
  onNavigateToUpload: () => void;
}

export const SeriesManager: React.FC<SeriesManagerProps> = ({ onBack, onNavigateToUpload }) => {
  const { stories, refreshStories } = useApp();
  const [isCreatingNew, setIsCreatingNew] = useState<boolean>(false);
  const [title, setTitle] = useState<string>('');
  const [tagline, setTagline] = useState<string>('');
  const [synopsis, setSynopsis] = useState<string>('');
  const [coverImage, setCoverImage] = useState<string>(
    'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=1200&q=80'
  );
  const [verticalPoster, setVerticalPoster] = useState<string>(
    'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=600&q=80'
  );
  const [genre, setGenre] = useState<string>('Dynasty & Thriller');
  const [language, setLanguage] = useState<string>('English / Yoruba');
  const [coinPrice, setCoinPrice] = useState<number>(5);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleCreateSeries = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSubmitting(true);
    try {
      await creatorApi.createSeries({
        title,
        tagline,
        synopsis,
        cover_image: coverImage,
        vertical_poster: verticalPoster,
        genre,
        language,
        available_languages: ['English', 'Yoruba', 'Swahili', 'French'],
        tags: ['#WeleleMicrodrama', '#AfricanStory'],
        creator_id: 'creator_1',
        coin_price_per_episode: Number(coinPrice),
      });

      await refreshStories();
      setIsCreatingNew(false);
      setTitle('');
      setTagline('');
      setSynopsis('');
    } catch (err) {
      console.error('Failed to create series:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 pb-24 max-w-3xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            aria-label="Go Back"
            className="w-9 h-9 rounded-[7px] bg-welele-surface-2 hover:bg-welele-surface-3 flex items-center justify-center text-white border border-white/10"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-xl font-black text-white font-cinematic">Series Management</h2>
            <p className="text-xs text-welele-muted">Manage show titles, pricing & episode catalogues</p>
          </div>
        </div>

        {!isCreatingNew && (
          <button
            onClick={() => setIsCreatingNew(true)}
            className="px-4 py-2.5 rounded-[7px] bg-gradient-welele text-white font-bold text-xs shadow flex items-center gap-1.5"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Create New Series</span>
          </button>
        )}
      </div>

      {isCreatingNew ? (
        <form onSubmit={handleCreateSeries} className="p-6 rounded-[7px] bg-welele-surface-2 border border-white/10 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">New Series Setup</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-welele-muted block mb-1">Series Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Crown of Kumasi"
                className="w-full bg-welele-surface px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white"
                required
              />
            </div>
            <div>
              <label className="text-xs text-welele-muted block mb-1">Tagline</label>
              <input
                type="text"
                value={tagline}
                onChange={(e) => setTagline(e.target.value)}
                placeholder="One sentence hook..."
                className="w-full bg-welele-surface px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white"
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-welele-muted block mb-1">Full Story Synopsis</label>
            <textarea
              rows={3}
              value={synopsis}
              onChange={(e) => setSynopsis(e.target.value)}
              className="w-full bg-welele-surface px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-welele-muted block mb-1">Genre</label>
              <input
                type="text"
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                className="w-full bg-welele-surface px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs text-welele-muted block mb-1">Coin Price / Episode</label>
              <input
                type="number"
                value={coinPrice}
                onChange={(e) => setCoinPrice(Number(e.target.value))}
                className="w-full bg-welele-surface px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsCreatingNew(false)}
              className="px-4 py-2 rounded-[7px] bg-white/5 text-xs text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-[7px] bg-gradient-welele text-white text-xs font-bold shadow"
            >
              {isSubmitting ? 'Creating...' : 'Save Series'}
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-3">
          {stories.map((story) => (
            <div
              key={story.id}
              className="p-4 rounded-[7px] bg-welele-surface-2 border border-white/5 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <img
                  src={story.vertical_poster}
                  alt={story.title}
                  className="w-12 h-16 rounded-[7px] object-cover"
                />
                <div>
                  <h4 className="text-sm font-bold text-white">{story.title}</h4>
                  <p className="text-xs text-welele-muted">{story.genre} • {story.total_episodes} Episodes</p>
                  <span className="text-[10px] text-welele-gold font-bold">🪙 {story.coin_price_per_episode || 5} coins per locked episode</span>
                </div>
              </div>

              <button
                onClick={onNavigateToUpload}
                className="px-3 py-1.5 rounded-[7px] bg-welele-orange text-black font-bold text-xs"
              >
                + Add Episode
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
