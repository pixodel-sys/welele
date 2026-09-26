import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/api';
import { useApp } from '../../context/AppContext';
import { ProvenanceBadge } from '../common/patterns/ProvenanceBadge';
import {
  Activity,
  Filter,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  CheckCircle,
  XCircle,
  Telescope,
  Users,
  Eye,
  Play,
  ArrowRight,
  Zap,
  Lock,
  CreditCard,
  Check,
  Heart,
  MessageCircle,
  RotateCcw,
  Sparkles
} from 'lucide-react';

interface FunnelStep {
  step: number;
  key: string;
  label: string;
  sessions: number;
  conversion_pct: number;
}

interface DropoffMilestones {
  started: number;
  reached_25: number;
  reached_50: number;
  reached_75: number;
  reached_90: number;
  stopped_before_25: number;
  stopped_25_to_50: number;
  stopped_50_to_75: number;
  stopped_75_to_90: number;
  completed_90_plus: number;
}

interface RetentionCurvePoint {
  second: number;
  active_viewers: number;
  retention_pct: number;
  stalls_at_interval: number;
  is_cliffhanger_window: boolean;
}

interface RetentionAnomaly {
  anomaly_id: string;
  second_start: number;
  second_end: number;
  retention_delta_pct: number;
  classification: 'RETENTION_ANOMALY_CLEAN_PLAYBACK' | 'RETENTION_ANOMALY_WITH_TECHNICAL_CORRELATION';
  stalls_in_window: number;
  sample_size: number;
  confidence_tier: string;
  description: string;
}

interface Project40FunnelData {
  provenance: {
    zero_synthetic_data: boolean;
    environment_filter: string;
    total_events_evaluated: number;
    test_events_excluded: number;
    canary_events_excluded: number;
    legacy_events_quarantined: number;
    has_data: boolean;
    timestamp: string;
    confidence_tier?: 'INSUFFICIENT' | 'PRELIMINARY' | 'DEVELOPING' | 'ESTABLISHED';
    confidence_disclosure?: string;
    projection_version?: string;
    methodology_version?: string;
  };
  funnel: FunnelStep[];
  dropoff_milestones: DropoffMilestones;
  engagement_metrics: {
    reactions_count: number;
    comments_count: number;
  };
  discovered_breakdown: Array<{ id: string; impressions: number }>;
  selected_breakdown: Array<{ title: string; sessions: number }>;
  hook_3s?: { count: number; pct: number };
  hook_10s?: { count: number; pct: number };
  continuation_intent?: number;
  completions?: number;
  completion_rate_pct?: number;
  rewatches?: number;
  technical_disruptions?: {
    total_buffer_events: number;
    total_stall_events: number;
    sessions_with_disruptions: number;
    stall_ratio_pct: number;
  };
  retention_curve?: RetentionCurvePoint[];
  detected_anomalies?: RetentionAnomaly[];
}

