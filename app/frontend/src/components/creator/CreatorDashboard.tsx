import React, { useState, useEffect } from 'react';
import { creatorApi, retentionApi } from '../../services/api';
import { useApp } from '../../context/AppContext';
import { RetentionTelemetry, DropoffDataPoint } from '../../types';
import { ProvenanceBadge } from '../common/patterns/ProvenanceBadge';
import {
  TrendingUp,
  Eye,
  Coins,
  DollarSign,
  PlusCircle,
  Video,
  Sparkles,
  Zap,
  Flame,
  Globe,
  Smartphone,
  ChevronDown,
  Info,
  Layers,
  ArrowUpRight,
  BrainCircuit,
  BarChart3,
  Activity
} from 'lucide-react';

interface CreatorDashboardProps {
  onNavigateToUpload: () => void;
  onNavigateToSeries: () => void;
  onNavigateToEarnings: () => void;
}

export const CreatorDashboard: React.FC<CreatorDashboardProps> = ({
  onNavigateToUpload,
  onNavigateToSeries,
  onNavigateToEarnings,
}) => {
  const { stories } = useApp();
  const [stats, setStats] = useState<any>(null);
  const [series, setSeries] = useState<any[]>(stories || []);
  const [loading, setLoading] = useState<boolean>(false);

  // Retention Telemetry state
  const [selectedSeriesId, setSelectedSeriesId] = useState<string>(stories[0]?.id || 'story_blood_ties');
  const [selectedEpisodeNumber, setSelectedEpisodeNumber] = useState<number>(1);
  const [telemetry, setTelemetry] = useState<RetentionTelemetry | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<DropoffDataPoint | null>(null);

  useEffect(() => {
    creatorApi
      .getDashboard('creator_zola')
      .then((res) => {
        if (res) {
          setStats(res.stats || null);
          if (res.series && res.series.length > 0) {
            setSeries(res.series);
            setSelectedSeriesId(res.series[0].id);
          } else if (stories && stories.length > 0) {
            setSeries(stories);
            setSelectedSeriesId(stories[0].id);
          }
        }
      })
      .catch((err) => {
        console.warn('Using local fallback for creator stats:', err);
      })
      .finally(() => setLoading(false));
  }, [stories]);

  useEffect(() => {
    if (selectedSeriesId) {
      retentionApi
        .getTelemetry(selectedSeriesId, selectedEpisodeNumber)
        .then((data) => {
          if (data) setTelemetry(data);
        })
        .catch(() => {});
    }
  }, [selectedSeriesId, selectedEpisodeNumber]);

  // Calculate SVG curve path for retention
  const points = telemetry?.dropoff_curve || [];
  const svgWidth = 700;
  const svgHeight = 160;
  const paddingX = 30;
  const paddingY = 20;

  const getSvgCoordinates = (sec: number, pct: number) => {
    const x = paddingX + (sec / 90) * (svgWidth - paddingX * 2);
    const y = paddingY + ((100 - pct) / 60) * (svgHeight - paddingY * 2); // Map 40-100%
    return { x, y };
  };

  const pathD = points.reduce((acc, pt, idx) => {
    const { x, y } = getSvgCoordinates(pt.second, pt.retention_pct);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  const areaD = points.length > 0
    ? `${pathD} L ${getSvgCoordinates(90, 40).x} ${svgHeight - paddingY} L ${getSvgCoordinates(0, 40).x} ${svgHeight - paddingY} Z`
    : '';

  return (
    <div className="space-y-6 pb-24 text-white animate-fade-in">
      {/* Studio Banner */}
      <div className="p-6 rounded-[7px] bg-gradient-to-r from-welele-surface-2 via-welele-surface-3 to-welele-surface border border-pink-500/20 shadow-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-[7px] text-[10px] font-black uppercase tracking-wider bg-[#E6007A]/20 text-[#FF2A6D] border border-pink-500/30">
              CREATOR HUB™ STUDIO
            </span>
            <span className="text-xs text-welele-muted">Showrunner Operating Center</span>
          </div>
          <h1 className="text-2xl font-black text-white font-cinematic uppercase tracking-tight">
            Production & Audience Retention Engine
          </h1>
          <p className="text-xs text-welele-muted mt-1">
            Real-time cliffhanger drop-off curves, multi-series operations & African Mobile Money settlements.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={onNavigateToUpload}
            className="px-4 py-2.5 rounded-[7px] bg-gradient-welele text-white font-bold text-xs shadow-lg shadow-orange-500/20 flex items-center gap-2 hover:opacity-95 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Upload New Episode</span>
          </button>

          <button
            onClick={onNavigateToEarnings}
            className="px-4 py-2.5 rounded-[7px] bg-[#14151B] border border-white/10 text-white font-bold text-xs hover:bg-white/5 flex items-center gap-1.5 transition-all"
          >
            <Coins className="w-4 h-4 text-welele-gold" />
            <span>MoMo Payouts</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs text-welele-muted">
            <span>Total Video Views</span>
            <Eye className="w-4 h-4 text-welele-orange" />
          </div>
          <div className="text-2xl font-black text-white font-cinematic">
            {stats?.total_views?.toLocaleString() || '1,842,900'}
          </div>
          <div className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> +24.8% this month
          </div>
        </div>

        <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs text-welele-muted">
            <span>Cliffhanger Hook Rate</span>
            <Zap className="w-4 h-4 text-welele-gold" />
          </div>
          <div className="text-2xl font-black text-welele-gold font-cinematic">
            {telemetry?.completion_rate_pct ? `${telemetry.completion_rate_pct}%` : '86.4%'}
          </div>
          <div className="text-[10px] text-emerald-400 font-bold">
            {telemetry?.cliffhanger_conversion_pct || '64.2'}% coin paywall conversion
          </div>
        </div>

        <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs text-welele-muted">
            <span>Coin Earnings</span>
            <Coins className="w-4 h-4 text-welele-orange" />
          </div>
          <div className="text-2xl font-black text-welele-orange font-cinematic">
            🪙 {stats?.coin_earnings?.toLocaleString() || '142,500'}
          </div>
          <div className="text-[10px] text-white/70">
            From unlocks & virtual gifts
          </div>
        </div>

        <div className="p-4 rounded-[7px] bg-[#14151B] border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs text-welele-muted">
            <span>Available Payout</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 font-cinematic">
            R {stats?.payout_balance_usd ? (parseFloat(stats.payout_balance_usd) * 18.5).toLocaleString(undefined, { minimumFractionDigits: 2 }) : '17,575.00'}
          </div>
          <div className="text-[10px] text-welele-muted">
            Ready for instant MTN / M-Pesa transfer
          </div>
        </div>
      </div>

      {/* SECOND-BY-SECOND RETENTION TELEMETRY ENGINE */}
      <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1 rounded-[7px] bg-welele-orange/20 text-welele-orange">
                <Flame className="w-4 h-4" />
              </span>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Audience Retention & Cliffhanger Telemetry (90s Curve)
              </h3>
            </div>
            <p className="text-xs text-welele-muted mt-0.5">
              Tracks viewer retention per second to spot plot pacing dips and cliffhanger paywall conversions.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedSeriesId}
              onChange={(e) => setSelectedSeriesId(e.target.value)}
              className="bg-[#0B0C10] px-3 py-1.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-welele-gold"
            >
              {series.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title}
                </option>
              ))}
            </select>

            <select
              value={selectedEpisodeNumber}
              onChange={(e) => setSelectedEpisodeNumber(Number(e.target.value))}
              className="bg-[#0B0C10] px-3 py-1.5 rounded-[7px] border border-white/10 text-xs text-white focus:outline-none focus:border-welele-gold"
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map((num) => (
                <option key={num} value={num}>
                  Episode {num}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Interactive SVG Chart */}
        <div className="relative bg-[#0B0C10] p-4 rounded-[7px] border border-white/5 overflow-hidden">
          <div className="flex items-center justify-between text-[11px] text-welele-muted mb-2 font-mono">
            <span>100% Retention</span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-welele-gold inline-block" /> Active Viewers
              </span>
              <span className="flex items-center gap-1.5 text-red-400 font-bold">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping inline-block" /> T+88s Cliffhanger
              </span>
            </div>
          </div>

          <div className="w-full overflow-x-auto">
            <svg
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              className="w-full h-44 text-welele-gold overflow-visible"
            >
              <defs>
                <linearGradient id="retentionGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#FFB800" stopOpacity="0.35" />
                  <stop offset="100%" stopColor="#FFB800" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Grid lines */}
              <line x1={paddingX} y1={paddingY} x2={svgWidth - paddingX} y2={paddingY} stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
              <line x1={paddingX} y1={svgHeight / 2} x2={svgWidth - paddingX} y2={svgHeight / 2} stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
              <line x1={paddingX} y1={svgHeight - paddingY} x2={svgWidth - paddingX} y2={svgHeight - paddingY} stroke="rgba(255,255,255,0.15)" />

              {/* Cliffhanger Marker Line */}
              {(() => {
                const cliffPos = getSvgCoordinates(88, 100);
                return (
                  <g>
                    <line
                      x1={cliffPos.x}
                      y1={paddingY}
                      x2={cliffPos.x}
                      y2={svgHeight - paddingY}
                      stroke="#EF4444"
                      strokeWidth="2"
                      strokeDasharray="4 4"
                    />
                    <text
                      x={cliffPos.x - 45}
                      y={paddingY + 12}
                      fill="#EF4444"
                      fontSize="9"
                      fontWeight="bold"
                    >
                      PAYWALL LOCK
                    </text>
                  </g>
                );
              })()}

              {/* Area & Line */}
              <path d={areaD} fill="url(#retentionGrad)" />
              <path d={pathD} fill="none" stroke="#FFB800" strokeWidth="2.5" strokeLinecap="round" />

              {/* Interactive Dots */}
              {points.map((pt, idx) => {
                const { x, y } = getSvgCoordinates(pt.second, pt.retention_pct);
                const isHovered = hoveredPoint?.second === pt.second;
                return (
                  <circle
                    key={idx}
                    cx={x}
                    cy={y}
                    r={isHovered ? 6 : pt.is_cliffhanger ? 4.5 : 3}
                    fill={pt.is_cliffhanger ? '#EF4444' : '#FFB800'}
                    stroke="#0B0C10"
                    strokeWidth="1.5"
                    className="cursor-pointer transition-all hover:scale-150"
                    onMouseEnter={() => setHoveredPoint(pt)}
                    onMouseLeave={() => setHoveredPoint(null)}
                  />
                );
              })}
            </svg>
          </div>

          {/* Bottom X-axis labels */}
          <div className="flex justify-between text-[10px] text-welele-muted font-mono mt-1 px-4">
            <span>00:00 (Hook)</span>
            <span>00:30 (Inciting Incident)</span>
            <span>00:60 (Reversal)</span>
            <span className="text-red-400 font-bold">00:88 (Paywall)</span>
            <span>00:90</span>
          </div>

          {/* Hover Telemetry Card */}
          {hoveredPoint && (
            <div className="mt-3 p-2.5 rounded-[7px] bg-[#14151B] border border-welele-gold/40 text-xs flex items-center justify-between">
              <span className="text-white">
                Timestamp: <strong className="font-mono text-welele-gold">00:{hoveredPoint.second < 10 ? '0' + hoveredPoint.second : hoveredPoint.second}</strong>
              </span>
              <span className="text-white">
                Retention: <strong className="text-emerald-400">{hoveredPoint.retention_pct}%</strong>
              </span>
              <span className="text-welele-muted">
                Active Viewers: <strong className="text-white font-mono">{(hoveredPoint.viewer_count || 0).toLocaleString()}</strong>
              </span>
            </div>
          )}
        </div>

        {/* Telemetry Secondary Grid: Geo & Telco Mix */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Geographic Breakdown */}
          <div className="p-4 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Globe className="w-4 h-4 text-welele-gold" />
                Audience Geographic Distribution
              </h4>
              <ProvenanceBadge tier="EXTERNAL_DATA" size="sm" />
            </div>
            <div className="space-y-2">
              {(telemetry?.geo_distribution || []).map((geo) => (
                <div key={geo.country} className="space-y-1">
                  <div className="flex justify-between text-xs text-white">
                    <span>
                      {geo.flag} {geo.country}
                    </span>
                    <span className="text-welele-muted font-mono">{geo.share_pct}% ({(geo.views || 0).toLocaleString()} views)</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-welele-gold rounded-full" style={{ width: `${geo.share_pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Telco Payment Mix */}
          <div className="p-4 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Smartphone className="w-4 h-4 text-emerald-400" />
                Telco Airtime & Mobile Money Revenue Mix
              </h4>
              <ProvenanceBadge tier="EXTERNAL_DATA" size="sm" />
            </div>
            <div className="space-y-2">
              {(telemetry?.telco_payment_mix || []).map((t) => (
                <div key={t.provider} className="space-y-1">
                  <div className="flex justify-between text-xs text-white">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: t.color }} />
                      {t.provider}
                    </span>
                    <span className="text-welele-gold font-mono font-bold">{t.share_pct}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${t.share_pct}%`, backgroundColor: t.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Evidence -> Analysis -> Recommendation Hierarchy Card */}
        <div className="mt-4 p-4 rounded-[7px] bg-black/40 border border-purple-500/20 space-y-3 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-white uppercase tracking-wider flex items-center gap-2 text-xs">
              <BrainCircuit className="w-4 h-4 text-purple-400" />
              IP Intelligence: Evidence → Analysis → Recommendation Stack
            </span>
            <ProvenanceBadge tier="INTELLIGENCE" size="sm" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-1">
              <div className="flex items-center justify-between text-[10px] text-welele-muted">
                <span className="font-bold text-white uppercase">1. Evidence Layer</span>
                <ProvenanceBadge tier="MEDIA_OBSERVED" size="sm" />
              </div>
              <p className="text-[11px] text-white/80">
                1,842,900 stream seconds observed. 88-second mean paywall engagement across ZA viewers.
              </p>
            </div>

            <div className="p-3 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-1">
              <div className="flex items-center justify-between text-[10px] text-welele-muted">
                <span className="font-bold text-white uppercase">2. Analytical Layer</span>
                <ProvenanceBadge tier="ANALYTICAL" size="sm" />
              </div>
              <p className="text-[11px] text-white/80">
                86.4% completion rate before paywall lock; 64.2% coin conversion velocity at climax cliffhanger.
              </p>
            </div>

            <div className="p-3 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-1">
              <div className="flex items-center justify-between text-[10px] text-welele-muted">
                <span className="font-bold text-white uppercase">3. Recommendation</span>
                <ProvenanceBadge tier="INTELLIGENCE" size="sm" />
              </div>
              <p className="text-[11px] text-emerald-300">
                Maintain high-stakes conflict climax between T+60s and T+88s to maximize immediate paywall coin unlocks.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Published Series List */}
      <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white font-cinematic uppercase tracking-wider flex items-center gap-2">
            <Video className="w-4 h-4 text-welele-orange" />
            Your Microdrama Series ({series.length})
          </h3>
          <button
            onClick={onNavigateToSeries}
            className="text-xs text-welele-orange hover:underline font-semibold"
          >
            Manage All Series
          </button>
        </div>

        <div className="space-y-3">
          {series.map((item) => {
            const views = item.total_views || 0;
            const audienceState =
              views > 50000
                ? 'MEASURED'
                : views > 1000
                ? 'EARLY SIGNAL'
                : 'COLLECTING EVIDENCE / INSUFFICIENT SAMPLE';

            return (
              <div
                key={item.id}
                className="p-4 rounded-[7px] bg-[#0B0C10] border border-white/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:border-white/15 transition-all"
              >
                <div className="flex items-center gap-3">
                  <img
                    src={item.vertical_poster}
                    alt={item.title}
                    className="w-12 h-16 rounded-[7px] object-cover"
                  />
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm font-bold text-white">{item.title}</h4>
                      {item.franchise_code && (
                        <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-white/10 text-welele-gold border border-white/10">
                          {item.franchise_code}
                        </span>
                      )}
                      <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-bold bg-emerald-500/20 text-emerald-400">
                        PUBLISHED
                      </span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[8px] font-mono font-bold ${
                          audienceState === 'MEASURED'
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : audienceState === 'EARLY SIGNAL'
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            : 'bg-white/10 text-welele-muted border border-white/10'
                        }`}
                      >
                        {audienceState}
                      </span>
                    </div>
                    <p className="text-xs text-welele-muted mt-0.5">{item.genre} • {item.language}</p>
                    <div className="flex items-center gap-3 text-[11px] text-welele-gold mt-1 font-semibold flex-wrap">
                      <span>{item.total_episodes} Episodes</span>
                      <span>🪙 {item.coin_price_per_episode || 5} coins/ep</span>
                      <span>{views.toLocaleString()} views</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <button
                    onClick={onNavigateToUpload}
                    className="px-3 py-1.5 rounded-[7px] bg-white/5 hover:bg-white/10 text-xs font-bold text-white border border-white/10 transition-all"
                  >
                    + Add Episode
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
