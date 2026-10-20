import React, { useState, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { creatorApi, storageApi } from '../../services/api';
import { X, Sparkles, Check, PlusCircle, UploadCloud, Image as ImageIcon, CheckCircle2 } from 'lucide-react';

interface CreateShowModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newSeriesId: string) => void;
}

interface CreationSuccessData {
  seriesId: string;
  title: string;
  genre: string;
  status: string;
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
  
  // Poster
  const [verticalPoster, setVerticalPoster] = useState<string>(
    'https://images.unsplash.com/photo-1509967419530-da38b4704bc6?auto=format&fit=crop&w=600&q=80'
  );
  
  // 16:9 Hero Banner
  const [coverBanner, setCoverBanner] = useState<string>(
    'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80'
  );

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isUploadingPoster, setIsUploadingPoster] = useState<boolean>(false);
  const [isUploadingBanner, setIsUploadingBanner] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [creationSuccess, setCreationSuccess] = useState<CreationSuccessData | null>(null);
  const posterInputRef = useRef<HTMLInputElement | null>(null);
  const bannerInputRef = useRef<HTMLInputElement | null>(null);

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

  const sampleBanners = [
    'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1514306191717-452ec28c7814?auto=format&fit=crop&w=1200&q=80'
  ];

  const handleCustomPoster = async (file: File) => {
    setIsUploadingPoster(true);
    setErrorMessage(null);
    try {
      const res = await storageApi.uploadArtwork(file, undefined, 'poster');
      const cdnUrl = res?.public_cdn_url;
      if (!cdnUrl || cdnUrl.startsWith('blob:') || cdnUrl.includes('X-Amz-Expires') || cdnUrl.includes('Expires=')) {
        throw new Error('Upload succeeded but server did not return a durable, non-expiring CDN URL');
      }
      setVerticalPoster(cdnUrl);
    } catch (err: any) {
      console.error('Failed to upload custom poster:', err);
      const isTimeout = err?.code === 'ECONNABORTED' || err?.message?.includes('timeout');
      const msg = isTimeout
        ? 'Upload timed out after 60s. Please check your network and retry.'
        : err?.response?.data?.detail || err?.message || 'Failed to upload poster to storage.';
      setErrorMessage(`Poster upload error: ${msg}`);
    } finally {
      setIsUploadingPoster(false);
    }
  };

  const handleCustomBanner = async (file: File) => {
    setIsUploadingBanner(true);
    setErrorMessage(null);
    try {
      const res = await storageApi.uploadArtwork(file, undefined, 'banner');
      const cdnUrl = res?.public_cdn_url;
      if (!cdnUrl || cdnUrl.startsWith('blob:') || cdnUrl.includes('X-Amz-Expires') || cdnUrl.includes('Expires=')) {
        throw new Error('Upload succeeded but server did not return a durable, non-expiring CDN URL');
      }
      setCoverBanner(cdnUrl);
    } catch (err: any) {
      console.error('Failed to upload custom banner:', err);
      const isTimeout = err?.code === 'ECONNABORTED' || err?.message?.includes('timeout');
      const msg = isTimeout
        ? 'Upload timed out after 60s. Please check your network and retry.'
        : err?.response?.data?.detail || err?.message || 'Failed to upload banner to storage.';
      setErrorMessage(`Banner upload error: ${msg}`);
    } finally {
      setIsUploadingBanner(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    if (verticalPoster.startsWith('blob:') || coverBanner.startsWith('blob:')) {
      setErrorMessage('Local temporary (blob:) URLs cannot be saved as series artwork. Please select or upload valid artwork.');
      return;
    }
    if (
      verticalPoster.includes('X-Amz-Expires') ||
      coverBanner.includes('X-Amz-Expires') ||
      verticalPoster.includes('Expires=') ||
      coverBanner.includes('Expires=')
    ) {
      setErrorMessage('Presigned expiring URLs cannot be saved as series artwork. Please upload artwork to obtain permanent CDN URLs.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
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

      const createdId = res?.story?.id || res?.series?.id || res?.id;
      if (!createdId) {
        throw new Error('Server did not return a valid series ID');
      }

      await refreshStories();
      setCreationSuccess({
        seriesId: createdId,
        title: title.trim(),
        genre,
        status: 'Draft / Unpublished',
      });
    } catch (err: any) {
      console.error('Failed to create show:', err);
      const detail = err?.response?.data?.detail || err?.message || 'Failed to create show. Please check connection and try again.';
      setErrorMessage(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setCreationSuccess(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0F1014] border border-white/10 rounded-[7px] max-w-2xl w-full p-6 shadow-2xl overflow-hidden animate-fade-in text-white space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-[7px] bg-gradient-to-tr from-[#E6007A] to-[#FF2A6D] flex items-center justify-center text-white shadow">
              <PlusCircle className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-black text-white uppercase tracking-wider">
                {creationSuccess ? 'Show Created' : 'Create New Show'}
              </h2>
              <p className="text-xs text-welele-muted">
                {creationSuccess
                  ? 'Registration confirmed in your Creator Studio workspace.'
                  : 'Set title, story premise, and upload your custom poster & 16:9 hero banner.'}
              </p>
            </div>
          </div>

          <button
            onClick={handleClose}
            className="w-8 h-8 rounded-[7px] bg-white/5 hover:bg-white/10 text-white/70 hover:text-white flex items-center justify-center transition-all"
            aria-label="Close Modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {errorMessage && (
          <div className="p-3 bg-red-500/15 border border-red-500/40 rounded-[7px] text-xs text-red-300">
            {errorMessage}
          </div>
        )}

        {/* Confirmation Screen */}
        {creationSuccess ? (
          <div className="py-6 px-4 text-center space-y-5 animate-fade-in">
            <div className="w-14 h-14 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 mx-auto flex items-center justify-center shadow-lg shadow-emerald-500/10">
              <CheckCircle2 className="w-8 h-8 stroke-[2.5]" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-lg font-black text-white tracking-wide uppercase">
                Show Successfully Registered
              </h3>
              <p className="text-xs text-welele-muted max-w-md mx-auto">
                <span className="text-white font-bold">"{creationSuccess.title}"</span> has been created in your creator workspace and is ready for episode production.
              </p>
            </div>

            <div className="bg-[#14151B] border border-white/10 rounded-[7px] p-4 text-left space-y-2 max-w-md mx-auto font-mono text-xs">
              <div className="flex justify-between items-center pb-1.5 border-b border-white/5">
                <span className="text-welele-muted font-sans">Series ID</span>
                <span className="text-welele-gold font-bold select-all">{creationSuccess.seriesId}</span>
              </div>
              <div className="flex justify-between items-center pb-1.5 border-b border-white/5">
                <span className="text-welele-muted font-sans">Genre</span>
                <span className="text-white font-sans">{creationSuccess.genre}</span>
              </div>
              <div className="flex justify-between items-center pb-1.5 border-b border-white/5">
                <span className="text-welele-muted font-sans">Lifecycle State</span>
                <span className="text-amber-400 font-sans font-bold flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                  {creationSuccess.status}
                </span>
              </div>
              <div className="flex justify-between items-center text-emerald-400 font-sans">
                <span className="text-welele-muted">Next Action</span>
                <span>Upload Episode 1 in Command Room</span>
              </div>
            </div>

            <div className="pt-3 flex items-center justify-center gap-3">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 rounded-[7px] text-xs font-bold text-welele-muted hover:text-white bg-white/5 hover:bg-white/10 transition-colors"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  const targetId = creationSuccess.seriesId;
                  handleClose();
                  onSuccess(targetId);
                }}
                className="px-6 py-2.5 rounded-[7px] text-xs font-bold bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white hover:opacity-95 shadow-lg shadow-pink-500/25 transition-all flex items-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                <span>Open in Command Room</span>
              </button>
            </div>
          </div>
        ) : (
          /* Creation Form */
          <form onSubmit={handleSubmit} className="space-y-4 max-h-[75vh] overflow-y-auto pr-1">
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
                spellCheck={true}
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
                spellCheck={true}
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
                spellCheck={true}
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

            {/* DUAL ARTWORK UPLOAD ZONES */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-white/10">
              {/* 1. Poster Key Art Dropzone */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-white flex items-center justify-between">
                  <span>Poster (Cover)</span>
                  <span className="text-[10px] text-pink-400 font-mono">1080 × 1920</span>
                </label>

                <div
                  onClick={() => !isUploadingPoster && posterInputRef.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (!isUploadingPoster && e.dataTransfer.files && e.dataTransfer.files[0]) {
                      handleCustomPoster(e.dataTransfer.files[0]);
                    }
                  }}
                  className={`w-full aspect-[9/16] max-h-56 rounded-[7px] border-2 border-dashed ${
                    isUploadingPoster ? 'border-pink-500/50 cursor-wait' : 'border-white/20 hover:border-pink-500 cursor-pointer'
                  } bg-[#14151B] relative overflow-hidden group flex flex-col items-center justify-center text-center p-3 transition-all`}
                >
                  <input
                    type="file"
                    ref={posterInputRef}
                    disabled={isUploadingPoster}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleCustomPoster(e.target.files[0]);
                      }
                    }}
                    accept="image/*"
                    className="hidden"
                  />

                  {isUploadingPoster ? (
                    <div className="space-y-2 text-center">
                      <div className="w-6 h-6 border-2 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto" />
                      <p className="text-[11px] text-pink-300 font-bold">Uploading to R2...</p>
                    </div>
                  ) : verticalPoster ? (
                    <>
                      <img
                        src={verticalPoster}
                        alt="Vertical Poster Preview"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                      />
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-2 text-xs font-bold text-white">
                        <UploadCloud className="w-5 h-5 mb-1 text-pink-400" />
                        <span>Click or Drop to Replace</span>
                      </div>
                    </>
                  ) : (
                    <div className="space-y-1">
                      <UploadCloud className="w-6 h-6 mx-auto text-pink-400" />
                      <p className="text-xs font-bold text-white">Drop Portrait Poster</p>
                      <p className="text-[10px] text-welele-muted">or click to browse</p>
                    </div>
                  )}
                </div>

                {/* Sample Quick Pick */}
                <div className="flex items-center gap-1.5 overflow-x-auto pt-1">
                  {samplePosters.map((poster, idx) => (
                    <button
                      type="button"
                      key={idx}
                      onClick={() => setVerticalPoster(poster)}
                      className={`w-10 h-14 rounded-[5px] overflow-hidden border transition-all shrink-0 ${
                        verticalPoster === poster ? 'border-pink-500 scale-105' : 'border-white/10 opacity-50 hover:opacity-100'
                      }`}
                    >
                      <img src={poster} alt="Sample" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              </div>

              {/* 2. 16:9 Horizontal Hero Banner Dropzone */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-white flex items-center justify-between">
                  <span>16:9 Hero Banner (Backdrop)</span>
                  <span className="text-[10px] text-welele-gold font-mono">1920 × 1080</span>
                </label>

                <div
                  onClick={() => !isUploadingBanner && bannerInputRef.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (!isUploadingBanner && e.dataTransfer.files && e.dataTransfer.files[0]) {
                      handleCustomBanner(e.dataTransfer.files[0]);
                    }
                  }}
                  className={`w-full aspect-video max-h-56 rounded-[7px] border-2 border-dashed ${
                    isUploadingBanner ? 'border-welele-gold/50 cursor-wait' : 'border-white/20 hover:border-welele-gold cursor-pointer'
                  } bg-[#14151B] relative overflow-hidden group flex flex-col items-center justify-center text-center p-3 transition-all`}
                >
                  <input
                    type="file"
                    ref={bannerInputRef}
                    disabled={isUploadingBanner}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleCustomBanner(e.target.files[0]);
                      }
                    }}
                    accept="image/*"
                    className="hidden"
                  />

                  {isUploadingBanner ? (
                    <div className="space-y-2 text-center">
                      <div className="w-6 h-6 border-2 border-welele-gold border-t-transparent rounded-full animate-spin mx-auto" />
                      <p className="text-[11px] text-yellow-300 font-bold">Uploading to R2...</p>
                    </div>
                  ) : coverBanner ? (
                    <>
                      <img
                        src={coverBanner}
                        alt="Hero Banner Preview"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                      />
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-2 text-xs font-bold text-white">
                        <UploadCloud className="w-5 h-5 mb-1 text-welele-gold" />
                        <span>Click or Drop to Replace</span>
                      </div>
                    </>
                  ) : (
                    <div className="space-y-1">
                      <UploadCloud className="w-6 h-6 mx-auto text-welele-gold" />
                      <p className="text-xs font-bold text-white">Drop Landscape Banner</p>
                      <p className="text-[10px] text-welele-muted">or click to browse</p>
                    </div>
                  )}
                </div>

                {/* Sample Quick Pick */}
                <div className="flex items-center gap-1.5 overflow-x-auto pt-1">
                  {sampleBanners.map((banner, idx) => (
                    <button
                      type="button"
                      key={idx}
                      onClick={() => setCoverBanner(banner)}
                      className={`w-16 h-10 rounded-[5px] overflow-hidden border transition-all shrink-0 ${
                        coverBanner === banner ? 'border-welele-gold scale-105' : 'border-white/10 opacity-50 hover:opacity-100'
                      }`}
                    >
                      <img src={banner} alt="Sample Banner" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 rounded-[7px] text-xs font-bold text-welele-muted hover:text-white bg-white/5 hover:bg-white/10 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || isUploadingPoster || isUploadingBanner || !title.trim()}
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
        )}
      </div>
    </div>
  );
};
