import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { creatorApi } from '../../services/api';
import { X, Sparkles, Check, PlusCircle } from 'lucide-react';

interface CreateShowModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newSeriesId: string) => void;
}

export const CreateShowModal: React.FC<CreateShowModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { refreshStories, user } = useApp();

  const [title, setTitle] = useState<string>('');
  const [tagline, setTagline] = useState<string>('');
  const [synopsis, setSynopsis] = useState<string>('');
  const [genre, setGenre] = useState<string>('Crime & Dynasty');
  const [language, setLanguage] = useState<string>('English / isiZulu');
  const [verticalPoster, setVerticalPoster] = useState<string>(
    'https://images.unsplash.com/photo-1509967419530-da38b4704bc6?auto=format&fit=crop&w=600&q=80'
  );
  const [coverBanner, setCoverBanner] = useState<string>(
    'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80'
  );
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  if (!isOpen) return null;

  const genres = [
    'Crime & Dynasty',
    'High Society Romance',
    'Supernatural & Ancestral',
    'Street Hustle & Rise',
    'Revenge & Thriller',
    'Township Comedy'
  ];

  const languages = [
    'English / isiZulu',
    'isiZulu (South Africa)',
    'isiXhosa (South Africa)',
    'Yoruba / English (Nigeria)',
    'Kiswahili (East Africa)',
    'Nigerian Pidgin',
    'Multilingual African'
  ];

  const samplePosters = [
    'https://images.unsplash.com/photo-1509967419530-da38b4704bc6?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=600&q=80'
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSubmitting(true);
    try {
      const res = await creatorApi.createSeries({
        title: title.trim(),
        tagline: tagline.trim() || 'A Welele Microdrama Series',
        synopsis: synopsis.trim() || 'Experience the drama, betrayal, and power struggle.',
        cover_image: coverBanner,
        vertical_poster: verticalPoster,
        genre,
        language,
        available_languages: ['English', 'isiZulu', 'Yoruba', 'Kiswahili'],
        tags: ['#WeleleOriginal', `#${genre.replace(/\s+/g, '')}`],
        creator_id: user?.creator_id || 'creator_zola',
        coin_price_per_episode: 5,
      });

      await refreshStories();
      const createdId = res?.series?.id || res?.id || 'story_new';
      onSuccess(createdId);
      onClose();
    } catch (err) {
      console.error('Failed to create show:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0F1014] border border-white/10 rounded-[7px] max-w-xl w-full p-6 shadow-2xl overflow-hidden animate-fade-in text-white space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-[7px] bg-gradient-to-tr from-[#E6007A] to-[#FF2A6D] flex items-center justify-center text-white shadow">
              <PlusCircle className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-black text-white uppercase tracking-wider">
                Create New Show
              </h2>
              <p className="text-xs text-welele-muted">
                Establish the title, genre, and look for your new microdrama series.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-[7px] bg-white/5 hover:bg-white/10 text-white/70 hover:text-white flex items-center justify-center transition-all"
            aria-label="Close Modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Show Title */}
          <div>
            <label className="text-xs font-bold text-white block mb-1">
              Show Title <span className="text-pink-500">*</span>
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Crown of Kumasi, Lagos Nights, Blood Ties"
              className="w-full bg-[#14151B] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white placeholder:text-welele-muted focus:outline-none focus:border-pink-500 transition-colors"
            />
          </div>

          {/* Tagline / Hook */}
          <div>
            <label className="text-xs font-bold text-white block mb-1">
              Tagline
            </label>
            <input
              type="text"
              value={tagline}
              onChange={(e) => setTagline(e.target.value)}
              placeholder="e.g., In this kingdom, loyalty is paid in blood."
              className="w-full bg-[#14151B] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-xs text-white placeholder:text-welele-muted focus:outline-none focus:border-pink-500 transition-colors"
            />
          </div>

          {/* Synopsis */}
          <div>
            <label className="text-xs font-bold text-white block mb-1">
              Synopsis
            </label>
            <textarea
              rows={2}
              value={synopsis}
              onChange={(e) => setSynopsis(e.target.value)}
              placeholder="What is the central conflict and world of this show?"
              className="w-full bg-[#14151B] px-3.5 py-2 rounded-[7px] border border-white/10 text-xs text-white placeholder:text-welele-muted focus:outline-none focus:border-pink-500 transition-colors"
            />
          </div>

          {/* Genre & Language */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-bold text-white block mb-1">Genre</label>
              <select
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                className="w-full bg-[#14151B] px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-pink-500 cursor-pointer"
              >
                {genres.map((g) => (
                  <option key={g} value={g} className="bg-[#0F1014] text-white">
                    {g}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-white block mb-1">Primary Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-[#14151B] px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-pink-500 cursor-pointer"
              >
                {languages.map((l) => (
                  <option key={l} value={l} className="bg-[#0F1014] text-white">
                    {l}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Vertical Poster Selection */}
          <div>
            <label className="text-xs font-bold text-white block mb-1.5">
              9:16 Vertical Poster (Cover)
            </label>
            <div className="flex items-center gap-2.5 overflow-x-auto pb-1">
              {samplePosters.map((poster, idx) => (
                <button
                  type="button"
                  key={idx}
                  onClick={() => setVerticalPoster(poster)}
                  className={`w-14 h-20 rounded-[7px] overflow-hidden border-2 transition-all shrink-0 relative ${
                    verticalPoster === poster
                      ? 'border-[#E6007A] scale-105 shadow-md shadow-pink-500/30'
                      : 'border-white/10 opacity-60 hover:opacity-100'
                  }`}
                >
                  <img src={poster} alt="Poster Sample" className="w-full h-full object-cover" />
                  {verticalPoster === poster && (
                    <div className="absolute inset-0 bg-pink-600/30 flex items-center justify-center text-white">
                      <Check className="w-4 h-4" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-[7px] text-xs font-bold text-welele-muted hover:text-white bg-white/5 hover:bg-white/10 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim()}
              className="px-5 py-2 rounded-[7px] text-xs font-bold bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white hover:opacity-95 shadow-lg shadow-pink-500/20 disabled:opacity-50 transition-all flex items-center gap-1.5"
            >
              {isSubmitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Creating Show...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Create Show</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
