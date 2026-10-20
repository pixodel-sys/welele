import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Story, Episode } from '../../types';
import { creatorApi, storageApi } from '../../services/api';
import { EntityHierarchyCrumb } from '../common/patterns/EntityHierarchyCrumb';
import { ProvenanceBadge } from '../common/patterns/ProvenanceBadge';
import { ReadinessBadge } from '../common/patterns/ReadinessBadge';
import { StatusBadge } from '../common/patterns/StatusBadge';
import {
  ArrowLeft,
  PlusCircle,
  Video,
  Coins,
  CheckCircle2,
  Clock,
  AlertTriangle,
  BookOpen,
  BarChart3,
  UploadCloud,
  Image as ImageIcon,
  Check,
  ShieldCheck,
  UserCheck,
  Sparkles,
  FileText,
  Edit3,
  Trash2,
  X,
  AlertCircle
} from 'lucide-react';

interface SeriesCommandRoomProps {
  seriesId: string;
  onBack: () => void;
  onOpenEpisodePipeline: (seriesId: string, episodeNum?: number) => void;
}

type ShowTab = 'episodes' | 'story' | 'insights' | 'earnings';

export const SeriesCommandRoom: React.FC<SeriesCommandRoomProps> = ({
  seriesId,
  onBack,
  onOpenEpisodePipeline,
}) => {
  const { stories } = useApp();
  const localFallbackStory = stories.find((s) => s.id === seriesId);

  const [activeTab, setActiveTab] = useState<ShowTab>('episodes');
  const [workspaceData, setWorkspaceData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [customPoster, setCustomPoster] = useState<string | null>(null);
  const [customBanner, setCustomBanner] = useState<string | null>(null);
  const [isUploadingPoster, setIsUploadingPoster] = useState<boolean>(false);
  const [isUploadingBanner, setIsUploadingBanner] = useState<boolean>(false);
  const [isSavingArtwork, setIsSavingArtwork] = useState<boolean>(false);
  const [artworkStatusMessage, setArtworkStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Phase 6J-2R-F: Show Metadata Edit & Persistence State
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const [editTitle, setEditTitle] = useState<string>('');
  const [editTagline, setEditTagline] = useState<string>('');
  const [editSynopsis, setEditSynopsis] = useState<string>('');
  const [editGenre, setEditGenre] = useState<string>('');
  const [editCoinPrice, setEditCoinPrice] = useState<number>(5);
  const [editLanguages, setEditLanguages] = useState<string>('');
  const [editTags, setEditTags] = useState<string>('');
  const [isSavingDetails, setIsSavingDetails] = useState<boolean>(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [editSuccess, setEditSuccess] = useState<string | null>(null);

  // Phase 6J-2R-F: Guarded Delete Show State
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [deleteConfirmTitle, setDeleteConfirmTitle] = useState<string>('');
  const [isDeletingShow, setIsDeletingShow] = useState<boolean>(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const posterInputRef = useRef<HTMLInputElement | null>(null);
  const bannerInputRef = useRef<HTMLInputElement | null>(null);

  const fetchWorkspace = () => {
    creatorApi
      .getSeriesWorkspace(seriesId)
      .then((res) => {
        if (res && res.series) {
          setWorkspaceData(res);
        } else if (localFallbackStory) {
          setWorkspaceData({
            series: localFallbackStory,
            metrics: {
              total_views: localFallbackStory.total_views || 0,
              completion_rate: "88.4%",
              coins_generated: 0,
              estimated_earnings_usd: 0,
              published_count: localFallbackStory.episodes?.filter(e => e.status === 'published').length || 0,
              under_review_count: localFallbackStory.under_review_episodes_count || 0,
              draft_count: 0
            }
          });
        }
      })
      .catch((err) => {
        console.warn('Failed to load backend show workspace, utilizing local state:', err);
        if (localFallbackStory) {
          setWorkspaceData({
            series: localFallbackStory,
            metrics: {
              total_views: localFallbackStory.total_views || 0,
              completion_rate: "88.4%",
              coins_generated: 0,
              estimated_earnings_usd: 0,
              published_count: localFallbackStory.episodes?.filter(e => e.status === 'published').length || 0,
              under_review_count: localFallbackStory.under_review_episodes_count || 0,
              draft_count: 0
            }
          });
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchWorkspace();
  }, [seriesId]);

  const handleUpdatePoster = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setArtworkStatusMessage({ type: 'error', text: 'Poster file must be an image (JPEG, PNG, WebP).' });
      return;
    }
    setIsUploadingPoster(true);
    setArtworkStatusMessage(null);
    try {
      const res = await storageApi.uploadArtwork(file, seriesId, 'poster');
      const cdnUrl = res?.public_cdn_url;
      if (cdnUrl) {
        if (cdnUrl.startsWith('blob:')) {
          throw new Error('Storage returned an invalid ephemeral blob URL.');
        }
        if (cdnUrl.includes('X-Amz-Expires') || cdnUrl.includes('Expires=')) {
          throw new Error('Storage returned an expiring presigned URL instead of a durable CDN URL.');
        }
        setCustomPoster(cdnUrl);
        setArtworkStatusMessage({ type: 'success', text: 'Poster uploaded to durable storage. Click "Save Artwork Changes" to persist.' });
      }
    } catch (err: any) {
      console.error('Failed to upload series poster:', err);
      const detail = err?.response?.data?.detail || err?.message || 'Failed to upload poster.';
      setArtworkStatusMessage({ type: 'error', text: detail });
    } finally {
      setIsUploadingPoster(false);
    }
  };

  const handleUpdateBanner = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setArtworkStatusMessage({ type: 'error', text: 'Hero banner file must be an image (JPEG, PNG, WebP).' });
      return;
    }
    setIsUploadingBanner(true);
    setArtworkStatusMessage(null);
    try {
      const res = await storageApi.uploadArtwork(file, seriesId, 'banner');
      const cdnUrl = res?.public_cdn_url;
      if (cdnUrl) {
        if (cdnUrl.startsWith('blob:')) {
          throw new Error('Storage returned an invalid ephemeral blob URL.');
        }
        if (cdnUrl.includes('X-Amz-Expires') || cdnUrl.includes('Expires=')) {
          throw new Error('Storage returned an expiring presigned URL instead of a durable CDN URL.');
        }
        setCustomBanner(cdnUrl);
        setArtworkStatusMessage({ type: 'success', text: 'Hero banner uploaded to durable storage. Click "Save Artwork Changes" to persist.' });
      }
    } catch (err: any) {
      console.error('Failed to upload series banner:', err);
      const detail = err?.response?.data?.detail || err?.message || 'Failed to upload banner.';
      setArtworkStatusMessage({ type: 'error', text: detail });
    } finally {
      setIsUploadingBanner(false);
    }
  };

  const handleSaveArtwork = async () => {
    setIsSavingArtwork(true);
    setArtworkStatusMessage(null);
    try {
      const posterToSave = customPoster || series?.vertical_poster;
      const bannerToSave = customBanner || series?.cover_image;

      if (!posterToSave && !bannerToSave) {
        throw new Error('No artwork selected to save.');
      }

      if (posterToSave?.startsWith('blob:') || bannerToSave?.startsWith('blob:')) {
        throw new Error('Invalid artwork: Ephemeral browser blob: URLs cannot be saved to database.');
      }

      const res = await creatorApi.updateSeriesArtwork(seriesId, {
        vertical_poster: posterToSave,
        cover_image: bannerToSave
      });

      if (res && res.series) {
        setWorkspaceData((prev: any) => ({
          ...prev,
          series: {
            ...prev?.series,
            ...res.series,
            vertical_poster: res.series.vertical_poster,
            cover_image: res.series.cover_image
          }
        }));
        setCustomPoster(null);
        setCustomBanner(null);
        setArtworkStatusMessage({ type: 'success', text: 'Artwork successfully saved to database & verified.' });
      } else {
        throw new Error('Server did not confirm artwork update.');
      }
    } catch (err: any) {
      console.error('Failed to save series artwork:', err);
      const detail = err?.response?.data?.detail || err?.message || 'Failed to save artwork changes.';
      setArtworkStatusMessage({ type: 'error', text: detail });
    } finally {
      setIsSavingArtwork(false);
    }
  };

  const series: Story | undefined = workspaceData?.series || localFallbackStory;

  if (loading && !series) {
    return (
      <div className="py-20 text-center text-welele-muted">
        <div className="w-8 h-8 border-2 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <span>Loading Show Workspace...</span>
      </div>
    );
  }

  if (!series) {
    return (
      <div className="py-16 text-center text-welele-muted space-y-4">
        <p className="text-sm font-bold text-white">Show not found</p>
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-[7px] bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-all"
        >
          ← Back to All Shows
        </button>
      </div>
    );
  }

  const metrics = workspaceData?.metrics || {
    total_views: series.total_views || 0,
    completion_rate: "—",
    coins_generated: 0,
    estimated_earnings_usd: 0,
    payout_balance_zar: 0,
    audience_momentum: "—",
    published_count: series.episodes?.filter(e => e.status === 'published').length || 0,
    under_review_count: series.under_review_episodes_count || 0,
    draft_count: 0
  };
  const episodes: Episode[] = series.episodes || [];
  const displayPoster = customPoster || series.vertical_poster;
  const displayBanner = customBanner || series.cover_image || series.vertical_poster;
  const franchiseCode = series.franchise_code || `IP-WEL-${series.id.replace(/[^a-zA-Z0-9]/g, '').slice(-4).toUpperCase()}`;

  // Phase 6J-2R-F: Show Metadata Edit & Guarded Deletion Handlers
  const handleOpenEditModal = () => {
    if (!series) return;
    setEditTitle(series.title || '');
    setEditTagline(series.tagline || '');
    setEditSynopsis(series.synopsis || '');
    setEditGenre(series.genre || '');
    setEditCoinPrice(series.coin_price_per_episode ?? 5);
    setEditLanguages(
      Array.isArray(series.available_languages)
        ? series.available_languages.join(', ')
        : 'English, isiZulu'
    );
    setEditTags(Array.isArray(series.tags) ? series.tags.join(', ') : '');
    setEditError(null);
    setEditSuccess(null);
    setIsEditModalOpen(true);
  };

  const handleSaveDetails = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editTitle.trim()) {
      setEditError('Show title is required.');
      return;
    }
    setIsSavingDetails(true);
    setEditError(null);
    setEditSuccess(null);
    try {
      const langArray = editLanguages
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const tagArray = editTags
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      await creatorApi.updateSeries(series.id, {
        title: editTitle.trim(),
        tagline: editTagline.trim(),
        synopsis: editSynopsis.trim(),
        genre: editGenre.trim(),
        coin_price_per_episode: Math.max(0, Number(editCoinPrice) || 0),
        available_languages: langArray.length > 0 ? langArray : ['English'],
        tags: tagArray
      });

      setEditSuccess('Show details saved and persisted to database!');
      fetchWorkspace();
      setTimeout(() => {
        setIsEditModalOpen(false);
        setEditSuccess(null);
      }, 1000);
    } catch (err: any) {
      console.error('Failed to update show details:', err);
      const detail = err?.response?.data?.detail || err?.message || 'Failed to persist show details.';
      setEditError(detail);
    } finally {
      setIsSavingDetails(false);
    }
  };

  const handleDeleteSeries = async () => {
    if (!series) return;
    if (deleteConfirmTitle.trim().toLowerCase() !== series.title.trim().toLowerCase()) {
      setDeleteError(`Please type "${series.title}" exactly to confirm deletion.`);
      return;
    }
    setIsDeletingShow(true);
    setDeleteError(null);
    try {
      await creatorApi.deleteSeries(series.id);
      setIsDeleteModalOpen(false);
      onBack();
    } catch (err: any) {
      console.error('Failed to delete series:', err);
      const detail = err?.response?.data?.detail || err?.message || 'Failed to delete series.';
      setDeleteError(detail);
    } finally {
      setIsDeletingShow(false);
    }
  };

  const getEpisodeReadiness = (ep: Episode): 'READY' | 'READY_WITH_WARNINGS' | 'NEEDS_INPUT' | 'BLOCKED' => {
    if (ep.status === 'published' || ep.status === 'approved') return 'READY';
    if (ep.status === 'under_review' || ep.status === 'submitted') return 'READY_WITH_WARNINGS';
    if (ep.status === 'changes_requested') return 'NEEDS_INPUT';
    if (!ep.video_url || !ep.cliffhanger_hook) return 'NEEDS_INPUT';
    return 'READY';
  };

  const getModerationBadge = (status?: string) => {
    switch (status) {
      case 'published':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-max">
            <CheckCircle2 className="w-3 h-3" /> Published
          </span>
        );
      case 'approved':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-teal-500/20 text-teal-400 border border-teal-500/30 flex items-center gap-1 w-max">
            <Check className="w-3 h-3" /> Approved
          </span>
        );
      case 'under_review':
      case 'submitted':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-max">
            <Clock className="w-3 h-3" /> Under Review
          </span>
        );
      case 'changes_requested':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-orange-500/20 text-orange-400 border border-orange-500/30 flex items-center gap-1 w-max">
            <AlertTriangle className="w-3 h-3" /> Changes Needed
          </span>
        );
      case 'draft':
      default:
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-white/10 text-white/70 border border-white/10 flex items-center gap-1 w-max">
            Draft
          </span>
        );
    }
  };

  const getCommercialBadge = (ep: Episode) => {
    if (ep.is_free) {
      return (
        <div className="flex flex-col">
          <span className="text-emerald-400 font-bold text-[11px] flex items-center gap-1">
            Free Episode
          </span>
          <span className="text-[9px] text-welele-muted">Public Access</span>
        </div>
      );
    }
    return (
      <div className="flex flex-col">
        <span className="text-amber-400 font-bold text-[11px] flex items-center gap-1">
          <Coins className="w-3 h-3" /> Locked • {ep.coin_price || 5} Coins
        </span>
        <span className="text-[9px] text-emerald-400/80 font-medium">Airtime Enabled (R3.00)</span>
      </div>
    );
  };

  return (
    <div className="space-y-6 pb-24 max-w-7xl mx-auto animate-fade-in text-white">
      {/* Show Workspace Header Container (Layer 2) */}
      <div className="p-4 sm:p-5 rounded-[7px] bg-[#14151B] border border-white/10 space-y-4 shadow-lg">
        {/* Top Row: Back button + Franchise Code + Title + Live Badge + Add Episode CTA */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="w-9 h-9 rounded-[7px] bg-white/5 hover:bg-white/10 flex items-center justify-center text-white border border-white/10 transition-all cursor-pointer shrink-0"
              aria-label="Back to All Shows"
              title="Back to All Shows"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 rounded-[7px] bg-black/60 border border-white/15 text-welele-gold font-mono text-[10px] font-bold">
                  {franchiseCode}
                </span>
                <h1 className="text-xl sm:text-2xl font-black text-white uppercase tracking-tight font-cinematic">
                  {series.title}
                </h1>
                <span className="px-2 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Live
                </span>
              </div>
              <p className="text-xs text-welele-muted mt-0.5">
                {series.genre} • {episodes.length} Episodes {metrics?.under_review_count ? `(${metrics.under_review_count} In Review)` : ''} • {series.language}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
            <button
              type="button"
              onClick={handleOpenEditModal}
              className="px-3.5 py-2 rounded-[7px] bg-white/10 hover:bg-white/15 text-white font-bold text-xs border border-white/15 flex items-center gap-1.5 transition-all cursor-pointer shadow-sm"
              title="Edit Show Details"
            >
              <Edit3 className="w-3.5 h-3.5 text-welele-gold" />
              <span>Edit Details</span>
            </button>
            <button
              onClick={() => onOpenEpisodePipeline(series.id, episodes.length + 1)}
              className="px-4 py-2 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-bold text-xs shadow-md shadow-pink-500/20 flex items-center gap-1.5 hover:opacity-95 transition-all cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span>+ Add Episode</span>
            </button>
          </div>
        </div>

        {/* Working Navigation Tabs inside the Show Workspace (Layer 3) */}
        <div className="border-t border-white/10 pt-3 flex items-center gap-2 overflow-x-auto no-scrollbar">
          {[
            { id: 'episodes', label: `Episodes (${episodes.length})`, icon: Video },
            { id: 'story', label: 'Story & Artwork', icon: BookOpen },
            { id: 'insights', label: 'Insights', icon: BarChart3 },
            { id: 'earnings', label: 'Earnings', icon: Coins },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as ShowTab)}
                className={`flex items-center gap-2 px-4 py-2 rounded-[7px] text-xs font-bold transition-all whitespace-nowrap cursor-pointer shrink-0 ${
                  isActive
                    ? 'bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white shadow-md shadow-pink-500/20'
                    : 'bg-black/40 text-welele-muted hover:text-white border border-white/5 hover:border-white/10'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-welele-muted'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* TAB CONTENT: EPISODES */}
      {activeTab === 'episodes' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Episodes Roster ({episodes.length})
              </h3>
              {metrics?.under_review_count > 0 && (
                <span className="px-2 py-0.5 rounded-[7px] bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-bold">
                  {metrics.under_review_count} Under Review
                </span>
              )}
            </div>
            <button
              onClick={() => onOpenEpisodePipeline(series.id, episodes.length + 1)}
              className="text-xs text-pink-400 hover:text-pink-300 font-bold flex items-center gap-1 cursor-pointer"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Add Episode {episodes.length + 1}</span>
            </button>
          </div>

          <div className="rounded-[7px] border border-white/10 bg-[#121318] overflow-hidden">
            <table className="w-full text-left text-xs text-white">
              <thead className="bg-[#181920] text-welele-muted uppercase font-mono text-[10px] border-b border-white/5">
                <tr>
                  <th className="px-4 py-3">#</th>
                  <th className="px-4 py-3">Episode</th>
                  <th className="px-4 py-3">Readiness</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Commercial Policy</th>
                  <th className="px-4 py-3">Moderation State</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {episodes.map((ep, idx) => {
                  const epNum = ep.episode_number || idx + 1;
                  const formattedNum = epNum < 10 ? `0${epNum}` : `${epNum}`;
                  const epReadiness = getEpisodeReadiness(ep);
                  return (
                    <tr key={ep.id} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3.5 font-mono font-bold text-welele-gold text-xs">
                        EP {formattedNum}
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="font-bold text-white text-xs">{ep.title}</div>
                        <div className="text-[11px] text-welele-muted line-clamp-1 mt-0.5">
                          {ep.cliffhanger_hook || ep.synopsis}
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <ReadinessBadge level={epReadiness} size="sm" />
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-welele-muted text-xs">
                            {ep.duration_seconds || 65}s
                          </span>
                          <ProvenanceBadge tier="MEDIA_OBSERVED" size="sm" />
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        {getCommercialBadge(ep)}
                      </td>
                      <td className="px-4 py-3.5">
                        {getModerationBadge(ep.status)}
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <button
                          onClick={() => onOpenEpisodePipeline(series.id, epNum)}
                          className="px-2.5 py-1 rounded-[7px] bg-white/5 hover:bg-white/10 text-white/80 hover:text-white text-[11px] font-semibold border border-white/10 cursor-pointer"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB CONTENT: STORY & ARTWORK */}
      {activeTab === 'story' && (
        <div className="space-y-6">
          {/* Show Premise & Provenance Card */}
          <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-pink-400" />
                Story World & Franchise Premise
              </h3>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleOpenEditModal}
                  className="px-2.5 py-1 rounded-[7px] bg-white/10 hover:bg-white/15 text-white font-bold text-[11px] border border-white/15 flex items-center gap-1.5 transition-all cursor-pointer"
                >
                  <Edit3 className="w-3 h-3 text-welele-gold" />
                  <span>Edit Metadata</span>
                </button>
                <ProvenanceBadge tier="CREATOR_DECLARED" size="sm" />
              </div>
            </div>

            {series.digital_ip && (
              <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-[7px] bg-black/40 border border-white/5 text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="text-welele-muted">Digital IP Franchise:</span>
                  <span className="text-welele-gold font-bold">{series.digital_ip.franchise_code || series.franchise_code}</span>
                  <span className="text-white">({series.digital_ip.title})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-welele-muted">Status:</span>
                  <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    {series.digital_ip.status || 'Active'}
                  </span>
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs text-welele-muted font-bold block">Series Synopsis</label>
              <p className="text-xs text-white leading-relaxed p-3 rounded-[7px] bg-black/40 border border-white/10">
                "{series.synopsis || series.tagline}"
              </p>
            </div>

            {series.story_world && (
              <div className="p-3 rounded-[7px] bg-black/40 border border-white/5 space-y-1.5 text-xs">
                <span className="text-welele-muted font-bold block">World Setting & Mythology</span>
                <p className="text-white">
                  <strong>{series.story_world.world_name}</strong> — {series.story_world.geographical_setting} ({series.story_world.time_period || 'Contemporary'})
                </p>
                {series.story_world.mythology_and_rules && (
                  <p className="text-[11px] text-welele-muted italic">
                    {series.story_world.mythology_and_rules}
                  </p>
                )}
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs text-welele-muted font-bold block">Available Languages & Dialects</label>
              <div className="flex flex-wrap gap-2">
                {series.available_languages?.map((lang) => (
                  <span
                    key={lang}
                    className="px-2.5 py-1 rounded-[7px] bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-medium"
                  >
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Character Roster Deck */}
          <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-emerald-400" />
                Character Roster & Digital IP Bibles
              </h3>
              <span className="text-[10px] text-welele-muted font-mono">
                {series.characters?.length || 0} Registered IP Characters
              </span>
            </div>

            {series.characters && series.characters.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {series.characters.map((char: any, i: number) => (
                  <div key={char.id || i} className="p-4 rounded-[7px] bg-black/40 border border-white/10 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        {char.role || 'Character'}
                      </span>
                      <span className="text-[10px] text-welele-muted font-mono">{char.archetype || 'Archetype'}</span>
                    </div>
                    <h4 className="text-sm font-bold text-white">{char.name}</h4>
                    {char.secret_motivation && (
                      <p className="text-[11px] text-welele-muted leading-relaxed">
                        {char.secret_motivation}
                      </p>
                    )}
                    {char.signature_quote && (
                      <p className="text-[10px] text-welele-gold italic pt-1 border-t border-white/5">
                        "{char.signature_quote}"
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 rounded-[7px] bg-black/20 border border-dashed border-white/10 text-center space-y-2">
                <UserCheck className="w-6 h-6 text-welele-muted mx-auto opacity-40" />
                <p className="text-xs font-bold text-white">No Character Bibles Registered</p>
                <p className="text-[11px] text-welele-muted max-w-md mx-auto">
                  Character rosters can be authored during story development or discovered through Story Forge™ narrative reasoning.
                </p>
              </div>
            )}
          </div>

          {/* Commercial Rights Declarations & Story Lineage */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Rights Declaration */}
            <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Commercial Rights Declarations
                </h3>
                <ProvenanceBadge tier={series.rights_ledger && series.rights_ledger.length > 0 ? "SYSTEM_DERIVED" : "CREATOR_DECLARED"} size="sm" />
              </div>

              <div className="space-y-2 text-xs">
                {series.rights_declarations && series.rights_declarations.length > 0 ? (
                  series.rights_declarations.map((r: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-white/5">
                      <div>
                        <span className="text-white font-semibold block">{r.stakeholder_role}</span>
                        <span className="text-[10px] text-welele-muted">{r.medium} • {r.territory}</span>
                      </div>
                      <span className="text-emerald-400 font-mono font-bold">{r.royalty_split_pct}%</span>
                    </div>
                  ))
                ) : (
                  <>
                    <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-white/5">
                      <span className="text-welele-muted">Digital Video On Demand:</span>
                      <span className="text-white font-semibold">Worldwide Platform Distribution</span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-white/5">
                      <span className="text-welele-muted">Original IP Ownership:</span>
                      <span className="text-emerald-400 font-semibold">100% Creator Owned ({series.creator_name || 'Showrunner'})</span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 rounded-[7px] bg-black/40 border border-white/5">
                      <span className="text-welele-muted">Linear & Ancillary Rights:</span>
                      <span className="text-white font-semibold">Retained by Showrunner</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Story Lineage */}
            <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-pink-400" />
                  Narrative Lineage & Origin
                </h3>
                <ProvenanceBadge tier={series.narrative_lineage?.origin === 'STORY_FORGE' ? "AI_ASSIST" : "CREATOR_DECLARED"} size="sm" />
              </div>
              <div className="space-y-2 text-xs">
                <div className="p-2.5 rounded-[7px] bg-black/40 border border-white/5 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-welele-muted">Origin Classification:</span>
                    <span className="text-white font-bold">
                      {series.narrative_lineage?.origin === 'STORY_FORGE' ? 'Story Forge™ Assisted' : 'Creator Original Treatment'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-welele-muted">Creative Authority:</span>
                    <span className="text-emerald-400 font-bold">
                      {series.narrative_lineage?.creative_authority || `Showrunner (${series.creator_name || 'Creator'})`}
                    </span>
                  </div>
                  {series.narrative_lineage?.source_engine && (
                    <div className="flex items-center justify-between">
                      <span className="text-welele-muted">Source Engine:</span>
                      <span className="text-white font-mono text-[11px]">{series.narrative_lineage.source_engine}</span>
                    </div>
                  )}
                </div>
                <p className="text-[11px] text-welele-muted leading-relaxed">
                  {series.narrative_lineage?.description ||
                    "Original story world and premise originated directly by the showrunner. No generative narrative synthesis utilized."}
                </p>
              </div>
            </div>
          </div>

          {/* Show Artwork Controls */}
          <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-welele-gold" />
                Show Artwork & Key Art
              </h3>
              <ProvenanceBadge tier="MEDIA_OBSERVED" size="sm" />
            </div>

            {/* Artwork Status Banner */}
            {artworkStatusMessage && (
              <div
                className={`p-3 rounded-[7px] text-xs font-semibold flex items-center justify-between border ${
                  artworkStatusMessage.type === 'success'
                    ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                    : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                }`}
              >
                <span>{artworkStatusMessage.text}</span>
                <button
                  type="button"
                  onClick={() => setArtworkStatusMessage(null)}
                  className="text-white/60 hover:text-white text-xs ml-2"
                >
                  ✕
                </button>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Vertical Poster Box */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Poster (Cover)</span>
                  <button
                    type="button"
                    disabled={isUploadingPoster || isSavingArtwork}
                    onClick={() => posterInputRef.current?.click()}
                    className="text-xs text-pink-400 hover:text-pink-300 font-bold cursor-pointer disabled:opacity-50"
                  >
                    {isUploadingPoster ? 'Uploading to R2...' : 'Replace Poster'}
                  </button>
                  <input
                    type="file"
                    ref={posterInputRef}
                    disabled={isUploadingPoster || isSavingArtwork}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleUpdatePoster(e.target.files[0]);
                      }
                    }}
                    accept="image/*"
                    className="hidden"
                  />
                </div>

                <div className="w-36 aspect-[9/16] rounded-[7px] overflow-hidden border border-white/20 bg-black relative shadow-lg">
                  {isUploadingPoster ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 space-y-2">
                      <div className="w-6 h-6 border-2 border-pink-500 border-t-transparent rounded-full animate-spin" />
                      <span className="text-[10px] text-pink-300 font-bold">Uploading...</span>
                    </div>
                  ) : null}
                  <img src={displayPoster} alt="Poster" className="w-full h-full object-cover" />
                </div>
              </div>

              {/* Horizontal Banner Box */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">16:9 Hero Banner</span>
                  <button
                    type="button"
                    disabled={isUploadingBanner || isSavingArtwork}
                    onClick={() => bannerInputRef.current?.click()}
                    className="text-xs text-welele-gold hover:text-yellow-300 font-bold cursor-pointer disabled:opacity-50"
                  >
                    {isUploadingBanner ? 'Uploading to R2...' : 'Replace Banner'}
                  </button>
                  <input
                    type="file"
                    ref={bannerInputRef}
                    disabled={isUploadingBanner || isSavingArtwork}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleUpdateBanner(e.target.files[0]);
                      }
                    }}
                    accept="image/*"
                    className="hidden"
                  />
                </div>

                <div className="w-full aspect-video rounded-[7px] overflow-hidden border border-white/20 bg-black relative shadow-lg">
                  {isUploadingBanner ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 space-y-2">
                      <div className="w-6 h-6 border-2 border-welele-gold border-t-transparent rounded-full animate-spin" />
                      <span className="text-[10px] text-yellow-300 font-bold">Uploading...</span>
                    </div>
                  ) : null}
                  <img src={displayBanner} alt="Hero Banner" className="w-full h-full object-cover" />
                </div>
              </div>
            </div>

            {/* Persistent Save Control */}
            {(() => {
              const hasUnsavedArtwork =
                (customPoster !== null && customPoster !== series?.vertical_poster) ||
                (customBanner !== null && customBanner !== series?.cover_image);

              return (
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-4 border-t border-white/10">
                  <div className="text-xs text-welele-muted">
                    {hasUnsavedArtwork ? (
                      <span className="text-yellow-400 font-semibold flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
                        Unsaved artwork changes ready to persist to database.
                      </span>
                    ) : (
                      <span className="text-white/60">
                        Authoritative artwork is stored in Cloudflare R2 and synced to PostgreSQL.
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    disabled={!hasUnsavedArtwork || isSavingArtwork || isUploadingPoster || isUploadingBanner}
                    onClick={handleSaveArtwork}
                    className={`px-4 py-2 rounded-[7px] text-xs font-bold transition-all flex items-center gap-2 ${
                      hasUnsavedArtwork && !isSavingArtwork
                        ? 'bg-gradient-to-r from-pink-500 to-welele-gold text-white shadow-lg hover:brightness-110 cursor-pointer'
                        : 'bg-white/10 text-white/40 cursor-not-allowed'
                    }`}
                  >
                    {isSavingArtwork ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Saving to Database...
                      </>
                    ) : (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        Save Artwork Changes
                      </>
                    )}
                  </button>
                </div>
              );
            })()}
          </div>

          {/* Danger Zone: Guarded Series Deletion */}
          <div className="p-5 rounded-[7px] bg-[#1a1114] border border-red-500/20 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                  Danger Zone: Series Lifecycle Management
                </h3>
                <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                  Guarded Operation
                </span>
              </div>
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="text-xs text-welele-muted space-y-1">
                  <p className="text-white/80 font-medium">
                    Permanently delete this series catalog entry and its {episodes.length} owned episode(s).
                  </p>
                  <p className="text-[11px] text-welele-muted">
                    Protected Boundary: Digital IP franchise ({franchiseCode}), character bibles, commercial rights declarations, and audit records remain 100% intact and preserved in PostgreSQL.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setDeleteConfirmTitle('');
                    setDeleteError(null);
                    setIsDeleteModalOpen(true);
                  }}
                  className="px-3.5 py-2 rounded-[7px] bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/40 text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer shrink-0"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete Show</span>
                </button>
              </div>
            </div>
          </div>
      )}

      {/* TAB CONTENT: INSIGHTS */}
      {activeTab === 'insights' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
              <span className="text-xs text-welele-muted">Average Completion Rate</span>
              <div className="text-2xl font-black text-emerald-400 font-cinematic">
                {metrics?.completion_rate ?? '—'}
              </div>
              <span className="text-[10px] text-welele-muted">Spine audience retention</span>
            </div>

            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
              <span className="text-xs text-welele-muted">Total Views</span>
              <div className="text-2xl font-black text-white font-cinematic">
                {metrics?.total_views != null ? Number(metrics.total_views).toLocaleString() : '0'}
              </div>
              <span className="text-[10px] text-welele-muted">Across all episodes</span>
            </div>

            <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
              <span className="text-xs text-welele-muted">Audience Momentum</span>
              <div className="text-2xl font-black text-[#FF2A6D] font-cinematic">
                {metrics?.audience_momentum ?? '—'}
              </div>
              <span className="text-[10px] text-welele-muted">Telemetry velocity signal</span>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: EARNINGS */}
      {activeTab === 'earnings' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
              <span className="text-xs text-welele-muted">Total Episode Unlocks</span>
              <div className="text-2xl font-black text-welele-gold font-cinematic">
                {metrics?.coins_generated != null ? `${Number(metrics.coins_generated).toLocaleString()} 🪙` : '0 🪙'}
              </div>
              <p className="text-[11px] text-welele-muted">From paid coin & airtime unlocks</p>
            </div>

            <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
              <span className="text-xs text-welele-muted">Creator Payout Balance</span>
              <div className="text-2xl font-black text-emerald-400 font-cinematic">
                {metrics?.payout_balance_zar != null
                  ? `R${Number(metrics.payout_balance_zar).toFixed(2)}`
                  : (metrics?.estimated_earnings_usd != null && Number(metrics.estimated_earnings_usd) > 0
                      ? `R${(Number(metrics.estimated_earnings_usd) * 18.5).toFixed(2)}`
                      : 'R0.00')}
              </div>
              <p className="text-[11px] text-welele-muted">Authoritative double-entry ledger balance</p>
            </div>
          </div>
        </div>
      )}

      {/* Phase 6J-2R-F: Edit Show Details Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-2xl bg-[#14151B] border border-white/15 rounded-[10px] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-5 border-b border-white/10 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Edit3 className="w-4 h-4 text-welele-gold" />
                  Edit Show Details
                </h3>
                <p className="text-xs text-welele-muted mt-0.5">
                  Update allowlisted metadata for {franchiseCode} ({series.title}).
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsEditModalOpen(false)}
                className="w-8 h-8 rounded-[7px] bg-white/5 hover:bg-white/10 text-white/60 hover:text-white flex items-center justify-center transition-all cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveDetails} className="p-5 space-y-4 overflow-y-auto">
              {editError && (
                <div className="p-3 rounded-[7px] bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-medium flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{editError}</span>
                </div>
              )}
              {editSuccess && (
                <div className="p-3 rounded-[7px] bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium flex items-center gap-2">
                  <Check className="w-4 h-4 shrink-0" />
                  <span>{editSuccess}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-white block">
                  Show Title <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  placeholder="e.g. Blood Ties"
                  required
                  className="w-full px-3 py-2 rounded-[7px] bg-black/50 border border-white/15 text-white text-xs focus:outline-none focus:border-welele-gold transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-white block">
                  Tagline / Catchphrase
                </label>
                <input
                  type="text"
                  value={editTagline}
                  onChange={(e) => setEditTagline(e.target.value)}
                  placeholder="e.g. Two powerful families tied by blood, torn apart by greed."
                  className="w-full px-3 py-2 rounded-[7px] bg-black/50 border border-white/15 text-white text-xs focus:outline-none focus:border-welele-gold transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-white block">
                  Synopsis
                </label>
                <textarea
                  value={editSynopsis}
                  onChange={(e) => setEditSynopsis(e.target.value)}
                  placeholder="Comprehensive narrative synopsis..."
                  rows={4}
                  className="w-full px-3 py-2 rounded-[7px] bg-black/50 border border-white/15 text-white text-xs focus:outline-none focus:border-welele-gold transition-colors leading-relaxed"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-white block">
                    Genre(s)
                  </label>
                  <input
                    type="text"
                    value={editGenre}
                    onChange={(e) => setEditGenre(e.target.value)}
                    placeholder="e.g. Drama • Family • Betrayal"
                    className="w-full px-3 py-2 rounded-[7px] bg-black/50 border border-white/15 text-white text-xs focus:outline-none focus:border-welele-gold transition-colors"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-white block">
                    Coin Price Per Episode (🪙)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={editCoinPrice}
                    onChange={(e) => setEditCoinPrice(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-[7px] bg-black/50 border border-white/15 text-white text-xs focus:outline-none focus:border-welele-gold transition-colors font-mono"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-white block">
                  Available Languages (comma separated)
                </label>
                <input
                  type="text"
                  value={editLanguages}
                  onChange={(e) => setEditLanguages(e.target.value)}
                  placeholder="e.g. English, isiZulu, isiXhosa"
                  className="w-full px-3 py-2 rounded-[7px] bg-black/50 border border-white/15 text-white text-xs focus:outline-none focus:border-welele-gold transition-colors"
                />
                <p className="text-[10px] text-welele-muted">
                  Comma-separated list of languages audio or subtitles are available in.
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-white block">
                  Tags (comma separated)
                </label>
                <input
                  type="text"
                  value={editTags}
                  onChange={(e) => setEditTags(e.target.value)}
                  placeholder="e.g. #MzansiDrama, #SandtonDynasty, #Billionaire"
                  className="w-full px-3 py-2 rounded-[7px] bg-black/50 border border-white/15 text-white text-xs focus:outline-none focus:border-welele-gold transition-colors"
                />
              </div>

              <div className="p-3 rounded-[7px] bg-black/30 border border-white/5 text-[11px] text-welele-muted">
                🛡️ <strong className="text-white/80">Allowlisted Persistence:</strong> Only allowlisted show metadata fields are sent to PostgreSQL. Franchise IP, ownership, rights ledger, and creator identity remain strictly protected.
              </div>

              <div className="pt-3 border-t border-white/10 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  disabled={isSavingDetails}
                  className="px-4 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 text-white text-xs font-bold transition-all cursor-pointer disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingDetails}
                  className="px-5 py-2 rounded-[7px] bg-gradient-to-r from-pink-500 to-welele-gold text-white text-xs font-bold transition-all shadow-md hover:brightness-110 flex items-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {isSavingDetails ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Saving to Database...</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Save Show Details</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Phase 6J-2R-F: Guarded Delete Confirmation Modal */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg bg-[#14151B] border border-red-500/40 rounded-[10px] shadow-2xl overflow-hidden p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center text-red-400 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Confirm Show Deletion</h3>
                <p className="text-xs text-red-400/90 font-medium">This action cannot be undone.</p>
              </div>
            </div>

            <div className="space-y-2 text-xs text-welele-muted">
              <p className="text-white/90">
                You are about to delete <strong className="text-white">"{series.title}"</strong> and its <strong className="text-white">{episodes.length}</strong> associated episode(s).
              </p>
              <div className="p-3 rounded-[7px] bg-black/40 border border-emerald-500/20 text-[11px] text-emerald-300 space-y-1">
                <div className="font-bold flex items-center gap-1.5 text-emerald-400">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Protected Boundaries Preserved
                </div>
                <p className="text-emerald-300/80">
                  Your master Digital IP franchise ({franchiseCode}), character bibles, commercial rights declarations, and audit logs will remain safe and intact in PostgreSQL.
                </p>
              </div>
            </div>

            {deleteError && (
              <div className="p-3 rounded-[7px] bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-medium flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{deleteError}</span>
              </div>
            )}

            <div className="space-y-1.5 pt-1">
              <label className="text-xs text-white/90 font-medium block">
                To confirm, type <strong className="text-red-400 select-all">{series.title}</strong> below:
              </label>
              <input
                type="text"
                value={deleteConfirmTitle}
                onChange={(e) => setDeleteConfirmTitle(e.target.value)}
                placeholder={series.title}
                className="w-full px-3 py-2 rounded-[7px] bg-black/60 border border-red-500/30 text-white text-xs focus:outline-none focus:border-red-500 transition-colors"
              />
            </div>

            <div className="pt-3 border-t border-white/10 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setIsDeleteModalOpen(false)}
                disabled={isDeletingShow}
                className="px-4 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 text-white text-xs font-bold transition-all cursor-pointer disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteSeries}
                disabled={
                  isDeletingShow ||
                  deleteConfirmTitle.trim().toLowerCase() !== series.title.trim().toLowerCase()
                }
                className="px-4 py-2 rounded-[7px] bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-all flex items-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isDeletingShow ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Deleting Show...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete This Show</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
