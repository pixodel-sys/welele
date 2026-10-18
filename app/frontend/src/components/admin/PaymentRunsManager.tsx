import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/api';
import {
  DollarSign,
  Download,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldAlert,
  FileText,
  Lock,
  RefreshCw,
  Plus,
  Eye,
  XCircle,
  FileSpreadsheet,
  Check,
  Building,
  CreditCard,
  UserCheck
} from 'lucide-react';

interface PaymentRun {
  id: string;
  run_reference: string;
  period_start: string;
  period_end: string;
  currency: string;
  payout_count: number;
  total_amount: number;
  status: string;
  created_by: string;
  created_at: string;
  approved_by?: string | null;
  approved_at?: string | null;
  exported_at?: string | null;
  export_file_hash_sha256?: string | null;
  idempotency_key: string;
  metadata?: any;
}

interface PaymentRunItem {
  id: string;
  payment_run_id: string;
  payout_id: string;
  creator_id: string;
  statement_id?: string | null;
  amount: number;
  currency: string;
  status: string;
  beneficiary_name_snapshot: string;
  bank_name_snapshot: string;
  account_number_snapshot: string;
  branch_code_snapshot: string;
  account_type_snapshot: string;
  payment_reference_snapshot: string;
  external_payment_reference?: string | null;
  failure_reason?: string | null;
  created_at: string;
}