export const Project40Evidence: React.FC = () => {
  const { stories } = useApp();
  const [funnelData, setFunnelData] = useState<Project40FunnelData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedSeriesId, setSelectedSeriesId] = useState<string>('ALL');
  const [selectedEnvironment, setSelectedEnvironment] = useState<string>('production');
  const [selectedDays, setSelectedDays] = useState<number | undefined>(undefined);

  const fetchEvidence = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getProject40Funnel({
        series_id: selectedSeriesId === 'ALL' ? undefined : selectedSeriesId,
        environment: selectedEnvironment,
        days: selectedDays
      });
      setFunnelData(res);
    } catch (err) {
      console.warn('[Project40Evidence] Failed to fetch funnel data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidence();
  }, [selectedSeriesId, selectedEnvironment, selectedDays]);

  const funnelIcons: Record<string, React.ReactNode> = {
    ENTERED: <Users className="w-4 h-4 text-sky-400" />,
    DISCOVERED: <Eye className="w-4 h-4 text-cyan-400" />,
    SELECTED: <Sparkles className="w-4 h-4 text-amber-400" />,
    WATCHED: <Play className="w-4 h-4 text-emerald-400 fill-current" />,
    CONTINUED: <ArrowRight className="w-4 h-4 text-teal-400" />,
    ENGAGED: <Heart className="w-4 h-4 text-pink-400 fill-current" />,
    PAYWALL: <Lock className="w-4 h-4 text-orange-400" />,
    PAYMENT_ATTEMPT: <CreditCard className="w-4 h-4 text-yellow-400" />,
    PAID: <Zap className="w-4 h-4 text-emerald-400 fill-current" />,
    CONTINUED_POST_PAY: <Check className="w-4 h-4 text-emerald-300" />,
    RETURNED: <RotateCcw className="w-4 h-4 text-indigo-400" />
  };

  return (
    <div className="space-y-6 animate-fade-in text-white">
      {/* Header Banner */}
      <div className="p-5 sm:p-6 rounded-[7px] bg-[#0E1015] border border-emerald-500/30 shadow-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-[7px] text-[10px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              PROJECT 40 OBSERVABLE
            </span>
            <span className="text-xs text-welele-muted">Authoritative Behavioural Evidence</span>
            <ProvenanceBadge tier="ANALYTICAL" label="Empirical Evidence" size="sm" />
          </div>
          <h2 className="text-xl font-black text-white font-cinematic uppercase tracking-tight">
            11-Step Viewer Journey & Empirical Funnel
          </h2>
          <p className="text-xs text-welele-muted mt-0.5">
            Strict Zero Synthetic Data Policy. Evaluates actual recorded telemetry events with environment isolation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchEvidence}
            disabled={loading}
            className="px-3 py-2 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-bold text-white flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Evidence</span>
          </button>
        </div>
      </div>

      {/* Control Filter Bar */}
      <div className="p-3.5 rounded-[7px] bg-[#0B0C10] border border-white/5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          {/* Environment Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-welele-muted font-bold">Environment:</span>
            <select
              value={selectedEnvironment}
              onChange={(e) => setSelectedEnvironment(e.target.value)}
              className="bg-[#14151B] px-3 py-1.5 rounded-[7px] border border-white/10 text-white font-bold focus:border-emerald-500 focus:outline-none cursor-pointer"
            >
              <option value="production">Production (Clean Launch Data)</option>
              <option value="staging">Staging (Internal Integration)</option>
              <option value="test">Canary / Unverified Historical</option>
              <option value="all">All Environments  •  Full Picture</option>
            </select>
          </div>

          {/* Series Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-welele-muted font-bold">Story / Series:</span>
            <select
              value={selectedSeriesId}
              onChange={(e) => setSelectedSeriesId(e.target.value)}
              className="bg-[#14151B] px-3 py-1.5 rounded-[7px] border border-white/10 text-white font-bold focus:border-emerald-500 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Catalog Stories</option>
              {stories.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title}
                </option>
              ))}
            </select>
          </div>

          {/* Time Window */}
          <div className="flex items-center gap-1.5">
            <span className="text-welele-muted font-bold">Time Window:</span>
            <select
              value={selectedDays ?? 'ALL'}
              onChange={(e) => setSelectedDays(e.target.value === 'ALL' ? undefined : Number(e.target.value))}
              className="bg-[#14151B] px-3 py-1.5 rounded-[7px] border border-white/10 text-white font-bold focus:border-emerald-500 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Time</option>
              <option value="1">Last 24 Hours</option>
              <option value="7">Last 7 Days</option>
              <option value="30">Last 30 Days</option>
            </select>
          </div>
        </div>

        {/* Provenance Badge Pill — always-visible production evidence status */}
        <div className="flex items-center gap-3 text-[11px] font-mono flex-wrap">
          {/* PRODUCTION EVIDENCE EXISTS vs NO PRODUCTION EVIDENCE pill */}
          {!loading && (
            funnelData?.provenance?.has_data ? (
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 font-black uppercase tracking-wider">
                <CheckCircle className="w-3.5 h-3.5" />
                Production Evidence Exists
              </span>
            ) : (
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-amber-500/15 border border-amber-500/40 text-amber-400 font-black uppercase tracking-wider">
                <XCircle className="w-3.5 h-3.5" />
                No Production Evidence
              </span>
            )
          )}

          {/* Canonical Projection Confidence Tier Badge */}
          {funnelData?.provenance?.confidence_tier && (
            <span
              className={`px-2.5 py-1 rounded-[6px] font-black uppercase tracking-wider border ${
                funnelData.provenance.confidence_tier === 'ESTABLISHED'
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                  : funnelData.provenance.confidence_tier === 'DEVELOPING'
                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                  : funnelData.provenance.confidence_tier === 'PRELIMINARY'
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-red-500/20 text-red-300 border-red-500/40'
              }`}
              title={funnelData.provenance.confidence_disclosure || ''}
            >
              TIER: {funnelData.provenance.confidence_tier}
            </span>
          )}

          {funnelData?.provenance?.projection_version && (
            <span className="text-welele-muted text-[10px]" title="Canonical Projection Contract">
              v{funnelData.provenance.projection_version} ({funnelData.provenance.methodology_version})
            </span>
          )}

          <span className="text-emerald-400 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            {funnelData?.provenance?.total_events_evaluated ?? 0} events evaluated
          </span>
          {/* Split exclusion counters — canary and legacy are distinct provenance classes */}
          {(funnelData?.provenance?.canary_events_excluded ?? 0) > 0 && (
            <>
              <span className="text-welele-muted">|</span>
              <span className="text-sky-400" title="Deliberately tagged test/staging events">
                {funnelData!.provenance.canary_events_excluded} canary isolated
              </span>
            </>
          )}
          {(funnelData?.provenance?.legacy_events_quarantined ?? 0) > 0 && (
            <>
              <span className="text-welele-muted">|</span>
              <span className="text-welele-orange" title="Events with missing or unverifiable provenance — not the same as test data">
                {funnelData!.provenance.legacy_events_quarantined} legacy/unverified quarantined
              </span>
            </>
          )}
        </div>
      </div>

      {/* Honest Confidence Disclosure Alert */}
      {funnelData?.provenance?.confidence_disclosure && (
        <div className="px-4 py-2.5 rounded-[7px] bg-white/[0.03] border border-white/10 flex items-center gap-2.5 text-xs text-welele-muted">
          <Telescope className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>{funnelData.provenance.confidence_disclosure}</span>
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-welele-muted animate-pulse">
          Querying authoritative telemetry ledger...
        </div>
      ) : !funnelData || !funnelData.provenance.has_data ? (
        /* ---------------------------------------------------------------- */
        /* ZERO-STATE: two differentiated panels based on quarantine context */
        /* ---------------------------------------------------------------- */
        funnelData && funnelData.provenance.test_events_excluded > 0 ? (
          /* QUARANTINE-EMPTY: events exist but ALL were quarantined as test fixtures */
          <div className="p-8 rounded-[7px] bg-amber-950/20 border border-amber-500/30 space-y-4">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-[7px] bg-amber-500/15 flex items-center justify-center text-amber-400 shrink-0 mt-0.5">
                <XCircle className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-base font-black text-amber-300 uppercase tracking-wider">
                  No Production Evidence
                </h3>
                <p className="text-sm text-amber-200/70">
                  All {funnelData.provenance.test_events_excluded.toLocaleString()} evaluated event
                  {funnelData.provenance.test_events_excluded !== 1 ? 's were' : ' was'} quarantined
                  from the {selectedEnvironment} view due to unverified or missing provenance.
                  {(funnelData.provenance.canary_events_excluded ?? 0) > 0 && (
                    <> {funnelData.provenance.canary_events_excluded} {funnelData.provenance.canary_events_excluded === 1 ? 'was an' : 'were'} explicit canary event{funnelData.provenance.canary_events_excluded !== 1 ? 's' : ''}.</>
                  )}
                  {(funnelData.provenance.legacy_events_quarantined ?? 0) > 0 && (
                    <> {funnelData.provenance.legacy_events_quarantined} had missing or unverifiable provenance — they are <em>not</em> labelled as test data.
                    </>
                  )}
                </p>
                <p className="text-xs text-welele-muted mt-2">
                  That's not bad — the quarantine boundary is working. To inspect this material, switch to{' '}
                  <button
                    onClick={() => setSelectedEnvironment('test')}
                    className="text-amber-400 font-bold underline underline-offset-2 hover:text-amber-300 transition-colors"
                  >
                    Canary / Unverified Historical
                  </button>.
                </p>
              </div>
            </div>
            <div className="pl-16 grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-[7px] bg-white/5 border border-white/5">
                <div className="text-welele-muted mb-0.5">Test Events Isolated</div>
                <div className="text-2xl font-black text-amber-400 font-cinematic">
                  {funnelData.provenance.test_events_excluded.toLocaleString()}
                </div>
              </div>
              <div className="p-3 rounded-[7px] bg-white/5 border border-white/5">
                <div className="text-welele-muted mb-0.5">Genuine Production Sessions</div>
                <div className="text-2xl font-black text-white font-cinematic">0</div>
              </div>
              <div className="p-3 rounded-[7px] bg-white/5 border border-white/5">
                <div className="text-welele-muted mb-0.5">Synthetic Numbers Shown</div>
                <div className="text-2xl font-black text-emerald-400 font-cinematic">0</div>
              </div>
            </div>
          </div>
        ) : (
          /* GENUINELY EMPTY: no events at all — platform is live but no data yet */
          <div className="p-8 rounded-[7px] bg-[#0D0F14] border border-sky-500/20 space-y-4">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-[7px] bg-sky-500/10 flex items-center justify-center text-sky-400 shrink-0 mt-0.5">
                <Telescope className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-base font-black text-sky-300 uppercase tracking-wider">
                  No Evidence Yet
                </h3>
                <p className="text-sm text-sky-200/60">
                  No viewer sessions have been recorded for{' '}
                  <span className="font-bold text-white">{selectedEnvironment}</span> yet.
                  The platform is live. Evidence will populate as real viewers engage.
                </p>
                <p className="text-xs text-welele-muted mt-2">
                  Zero synthetic numbers or speculative charts are displayed. This panel will transform into the full empirical funnel as soon as the first authenticated viewer session arrives.
                </p>
              </div>
            </div>
          </div>
        )
      ) : (
        <>
          {/* Main 11-Step Funnel Grid */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                Empirical Project 40 Viewer Funnel
              </h3>
              <span className="text-[11px] text-welele-muted font-mono">
                Base: {funnelData.funnel[0]?.sessions || 0} entered sessions
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
              {funnelData.funnel.map((step) => (
                <div
                  key={step.key}
                  className="p-3.5 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-2 flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <div className="p-1.5 rounded-[5px] bg-white/5">
                        {funnelIcons[step.key] || <Activity className="w-4 h-4" />}
                      </div>
                      <span className="text-xs font-bold text-white truncate">{step.label}</span>
                    </div>
                    <span className="text-[10px] font-mono text-welele-muted">#{step.step}</span>
                  </div>

                  <div>
                    <div className="text-2xl font-black text-white font-cinematic">
                      {step.sessions.toLocaleString()}
                    </div>
                    <div className="flex items-center justify-between text-[10px] mt-0.5">
                      <span className="text-welele-muted">Conversion</span>
                      <span className="font-mono font-bold text-emerald-400">{step.conversion_pct}%</span>
                    </div>
                    <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden mt-1.5">
                      <div
                        className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full"
                        style={{ width: `${Math.min(100, step.conversion_pct)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Secondary Telemetry Inspections */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Where Did They Stop? (Drop-Off Milestones) */}
            <div className="p-4 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Play className="w-3.5 h-3.5 text-welele-orange" />
                  Playback Drop-Off Breakdown
                </h4>
                <span className="text-[10px] text-welele-muted font-mono">
                  {funnelData.dropoff_milestones.started} Starts
                </span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-welele-muted">Stopped before 25% (Bounce):</span>
                  <span className="font-mono font-bold text-red-400">
                    {funnelData.dropoff_milestones.stopped_before_25} sessions
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-welele-muted">Stopped between 25% - 50%:</span>
                  <span className="font-mono font-bold text-amber-400">
                    {funnelData.dropoff_milestones.stopped_25_to_50} sessions
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-welele-muted">Stopped between 50% - 75%:</span>
                  <span className="font-mono font-bold text-yellow-400">
                    {funnelData.dropoff_milestones.stopped_50_to_75} sessions
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-welele-muted">Stopped at Cliffhanger (75%-90%):</span>
                  <span className="font-mono font-bold text-orange-400">
                    {funnelData.dropoff_milestones.stopped_75_to_90} sessions
                  </span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-emerald-400 font-bold">Completed (90%+):</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {funnelData.dropoff_milestones.completed_90_plus} sessions
                  </span>
                </div>
              </div>
            </div>

            {/* Story Selection Distribution */}
            <div className="p-4 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-welele-gold" />
                  What Did They Select?
                </h4>
                <span className="text-[10px] text-welele-muted font-mono">
                  {funnelData.selected_breakdown.length} Titles
                </span>
              </div>
              <div className="space-y-2 text-xs">
                {funnelData.selected_breakdown.length === 0 ? (
                  <div className="py-6 text-center text-welele-muted text-xs">
                    No story selection events recorded.
                  </div>
                ) : (
                  funnelData.selected_breakdown.map((item) => (
                    <div key={item.title} className="flex justify-between items-center py-1 border-b border-white/5">
                      <span className="text-white truncate max-w-[200px]">{item.title}</span>
                      <span className="font-mono font-bold text-welele-gold">{item.sessions} sessions</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Viewer Engagement Breakdown */}
            <div className="p-4 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Heart className="w-3.5 h-3.5 text-pink-400" />
                  Did They Engage?
                </h4>
              </div>
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-3 rounded-[7px] bg-white/5 space-y-1">
                  <div className="flex items-center gap-1.5 text-pink-400 text-xs font-bold">
                    <Heart className="w-3.5 h-3.5 fill-current" />
                    <span>Reactions</span>
                  </div>
                  <div className="text-2xl font-black text-white font-cinematic">
                    {funnelData.engagement_metrics.reactions_count}
                  </div>
                  <span className="text-[10px] text-welele-muted">Likes logged</span>
                </div>

                <div className="p-3 rounded-[7px] bg-white/5 space-y-1">
                  <div className="flex items-center gap-1.5 text-cyan-400 text-xs font-bold">
                    <MessageCircle className="w-3.5 h-3.5" />
                    <span>Comments</span>
                  </div>
                  <div className="text-2xl font-black text-white font-cinematic">
                    {funnelData.engagement_metrics.comments_count}
                  </div>
                  <span className="text-[10px] text-welele-muted">Viewer comments</span>
                </div>
              </div>
            </div>
          </div>

          {/* Canonical Content Evidence Projections: Behavioral Distinctions & Technical Disambiguation */}
          <div className="space-y-4 pt-2">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Canonical Content Evidence Matrix
              </h3>
              <span className="text-[10px] text-welele-muted font-mono">
                Single Production Derivation • Semantic Clarity
              </span>
            </div>

            {/* 6 Key Behavioral Pillars (Disambiguating 25% milestone from Continuation Intent) */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="p-3 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-1">
                <div className="text-[10px] font-bold text-welele-muted uppercase">3s Hook Retention</div>
                <div className="text-xl font-black text-white font-cinematic">
                  {funnelData.hook_3s?.pct ?? 0}%
                </div>
                <div className="text-[10px] text-emerald-400 font-mono">
                  {funnelData.hook_3s?.count ?? 0} viewers
                </div>
              </div>

              <div className="p-3 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-1">
                <div className="text-[10px] font-bold text-welele-muted uppercase">10s Hook Retention</div>
                <div className="text-xl font-black text-white font-cinematic">
                  {funnelData.hook_10s?.pct ?? 0}%
                </div>
                <div className="text-[10px] text-teal-400 font-mono">
                  {funnelData.hook_10s?.count ?? 0} viewers
                </div>
              </div>

              <div className="p-3 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-1">
                <div className="text-[10px] font-bold text-welele-muted uppercase">25% Milestone</div>
                <div className="text-xl font-black text-white font-cinematic">
                  {funnelData.dropoff_milestones.reached_25}
                </div>
                <div className="text-[10px] text-amber-400 font-mono">Milestone reach</div>
              </div>

              <div className="p-3 rounded-[7px] bg-[#0B0C10] border border-cyan-500/20 space-y-1">
                <div className="text-[10px] font-bold text-cyan-400 uppercase">Continuation Intent</div>
                <div className="text-xl font-black text-white font-cinematic">
                  {funnelData.continuation_intent ?? 0}
                </div>
                <div className="text-[10px] text-cyan-400 font-mono">Next ep action</div>
              </div>

              <div className="p-3 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-1">
                <div className="text-[10px] font-bold text-welele-muted uppercase">Completion Rate</div>
                <div className="text-xl font-black text-emerald-400 font-cinematic">
                  {funnelData.completion_rate_pct ?? 0}%
                </div>
                <div className="text-[10px] text-emerald-400 font-mono">
                  {funnelData.completions ?? 0} completed
                </div>
              </div>

              <div className="p-3 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-1">
                <div className="text-[10px] font-bold text-welele-muted uppercase">Rewatches</div>
                <div className="text-xl font-black text-welele-gold font-cinematic">
                  {funnelData.rewatches ?? 0}
                </div>
                <div className="text-[10px] text-welele-gold font-mono">Repeat sessions</div>
              </div>
            </div>

            {/* Technical Disruption Correlation & Anomaly Detection Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Technical Disruption Ledger */}
              <div className="p-4 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-sky-400" />
                    Technical Disruption Correlation
                  </h4>
                  <span className="text-[10px] font-mono text-sky-400">
                    Stall Ratio: {funnelData.technical_disruptions?.stall_ratio_pct ?? 0}%
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2.5 rounded-[5px] bg-white/5">
                    <div className="text-welele-muted text-[10px]">Buffer Events</div>
                    <div className="text-lg font-black text-white font-cinematic">
                      {funnelData.technical_disruptions?.total_buffer_events ?? 0}
                    </div>
                  </div>
                  <div className="p-2.5 rounded-[5px] bg-white/5">
                    <div className="text-welele-muted text-[10px]">Stall Events</div>
                    <div className="text-lg font-black text-amber-400 font-cinematic">
                      {funnelData.technical_disruptions?.total_stall_events ?? 0}
                    </div>
                  </div>
                  <div className="p-2.5 rounded-[5px] bg-white/5">
                    <div className="text-welele-muted text-[10px]">Disrupted Sessions</div>
                    <div className="text-lg font-black text-red-400 font-cinematic">
                      {funnelData.technical_disruptions?.sessions_with_disruptions ?? 0}
                    </div>
                  </div>
                </div>
                <p className="text-[11px] text-welele-muted">
                  Technical stalls are isolated from editorial drop-offs to prevent mistaking network degradation for creative audience rejection.
                </p>
              </div>

              {/* Retention Anomaly Classifier */}
              <div className="p-4 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    Disambiguated Retention Anomalies
                  </h4>
                  <span className="text-[10px] font-mono text-welele-muted">
                    {funnelData.detected_anomalies?.length ?? 0} Detected
                  </span>
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto text-xs pr-1">
                  {!funnelData.detected_anomalies || funnelData.detected_anomalies.length === 0 ? (
                    <div className="py-6 text-center text-welele-muted text-xs">
                      No anomalous drop-offs (&gt;=10% interval drop) detected.
                    </div>
                  ) : (
                    funnelData.detected_anomalies.map((a) => (
                      <div
                        key={a.anomaly_id}
                        className={`p-2.5 rounded-[6px] border text-xs space-y-1 ${
                          a.classification === 'RETENTION_ANOMALY_WITH_TECHNICAL_CORRELATION'
                            ? 'bg-sky-950/20 border-sky-500/30 text-sky-200'
                            : 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-[11px]">
                            {a.second_start}s – {a.second_end}s
                          </span>
                          <span
                            className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-black uppercase ${
                              a.classification === 'RETENTION_ANOMALY_WITH_TECHNICAL_CORRELATION'
                                ? 'bg-sky-500/20 text-sky-300'
                                : 'bg-amber-500/20 text-amber-300'
                            }`}
                          >
                            {a.classification === 'RETENTION_ANOMALY_WITH_TECHNICAL_CORRELATION'
                              ? 'TECHNICAL CORRELATION'
                              : 'CLEAN PLAYBACK DROP'}
                          </span>
                        </div>
                        <p className="text-[11px] opacity-90">{a.description}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Granular Retention Curve */}
            {funnelData.retention_curve && funnelData.retention_curve.length > 0 && (
              <div className="p-4 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-emerald-400" />
                    Second-by-Second Empirical Retention Curve
                  </h4>
                  <span className="text-[10px] font-mono text-welele-muted">5s Interval Granularity</span>
                </div>
                <div className="h-28 flex items-end gap-1.5 pt-4 pb-2 px-1 border-b border-white/10 overflow-x-auto">
                  {funnelData.retention_curve.map((sample) => (
                    <div
                      key={sample.second}
                      className="flex-1 min-w-[20px] flex flex-col items-center gap-1 group relative cursor-pointer"
                      title={`${sample.second}s: ${sample.retention_pct}% (${sample.active_viewers} viewers, ${sample.stalls_at_interval} stalls)`}
                    >
                      <div className="w-full bg-white/5 h-20 rounded-t flex items-end overflow-hidden">
                        <div
                          className={`w-full rounded-t transition-all ${
                            sample.stalls_at_interval > 0
                              ? 'bg-sky-400'
                              : sample.is_cliffhanger_window
                              ? 'bg-amber-400'
                              : 'bg-emerald-400'
                          }`}
                          style={{ height: `${sample.retention_pct}%` }}
                        />
                      </div>
                      <span className="text-[8px] font-mono text-welele-muted">{sample.second}s</span>
                    </div>
                  ))}
                </div>
                <div className="flex items-center justify-between text-[10px] text-welele-muted font-mono pt-1">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
                      Clean Retention
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-sky-400 inline-block" />
                      Buffer Stall at Interval
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />
                      Cliffhanger Window (60s+)
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
