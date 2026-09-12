import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/api';
import { ProvenanceBadge } from '../common/patterns/ProvenanceBadge';
import {
  ShieldCheck,
  Lock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Hash,
  Clock,
  User,
  Activity,
  Layers,
  Search,
  Filter
} from 'lucide-react';

interface AuditLogEntry {
  sequence_id: number;
  event_id: string;
  domain: 'AUTH' | 'IP' | 'CONTENT' | 'COMMERCE' | 'EXPERIENCE' | 'SECURITY' | string;
  event_type: string;
  actor_id: string;
  actor_role: string;
  target_type: string;
  target_id: string;
  before_state?: Record<string, any>;
  after_state?: Record<string, any>;
  metadata?: Record<string, any>;
  payload_hash: string;
  previous_hash: string;
  entry_hash: string;
  timestamp: string;
}

interface VerificationResult {
  valid: boolean;
  total_blocks_verified: number;
  chain_head_hash: string;
  tampered_blocks: number[];
  verified_at: string;
}

export const AuditChainInspector: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [domainFilter, setDomainFilter] = useState<string>('ALL');
  const [selectedEntry, setSelectedEntry] = useState<AuditLogEntry | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [logsRes, verifyRes] = await Promise.all([
        adminApi.getAuditLogs({ limit: 100 }),
        adminApi.verifyAuditChain(),
      ]);
      setLogs(logsRes?.logs || []);
      setVerification(verifyRes?.verification || null);
    } catch (err) {
      console.error('Failed to load audit chain:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await adminApi.verifyAuditChain();
      setVerification(res?.verification || null);
    } catch (err) {
      console.error('Audit verification error:', err);
    } finally {
      setVerifying(false);
    }
  };

  const filteredLogs = logs.filter((log) => {
    if (domainFilter === 'ALL') return true;
    return log.domain === domainFilter;
  });

  const domains = ['ALL', 'AUTH', 'IP', 'CONTENT', 'COMMERCE', 'EXPERIENCE', 'SECURITY'];

  if (loading) {
    return (
      <div className="p-12 text-center text-welele-muted flex flex-col items-center justify-center gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-emerald-400" />
        <span className="text-sm font-mono">Traversing Cryptographic Audit Chain...</span>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header & Cryptographic Health Ribbon */}
      <div className="p-5 rounded-[7px] bg-[#0E1117] border border-emerald-500/30 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-[7px] bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0">
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-white font-cinematic">
                SHA-256 Cryptographic Audit Ledger
              </h3>
              <ProvenanceBadge tier="SYSTEM_DERIVED" size="sm" label="IMMUTABLE HASH CHAIN" />
            </div>
            <p className="text-xs text-welele-muted mt-0.5">
              Append-only security log covering all Auth, IP, Content, Commerce & Experience mutations.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-end">
          <div className="text-right font-mono">
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-bold">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{verification?.valid ? 'CHAIN 100% VALID' : 'CHAIN TAMPER DETECTED'}</span>
            </div>
            <span className="text-[10px] text-welele-muted">
              {verification?.total_blocks_verified || logs.length} Blocks Cryptographically Verified
            </span>
          </div>

          <button
            onClick={handleVerifyChain}
            disabled={verifying}
            className="px-3.5 py-2 rounded-[7px] bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 font-mono text-xs font-bold border border-emerald-500/40 flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
            <span>{verifying ? 'Verifying...' : 'Recalculate Hashes'}</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex flex-wrap gap-1 bg-[#14151B] p-1 rounded-[7px] border border-white/5 text-xs">
          {domains.map((d) => (
            <button
              key={d}
              onClick={() => setDomainFilter(d)}
              className={`px-2.5 py-1 rounded-[5px] font-mono text-[11px] font-bold uppercase transition-all ${
                domainFilter === d
                  ? 'bg-emerald-500 text-black shadow-sm'
                  : 'text-welele-muted hover:text-white'
              }`}
            >
              {d}
            </button>
          ))}
        </div>

        <span className="text-[11px] text-welele-muted font-mono">
          Showing {filteredLogs.length} of {logs.length} Recorded Blocks
        </span>
      </div>

      {/* Audit Blocks Table */}
      <div className="rounded-[7px] bg-[#0B0C10] border border-white/5 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#14151B] text-[10px] uppercase tracking-wider text-welele-muted border-b border-white/5">
              <tr>
                <th className="p-3">Seq #</th>
                <th className="p-3">Domain & Event</th>
                <th className="p-3">Actor</th>
                <th className="p-3">Target</th>
                <th className="p-3">Block Hash (SHA-256)</th>
                <th className="p-3">Timestamp (UTC)</th>
                <th className="p-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredLogs.map((entry) => {
                const isGenesis = entry.sequence_id === 1;
                return (
                  <tr
                    key={entry.event_id || entry.sequence_id}
                    className="hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="p-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          isGenesis
                            ? 'bg-welele-gold/20 text-welele-gold border border-welele-gold/30'
                            : 'bg-white/10 text-white'
                        }`}
                      >
                        #{entry.sequence_id}
                      </span>
                    </td>
                    <td className="p-3">
                      <div className="space-y-0.5">
                        <span className="px-1.5 py-0.2 rounded text-[9px] font-extrabold uppercase bg-sky-500/20 text-sky-400 border border-sky-500/30">
                          {entry.domain}
                        </span>
                        <p className="text-[11px] text-white font-bold truncate max-w-[200px]">
                          {entry.event_type}
                        </p>
                      </div>
                    </td>
                    <td className="p-3 text-welele-muted">
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3 text-emerald-400" />
                        <span className="text-white truncate max-w-[120px]">{entry.actor_id}</span>
                        <span className="text-[9px] text-welele-muted">({entry.actor_role})</span>
                      </div>
                    </td>
                    <td className="p-3 text-welele-muted">
                      <span className="text-white truncate max-w-[140px] block">
                        {entry.target_type}: {entry.target_id}
                      </span>
                    </td>
                    <td className="p-3">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-1 text-[10px] text-emerald-400" title={entry.entry_hash}>
                          <Hash className="w-3 h-3 text-emerald-500 shrink-0" />
                          <span className="truncate max-w-[130px]">{entry.entry_hash}</span>
                        </div>
                        <div className="text-[9px] text-welele-muted truncate max-w-[130px]" title={`Prev: ${entry.previous_hash}`}>
                          prev: {entry.previous_hash.slice(0, 12)}...
                        </div>
                      </div>
                    </td>
                    <td className="p-3 text-welele-muted text-[10px] whitespace-nowrap">
                      {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => setSelectedEntry(entry)}
                        className="px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-white text-[10px] font-bold border border-white/10 transition-all cursor-pointer"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Entry Modal Detail */}
      {selectedEntry && (
        <div className="fixed inset-0 z-[999] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-2xl bg-[#0F1117] border border-emerald-500/30 rounded-[7px] p-6 space-y-4 shadow-2xl font-mono text-xs max-h-[85vh] overflow-y-auto animate-scale-up">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white">Block #{selectedEntry.sequence_id} Inspector</span>
                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-sky-500/20 text-sky-400">
                  {selectedEntry.domain}
                </span>
              </div>
              <button
                onClick={() => setSelectedEntry(null)}
                className="w-7 h-7 rounded bg-white/10 hover:bg-white/20 text-white flex items-center justify-center cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-[11px]">
              <div className="p-3 rounded bg-black/40 border border-white/5 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-welele-muted">Event Identifier:</span>
                  <span className="text-white">{selectedEntry.event_id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-welele-muted">Event Type:</span>
                  <span className="text-emerald-400 font-bold">{selectedEntry.event_type}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-welele-muted">Actor:</span>
                  <span className="text-white">{selectedEntry.actor_id} ({selectedEntry.actor_role})</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-welele-muted">Target:</span>
                  <span className="text-white">{selectedEntry.target_type} / {selectedEntry.target_id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-welele-muted">Timestamp:</span>
                  <span className="text-white">{selectedEntry.timestamp}</span>
                </div>
              </div>

              {/* Cryptographic Hashes */}
              <div className="p-3 rounded bg-black/40 border border-emerald-500/20 space-y-2">
                <div className="text-[10px] font-bold uppercase text-emerald-400">Cryptographic Hashes</div>
                <div className="space-y-1 text-[10px]">
                  <div>
                    <span className="text-welele-muted block">Entry Hash:</span>
                    <span className="text-emerald-300 break-all select-all">{selectedEntry.entry_hash}</span>
                  </div>
                  <div>
                    <span className="text-welele-muted block">Previous Block Hash:</span>
                    <span className="text-sky-300 break-all select-all">{selectedEntry.previous_hash}</span>
                  </div>
                  <div>
                    <span className="text-welele-muted block">Payload Hash (Canonical SHA-256):</span>
                    <span className="text-amber-300 break-all select-all">{selectedEntry.payload_hash}</span>
                  </div>
                </div>
              </div>

              {/* Payload State */}
              <div className="p-3 rounded bg-black/40 border border-white/5 space-y-2">
                <div className="text-[10px] font-bold uppercase text-welele-muted">State Payload Diffs</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px]">
                  <div className="space-y-1">
                    <span className="text-rose-400 font-bold">Before State:</span>
                    <pre className="p-2 rounded bg-[#07080A] text-welele-muted overflow-x-auto text-[9px] max-h-32">
                      {JSON.stringify(selectedEntry.before_state, null, 2)}
                    </pre>
                  </div>
                  <div className="space-y-1">
                    <span className="text-emerald-400 font-bold">After State:</span>
                    <pre className="p-2 rounded bg-[#07080A] text-emerald-300 overflow-x-auto text-[9px] max-h-32">
                      {JSON.stringify(selectedEntry.after_state, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