export const PaymentRunsManager: React.FC = () => {
  const [runs, setRuns] = useState<PaymentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<any | null>(null);
  const [exceptions, setExceptions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [subTab, setSubTab] = useState<'runs' | 'exceptions'>('runs');
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Create Run Modal
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [createForm, setCreateForm] = useState({
    period_start: new Date(Date.now() - 7 * 86400000).toISOString().split('T')[0],
    period_end: new Date().toISOString().split('T')[0],
    currency: 'ZAR'
  });

  // Record Results Modal
  const [showResultsModal, setShowResultsModal] = useState<boolean>(false);
  const [resultItem, setResultItem] = useState<{
    payout_id: string;
    status: 'SUCCESS' | 'FAILED';
    external_payment_reference: string;
    failure_reason: string;
    amount?: number;
  } | null>(null);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      const res = await adminApi.listPaymentRuns({ limit: 50 });
      setRuns(res.runs || []);
    } catch (err: any) {
      console.error('Failed to fetch payment runs', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchExceptions = async () => {
    try {
      const res = await adminApi.getPaymentRunExceptions();
      setExceptions(res.unreconciled_runs || []);
    } catch (err: any) {
      console.error('Failed to fetch exceptions', err);
    }
  };

  useEffect(() => {
    fetchRuns();
    fetchExceptions();
  }, []);

  const handleSelectRun = async (runId: string) => {
    try {
      setActionLoading(true);
      const detail = await adminApi.getPaymentRunDetail(runId);
      setSelectedRun(detail);
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to load run detail' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateRun = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      const res = await adminApi.createPaymentRun({
        period_start: new Date(createForm.period_start).toISOString(),
        period_end: new Date(createForm.period_end + 'T23:59:59Z').toISOString(),
        currency: createForm.currency,
        idempotency_key: `run_ui_${Date.now()}`
      });
      setFeedback({ type: 'success', message: res.message || 'Payment run created successfully.' });
      setShowCreateModal(false);
      fetchRuns();
      if (res.run) {
        handleSelectRun(res.run.id);
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to create payment run' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitForReview = async (runId: string) => {
    try {
      setActionLoading(true);
      await adminApi.submitPaymentRunForReview(runId);
      setFeedback({ type: 'success', message: 'Payment run submitted for supervisor review.' });
      handleSelectRun(runId);
      fetchRuns();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to submit run for review' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprove = async (runId: string) => {
    try {
      setActionLoading(true);
      await adminApi.approvePaymentRun(runId);
      setFeedback({ type: 'success', message: 'Payment run APPROVED under dual-control authorization.' });
      handleSelectRun(runId);
      fetchRuns();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to approve payment run' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async (runId: string) => {
    if (!confirm('Are you sure you want to cancel this payment run? Included payouts will be returned to PENDING.')) {
      return;
    }
    try {
      setActionLoading(true);
      await adminApi.cancelPaymentRun(runId, 'Operator cancelled via Admin Console');
      setFeedback({ type: 'success', message: 'Payment run cancelled.' });
      handleSelectRun(runId);
      fetchRuns();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to cancel payment run' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleExport = async (runId: string, runRef: string) => {
    try {
      setActionLoading(true);
      const res = await adminApi.exportPaymentRun(runId);
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${runRef}_FNB_Payments.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      const sha = res.headers ? res.headers['x-export-sha256'] : 'Computed';
      const hashTotal = res.headers ? res.headers['x-fnb-hash-total'] : '';
      const hashMsg = hashTotal ? ` | FNB Hash Total: ${hashTotal}` : '';
      setFeedback({ type: 'success', message: `FNB Payments CSV downloaded. SHA-256: ${sha}${hashMsg}` });
      handleSelectRun(runId);
      fetchRuns();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to export payment run' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRecordResultSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRun || !resultItem) return;
    try {
      setActionLoading(true);
      const res = await adminApi.recordPaymentRunResults(selectedRun.id, [
        {
          payout_id: resultItem.payout_id,
          status: resultItem.status,
          external_payment_reference: resultItem.external_payment_reference,
          failure_reason: resultItem.failure_reason,
          amount: resultItem.amount,
          settled_at: new Date().toISOString()
        }
      ]);
      setFeedback({ type: 'success', message: `Result recorded: ${resultItem.status}. Payout updated.` });
      setShowResultsModal(false);
      setResultItem(null);
      handleSelectRun(selectedRun.id);
      fetchRuns();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Failed to record external result' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleReconcile = async (runId: string) => {
    try {
      setActionLoading(true);
      const res = await adminApi.reconcilePaymentRun(runId);
      if (res.is_clean) {
        setFeedback({ type: 'success', message: `Reconciliation PASS: Run verified 100% clean across all accounting layers.` });
      } else {
        setFeedback({ type: 'error', message: `Reconciliation FAIL: ${res.exceptions?.length} exceptions found.` });
      }
      handleSelectRun(runId);
      fetchRuns();
      fetchExceptions();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err?.response?.data?.detail || 'Reconciliation failed' });
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">DRAFT</span>;
      case 'UNDER_REVIEW':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">UNDER REVIEW</span>;
      case 'APPROVED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">APPROVED</span>;
      case 'EXPORTED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">EXPORTED</span>;
      case 'AWAITING_EXTERNAL_RESULT':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30">AWAITING RESULTS</span>;
      case 'RESULTS_RECORDED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-500/20 text-teal-400 border border-teal-500/30">RESULTS RECORDED</span>;
      case 'RECONCILED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500 text-black border border-emerald-400 font-black">RECONCILED</span>;
      case 'CANCELLED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">CANCELLED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white/10 text-white">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-4 rounded-[7px] bg-gradient-to-r from-emerald-950/30 via-welele-surface-2 to-welele-surface border border-emerald-500/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-black text-white font-cinematic">Commercial Payment Operations</h2>
            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              WORKSTREAM 6I-G.4.2
            </span>
          </div>
          <p className="text-xs text-welele-muted mt-1">
            Human-in-the-Loop Creator Payment Run Layer. Dual-control approval, immutable snapshots, and verified settlement reconciliation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              fetchRuns();
              fetchExceptions();
            }}
            className="px-3 py-1.5 rounded-[7px] text-xs font-bold bg-white/5 hover:bg-white/10 text-white border border-white/10 flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3.5 py-1.5 rounded-[7px] text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-black shadow-lg flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4 font-black" />
            Prepare Payment Run
          </button>
        </div>
      </div>

      {/* Notifications */}
      {feedback && (
        <div
          className={`p-3.5 rounded-[7px] text-xs font-bold flex items-center justify-between border ${
            feedback.type === 'success'
              ? 'bg-emerald-950/40 text-emerald-300 border-emerald-500/30'
              : 'bg-rose-950/40 text-rose-300 border-rose-500/30'
          }`}
        >
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="text-welele-muted hover:text-white">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Sub-tabs */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-2">
        <button
          onClick={() => setSubTab('runs')}
          className={`px-4 py-1.5 rounded-[7px] text-xs font-bold transition-all ${
            subTab === 'runs'
              ? 'bg-emerald-500 text-black'
              : 'text-welele-muted hover:text-white hover:bg-white/5'
          }`}
        >
          Payment Runs ({runs.length})
        </button>
        <button
          onClick={() => setSubTab('exceptions')}
          className={`px-4 py-1.5 rounded-[7px] text-xs font-bold transition-all flex items-center gap-1.5 ${
            subTab === 'exceptions'
              ? 'bg-rose-500 text-white'
              : 'text-welele-muted hover:text-white hover:bg-white/5'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          Exceptions ({exceptions.length})
        </button>
      </div>

      {/* Sub-tab 1: Payment Runs List */}
      {subTab === 'runs' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Runs Table */}
          <div className="lg:col-span-1 space-y-3">
            <div className="text-xs font-bold text-welele-muted uppercase tracking-wider">
              Recorded Payment Runs
            </div>
            {loading ? (
              <div className="p-8 text-center text-xs text-welele-muted">Loading runs...</div>
            ) : runs.length === 0 ? (
              <div className="p-6 rounded-[7px] bg-welele-surface-2 border border-white/5 text-center space-y-2">
                <p className="text-xs text-welele-muted">No creator payment runs recorded yet.</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-3 py-1.5 rounded-[7px] text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                >
                  Create First Run
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {runs.map((r) => {
                  const isSelected = selectedRun && selectedRun.id === r.id;
                  return (
                    <div
                      key={r.id}
                      onClick={() => handleSelectRun(r.id)}
                      className={`p-3.5 rounded-[7px] border cursor-pointer transition-all space-y-2 ${
                        isSelected
                          ? 'bg-emerald-950/30 border-emerald-500 shadow-md'
                          : 'bg-welele-surface-2 border-white/5 hover:border-white/20'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-white">{r.run_reference}</span>
                        {getStatusBadge(r.status)}
                      </div>
                      <div className="flex items-center justify-between text-xs text-welele-muted">
                        <span>{r.payout_count} payouts</span>
                        <span className="font-bold text-white">R{Number(r.total_amount).toFixed(2)}</span>
                      </div>
                      <div className="text-[10px] text-welele-muted flex items-center justify-between">
                        <span>By: {r.created_by}</span>
                        <span>{new Date(r.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Selected Run Details */}
          <div className="lg:col-span-2">
            {selectedRun ? (
              <div className="p-5 rounded-[7px] bg-welele-surface-2 border border-white/10 space-y-5">
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-white font-mono">{selectedRun.run_reference}</h3>
                      {getStatusBadge(selectedRun.status)}
                    </div>
                    <p className="text-xs text-welele-muted mt-0.5">
                      Period: {new Date(selectedRun.period_start).toLocaleDateString()} — {new Date(selectedRun.period_end).toLocaleDateString()}
                    </p>
                  </div>

                  {/* Contextual Actions */}
                  <div className="flex items-center gap-2 flex-wrap">
                    {selectedRun.status === 'DRAFT' && (
                      <>
                        <button
                          disabled={actionLoading}
                          onClick={() => handleSubmitForReview(selectedRun.id)}
                          className="px-3 py-1.5 rounded-[7px] text-xs font-bold bg-sky-500 hover:bg-sky-400 text-black shadow"
                        >
                          Submit for Review
                        </button>
                        <button
                          disabled={actionLoading}
                          onClick={() => handleCancel(selectedRun.id)}
                          className="px-3 py-1.5 rounded-[7px] text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30"
                        >
                          Cancel Run
                        </button>
                      </>
                    )}

                    {selectedRun.status === 'UNDER_REVIEW' && (
                      <>
                        <button
                          disabled={actionLoading}
                          onClick={() => handleApprove(selectedRun.id)}
                          className="px-3 py-1.5 rounded-[7px] text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-black shadow flex items-center gap-1.5"
                        >
                          <Check className="w-3.5 h-3.5 font-black" />
                          Approve (Dual Control)
                        </button>
                        <button
                          disabled={actionLoading}
                          onClick={() => handleCancel(selectedRun.id)}
                          className="px-3 py-1.5 rounded-[7px] text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30"
                        >
                          Cancel Run
                        </button>
                      </>
                    )}

                    {['APPROVED', 'EXPORTED'].includes(selectedRun.status) && (
                      <button
                        disabled={actionLoading}
                        onClick={() => handleExport(selectedRun.id, selectedRun.run_reference)}
                        className="px-3 py-1.5 rounded-[7px] text-xs font-bold bg-indigo-500 hover:bg-indigo-400 text-white shadow flex items-center gap-1.5"
                      >
                        <Download className="w-3.5 h-3.5" />
                        Export Bank File
                      </button>
                    )}

                    <button
                      disabled={actionLoading}
                      onClick={() => handleReconcile(selectedRun.id)}
                      className="px-3 py-1.5 rounded-[7px] text-xs font-bold bg-white/5 hover:bg-white/10 text-white border border-white/10 flex items-center gap-1.5"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Forensic Reconcile
                    </button>
                  </div>
                </div>

                {/* KPI Metadata Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-[7px] bg-welele-surface border border-white/5">
                    <span className="text-[10px] text-welele-muted">Total Amount</span>
                    <div className="text-base font-bold text-white mt-0.5">
                      R{Number(selectedRun.total_amount).toFixed(2)}
                    </div>
                  </div>
                  <div className="p-3 rounded-[7px] bg-welele-surface border border-white/5">
                    <span className="text-[10px] text-welele-muted">Payout Count</span>
                    <div className="text-base font-bold text-white mt-0.5">
                      {selectedRun.payout_count} Instructions
                    </div>
                  </div>
                  <div className="p-3 rounded-[7px] bg-welele-surface border border-white/5">
                    <span className="text-[10px] text-welele-muted">Prepared By</span>
                    <div className="text-xs font-mono text-white mt-1 truncate">
                      {selectedRun.created_by}
                    </div>
                  </div>
                  <div className="p-3 rounded-[7px] bg-welele-surface border border-white/5">
                    <span className="text-[10px] text-welele-muted">Approved By</span>
                    <div className="text-xs font-mono text-emerald-400 mt-1 truncate">
                      {selectedRun.approved_by || 'Awaiting Review'}
                    </div>
                  </div>
                </div>

                {/* Export Hash & Audit */}
                {selectedRun.export_file_hash_sha256 && (
                  <div className="p-3 rounded-[7px] bg-indigo-950/30 border border-indigo-500/30 flex items-center justify-between gap-2 text-xs">
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1">
                        <Lock className="w-3 h-3" />
                        Deterministic SHA-256 Digest
                      </span>
                      <div className="font-mono text-[11px] text-white break-all">
                        {selectedRun.export_file_hash_sha256}
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-indigo-500/20 text-indigo-300">
                      PERSISTED
                    </span>
                  </div>
                )}

                {/* Items Membership Table */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-bold text-welele-muted">
                    <span>Included Payout Snapshot Membership ({selectedRun.items?.length || 0})</span>
                    <span className="text-[10px] text-emerald-400 font-normal">
                      Account numbers masked for privacy
                    </span>
                  </div>

                  <div className="overflow-x-auto border border-white/5 rounded-[7px]">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-white/5 text-welele-muted text-[10px] uppercase font-bold">
                        <tr>
                          <th className="p-2.5">Creator / Beneficiary</th>
                          <th className="p-2.5">Bank & Destination</th>
                          <th className="p-2.5">Amount</th>
                          <th className="p-2.5">Item Status</th>
                          <th className="p-2.5">External Ref</th>
                          <th className="p-2.5 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {selectedRun.items?.map((item: PaymentRunItem) => (
                          <tr key={item.id} className="hover:bg-white/5">
                            <td className="p-2.5">
                              <div className="font-bold text-white">{item.beneficiary_name_snapshot}</div>
                              <div className="text-[10px] font-mono text-welele-muted">{item.creator_id}</div>
                            </td>
                            <td className="p-2.5">
                              <div className="text-white">{item.bank_name_snapshot}</div>
                              <div className="text-[10px] font-mono text-welele-muted">
                                {item.account_number_snapshot} ({item.branch_code_snapshot})
                              </div>
                            </td>
                            <td className="p-2.5 font-bold text-white">
                              R{Number(item.amount).toFixed(2)}
                            </td>
                            <td className="p-2.5">
                              <span
                                className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                                  item.status === 'PAID'
                                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                    : item.status === 'FAILED'
                                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                    : 'bg-white/10 text-welele-muted'
                                }`}
                              >
                                {item.status}
                              </span>
                            </td>
                            <td className="p-2.5 font-mono text-[10px] text-welele-muted">
                              {item.external_payment_reference || '—'}
                            </td>
                            <td className="p-2.5 text-right">
                              {item.status !== 'PAID' && (
                                <button
                                  onClick={() => {
                                    setResultItem({
                                      payout_id: item.payout_id,
                                      status: 'SUCCESS',
                                      external_payment_reference: `EFT-${Date.now()}`,
                                      failure_reason: '',
                                      amount: item.amount
                                    });
                                    setShowResultsModal(true);
                                  }}
                                  className="px-2 py-1 rounded text-[10px] font-bold bg-white/5 hover:bg-white/10 text-white border border-white/10"
                                >
                                  Record Result
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-12 rounded-[7px] bg-welele-surface-2 border border-white/5 text-center text-xs text-welele-muted space-y-2">
                <FileSpreadsheet className="w-8 h-8 text-welele-muted mx-auto" />
                <p>Select a payment run on the left to inspect immutable snapshot items and trigger operations.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sub-tab 2: Exceptions */}
      {subTab === 'exceptions' && (
        <div className="space-y-4">
          <div className="p-4 rounded-[7px] bg-welele-surface-2 border border-white/5 flex items-center justify-between">
            <span className="text-xs font-bold text-white">
              Actionable Commercial Exceptions & Mismatches
            </span>
            <button
              onClick={fetchExceptions}
              className="px-3 py-1.5 rounded-[7px] text-xs font-bold bg-white/5 hover:bg-white/10 text-white border border-white/10 flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Re-scan Exceptions
            </button>
          </div>

          {exceptions.length === 0 ? (
            <div className="p-10 rounded-[7px] bg-emerald-950/20 border border-emerald-500/30 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
              <p className="text-xs font-bold text-emerald-300">
                Zero exceptions detected. All payment runs and ledger allocations are in strict balance.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {exceptions.map((ex, i) => (
                <div key={i} className="p-4 rounded-[7px] bg-rose-950/30 border border-rose-500/30 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-rose-300">{ex.run_reference}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400">
                      ACTION REQUIRED
                    </span>
                  </div>
                  <ul className="list-disc list-inside text-xs text-rose-200/80 space-y-1">
                    {ex.exceptions?.map((err: string, j: number) => (
                      <li key={j}>{err}</li>
                    ))}
                  </ul>
                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={() => handleReconcile(ex.run_id)}
                      className="px-3 py-1 rounded text-xs font-bold bg-rose-500 hover:bg-rose-400 text-white"
                    >
                      Re-verify Run
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal: Prepare Payment Run */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-welele-surface-2 border border-white/10 rounded-[7px] p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-emerald-400" />
                Prepare New Creator Payment Run
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-welele-muted hover:text-white">
                <XCircle className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateRun} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-welele-muted">Period Start</label>
                <input
                  type="date"
                  value={createForm.period_start}
                  onChange={(e) => setCreateForm({ ...createForm, period_start: e.target.value })}
                  required
                  className="w-full p-2 rounded bg-welele-surface border border-white/10 text-white"
                />
              </div>

              <div className="space-y-1">
                <label className="text-welele-muted">Period End</label>
                <input
                  type="date"
                  value={createForm.period_end}
                  onChange={(e) => setCreateForm({ ...createForm, period_end: e.target.value })}
                  required
                  className="w-full p-2 rounded bg-welele-surface border border-white/10 text-white"
                />
              </div>

              <div className="space-y-1">
                <label className="text-welele-muted">Settlement Currency</label>
                <input
                  type="text"
                  value={createForm.currency}
                  disabled
                  className="w-full p-2 rounded bg-welele-surface/50 border border-white/10 text-welele-muted font-bold"
                />
              </div>

              <div className="p-3 rounded bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300">
                Notice: A payment run includes only existing creator payout requests in PENDING status. It will not sweep balances automatically.
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 rounded text-xs font-bold text-welele-muted hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 rounded text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-black shadow"
                >
                  {actionLoading ? 'Creating...' : 'Create Draft Run'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Record External Result */}
      {showResultsModal && resultItem && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-welele-surface-2 border border-white/10 rounded-[7px] p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-emerald-400" />
                Record External Execution Result
              </h3>
              <button onClick={() => setShowResultsModal(false)} className="text-welele-muted hover:text-white">
                <XCircle className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleRecordResultSubmit} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-welele-muted">Execution Status</label>
                <select
                  value={resultItem.status}
                  onChange={(e) => setResultItem({ ...resultItem, status: e.target.value as any })}
                  className="w-full p-2 rounded bg-welele-surface border border-white/10 text-white font-bold"
                >
                  <option value="SUCCESS">SUCCESS (Disbursement Verified)</option>
                  <option value="FAILED">FAILED (Disbursement Rejected by Bank)</option>
                </select>
              </div>

              {resultItem.status === 'SUCCESS' ? (
                <div className="space-y-1">
                  <label className="text-welele-muted">Bank External Reference (Required)</label>
                  <input
                    type="text"
                    required
                    value={resultItem.external_payment_reference}
                    onChange={(e) => setResultItem({ ...resultItem, external_payment_reference: e.target.value })}
                    placeholder="e.g. FNB-EFT-98721345"
                    className="w-full p-2 rounded bg-welele-surface border border-white/10 text-white font-mono"
                  />
                </div>
              ) : (
                <div className="space-y-1">
                  <label className="text-welele-muted">Failure Reason</label>
                  <input
                    type="text"
                    required
                    value={resultItem.failure_reason}
                    onChange={(e) => setResultItem({ ...resultItem, failure_reason: e.target.value })}
                    placeholder="e.g. Invalid account number / Branch mismatch"
                    className="w-full p-2 rounded bg-welele-surface border border-white/10 text-white"
                  />
                </div>
              )}

              <div className="p-3 rounded bg-white/5 border border-white/10 text-[11px] text-welele-muted">
                Authoritative settlement boundary: SUCCESS moves payout to PAID only upon valid reference and matching amount. FAILED preserves creator ledger earnings.
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowResultsModal(false)}
                  className="px-3 py-1.5 rounded text-xs font-bold text-welele-muted hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 rounded text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-black shadow"
                >
                  {actionLoading ? 'Recording...' : 'Commit External Result'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
