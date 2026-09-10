import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { creatorApi } from '../../services/api';
import { Episode, EpisodeStatus } from '../../types';
import {
  Video,
  PlusCircle,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Coins,
  Search,
  Filter,
  Layers,
  Sparkles
} from 'lucide-react';

interface GlobalEpisodesManagerProps {
  onOpenEpisodePipeline: (seriesId?: string, episodeNumber?: number) => void;
}

export const GlobalEpisodesManager: React.FC<GlobalEpisodesManagerProps> = ({
  onOpenEpisodePipeline,
}) => {
  const { stories, user } = useApp();
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [episodesList, setEpisodesList] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchEpisodes = async () => {
    try {
      const creatorId = user?.creator_id || 'creator_zola';
      const res = await creatorApi.getEpisodes(creatorId);
      if (res && res.episodes && res.episodes.length > 0) {
        setEpisodesList(
          res.episodes.map((ep: any) => ({
            ...ep,
            effective_status: ep.status || 'published',
            calculated_number: ep.episode_number || 1,
          }))
        );
        return;
      }
    } catch (e) {
      console.warn('[GlobalEpisodesManager] Could not fetch creator episodes:', e);
    }

    // Fallback mapping from stories feed
    const fallback = stories.flatMap((s) =>
      (s.episodes || []).map((ep, idx) => ({
        ...ep,
        series_id: s.id,
        series_title: s.title,
        series_cover: s.vertical_poster || s.cover_image,
        genre: s.genre,
        calculated_number: ep.episode_number || idx + 1,
        effective_status: ep.status || 'published',
      }))
    );
    setEpisodesList(fallback);
  };

  useEffect(() => {
    fetchEpisodes().finally(() => setLoading(false));
  }, [stories, user?.creator_id]);

  const filteredEpisodes = episodesList.filter((ep) => {
    if (selectedFilter === 'published' && ep.effective_status !== 'published') return false;
    if (selectedFilter === 'under_review' && !['under_review', 'submitted', 'pending_review'].includes(ep.effective_status)) return false;
    if (selectedFilter === 'draft' && ep.effective_status !== 'draft') return false;
    if (selectedFilter === 'changes_requested' && ep.effective_status !== 'changes_requested') return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        ep.title?.toLowerCase().includes(q) ||
        ep.series_title?.toLowerCase().includes(q) ||
        (ep.cliffhanger_hook && ep.cliffhanger_hook.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'published':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-max">
            <CheckCircle2 className="w-3 h-3" /> Published
          </span>
        );
      case 'under_review':
      case 'submitted':
      case 'pending_review':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-max">
            <Clock className="w-3 h-3" /> In Review
          </span>
        );
      case 'changes_requested':
        return (
          <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-bold bg-orange-500/20 text-orange-400 border border-orange-500/30 flex items-center gap-1 w-max">
            <AlertTriangle className="w-3 h-3" /> Needs Changes
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

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-24 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold text-[#FF2A6D] uppercase tracking-wider">
              CREATOR STUDIO OS
            </span>
            <span className="text-xs text-welele-muted">•</span>
            <span className="text-xs text-welele-muted">Master Production Ingestion</span>
          </div>
          <h1 className="text-2xl font-black text-white uppercase tracking-tight font-cinematic">
            Episode Management & Production Lifecycle
          </h1>
          <p className="text-xs text-welele-muted mt-0.5">
            Monitor, inspect, and submit vertical episodes across all your microdrama titles.
          </p>
        </div>

        <button
          onClick={() => onOpenEpisodePipeline()}
          className="px-4 py-2.5 rounded-[7px] bg-gradient-to-r from-[#E6007A] to-[#FF2A6D] text-white font-bold text-xs shadow-lg shadow-pink-500/20 flex items-center gap-2 hover:opacity-95 transition-all"
        >
          <PlusCircle className="w-4 h-4" />
          <span>+ Upload / Add Episode</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
          {[
            { id: 'all', label: `All Episodes (${episodesList.length})` },
            { id: 'published', label: 'Published' },
            { id: 'under_review', label: 'In Review' },
            { id: 'draft', label: 'Drafts' },
            { id: 'changes_requested', label: 'Needs Changes' },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setSelectedFilter(f.id)}
              className={`px-3 py-1.5 rounded-[7px] text-xs font-bold transition-all whitespace-nowrap ${
                selectedFilter === f.id
                  ? 'bg-[#E6007A] text-white shadow-sm'
                  : 'bg-black/40 text-welele-muted hover:text-white border border-white/5'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="relative min-w-[240px]">
          <Search className="w-3.5 h-3.5 text-welele-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by title, series, or cliffhanger..."
            className="w-full bg-[#0F1014] pl-9 pr-3.5 py-2 rounded-[7px] border border-white/10 text-xs text-white placeholder:text-welele-muted focus:outline-none focus:border-[#E6007A]"
          />
        </div>
      </div>

      {/* Episodes Master Table */}
      <div className="rounded-[7px] border border-white/10 bg-[#121318] overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs text-white">
          <thead className="bg-[#181920] text-welele-muted uppercase font-mono text-[10px] border-b border-white/5">
            <tr>
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">Episode</th>
              <th className="px-4 py-3">Series Title</th>
              <th className="px-4 py-3">Duration</th>
              <th className="px-4 py-3">Tier</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filteredEpisodes.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-welele-muted">
                  No episodes match the selected filter.
                </td>
              </tr>
            ) : (
              filteredEpisodes.map((ep) => {
                const numStr = ep.calculated_number < 10 ? `0${ep.calculated_number}` : `${ep.calculated_number}`;
                return (
                  <tr key={ep.id} className="hover:bg-white/5 transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-welele-gold text-xs">
                      {numStr}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-bold text-white text-xs">{ep.title}</div>
                      <div className="text-[11px] text-welele-muted line-clamp-1 mt-0.5 max-w-sm">
                        {ep.cliffhanger_hook || ep.synopsis}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-semibold text-white/90">{ep.series_title}</span>
                      <span className="text-[10px] text-welele-muted block">{ep.genre}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-welele-muted">
                      {ep.duration_seconds || 62}s
                    </td>
                    <td className="px-4 py-3">
                      {ep.is_free ? (
                        <span className="text-emerald-400 font-bold text-[11px]">Free</span>
                      ) : (
                        <span className="text-amber-400 font-bold text-[11px] flex items-center gap-1">
                          <Coins className="w-3 h-3" /> {ep.coin_price || 5}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(ep.effective_status)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => onOpenEpisodePipeline(ep.series_id, ep.calculated_number)}
                        className="px-2.5 py-1 rounded-[7px] bg-white/5 hover:bg-white/10 text-white/80 hover:text-white text-[11px] font-semibold border border-white/10"
                      >
                        Inspect Pipeline
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
