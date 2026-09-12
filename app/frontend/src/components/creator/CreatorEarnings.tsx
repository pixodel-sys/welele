import React, { useState } from 'react';
import { monetizationApi } from '../../services/api';
import { MoMoPayoutTransaction, PayoutRail } from '../../types';
import { ProvenanceBadge } from '../common/patterns/ProvenanceBadge';
import {
  Coins,
  ArrowLeft,
  Smartphone,
  CheckCircle2,
  DollarSign,
  Zap,
  Building,
  CreditCard,
  PhoneCall,
  ShieldCheck,
  TrendingUp,
  Clock,
  Download,
  FileText,
  Printer,
  X,
  ExternalLink,
  Info
} from 'lucide-react';

interface CreatorEarningsProps {
  onBack?: () => void;
}

export const CreatorEarnings: React.FC<CreatorEarningsProps> = ({ onBack }) => {
  const [payoutRail, setPayoutRail] = useState<PayoutRail>('momo');
  const [payoutProvider, setPayoutProvider] = useState('MTN Mobile Money (MoMo)');
  const [amountCoins, setAmountCoins] = useState<number>(50000);
  const [accountName, setAccountName] = useState('Sipho Dlamini');
  const [accountIdentifier, setAccountIdentifier] = useState('+27 83 555 0192');
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  // Available balance
  const [availableCoins, setAvailableCoins] = useState<number>(142500);

  // Invoice / Receipt Modal State
  const [selectedInvoice, setSelectedInvoice] = useState<MoMoPayoutTransaction | null>(null);

  // Transaction Ledger State
  const [transactions, setTransactions] = useState<MoMoPayoutTransaction[]>([
    {
      id: 'tx_98214',
      transaction_ref: 'WLE-MOMO-20260901-841',
      invoice_number: 'INV-2026-09-0012',
      creator_id: 'creator_1',
      creator_name: 'Sipho Dlamini',
      rail: 'momo',
      provider_name: 'MTN Mobile Money',
      account_identifier: '+27 83 555 0192',
      coins_redeemed: 50000,
      gross_amount_zar: 6500.0,
      platform_fee_zar: 325.0,
      tax_withholding_zar: 926.25,
      net_payout_zar: 5248.75,
      currency: 'ZAR',
      status: 'completed',
      created_at: '2026-09-01 14:22',
      settled_at: '2026-09-01 14:28'
    },
    {
      id: 'tx_98190',
      transaction_ref: 'WLE-MPESA-20260824-219',
      invoice_number: 'INV-2026-08-0094',
      creator_id: 'creator_1',
      creator_name: 'Sipho Dlamini',
      rail: 'mpesa',
      provider_name: 'Vodacom M-Pesa',
      account_identifier: '+27 72 444 8190',
      coins_redeemed: 30000,
      gross_amount_zar: 3900.0,
      platform_fee_zar: 195.0,
      tax_withholding_zar: 555.75,
      net_payout_zar: 3149.25,
      currency: 'ZAR',
      status: 'completed',
      created_at: '2026-08-24 10:15',
      settled_at: '2026-08-24 10:20'
    }
  ]);

  // Calculations
  const coinToZarRate = 0.13; // R0.13 per coin
  const grossZar = amountCoins * coinToZarRate;
  const platformFee = grossZar * 0.05; // 5% platform infrastructure
  const taxWithholding = (grossZar - platformFee) * 0.15; // 15% withholding
  const netZar = grossZar - platformFee - taxWithholding;
  const estimatedUsd = (netZar / 18.5).toFixed(2);

  const handleRequestPayout = async (e: React.FormEvent) => {
    e.preventDefault();
    if (amountCoins > availableCoins) {
      alert('Insufficient coin balance');
      return;
    }

    setIsProcessing(true);
    setStatusMsg(null);

    setTimeout(() => {
      const newTx: MoMoPayoutTransaction = {
        id: 'tx_' + Date.now().toString().slice(-5),
        transaction_ref: `WLE-${payoutRail.toUpperCase()}-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${Math.floor(Math.random() * 900 + 100)}`,
        invoice_number: `INV-2026-09-00${transactions.length + 13}`,
        creator_id: 'creator_1',
        creator_name: accountName,
        rail: payoutRail,
        provider_name: payoutProvider,
        account_identifier: accountIdentifier,
        coins_redeemed: amountCoins,
        gross_amount_zar: grossZar,
        platform_fee_zar: platformFee,
        tax_withholding_zar: taxWithholding,
        net_payout_zar: netZar,
        currency: 'ZAR',
        status: 'completed',
        created_at: new Date().toISOString().replace('T', ' ').slice(0, 16),
        settled_at: new Date().toISOString().replace('T', ' ').slice(0, 16)
      };

      setAvailableCoins((prev) => prev - amountCoins);
      setTransactions([newTx, ...transactions]);
      setSelectedInvoice(newTx);
      setIsProcessing(false);
      setStatusMsg(`Payout of R${netZar.toFixed(2)} ZAR dispatched successfully via ${payoutProvider}!`);
    }, 1200);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-24 text-white animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={onBack}
              className="w-9 h-9 rounded-[7px] bg-white/5 hover:bg-white/10 flex items-center justify-center text-white border border-white/10 transition-all"
              aria-label="Go Back"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-[10px] font-bold text-[#FF2A6D] uppercase tracking-wider">
                CREATOR REVENUE
              </span>
              <span className="text-xs text-welele-muted">•</span>
              <span className="text-xs text-welele-muted">African Telco Settlement Switch</span>
            </div>
            <h1 className="text-2xl font-black text-white font-cinematic uppercase tracking-tight">
              Earnings & MoMo Payouts Hub
            </h1>
          </div>
        </div>
      </div>

      {/* Revenue Snapshot Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-welele-muted">Unclaimed Coin Balance</span>
            <ProvenanceBadge tier="SYSTEM_DERIVED" size="sm" />
          </div>
          <div className="text-2xl font-black text-welele-gold font-cinematic">
            🪙 {availableCoins.toLocaleString()}
          </div>
          <div className="flex items-center justify-between text-[10px] text-welele-muted">
            <span>From viewer unlocks & gifts</span>
            <span className="text-emerald-400 font-bold">Min 1,000 coins met</span>
          </div>
        </div>

        <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-welele-muted">Est. Net Settlement Value</span>
            <ProvenanceBadge tier="SYSTEM_DERIVED" size="sm" />
          </div>
          <div className="text-2xl font-black text-emerald-400 font-cinematic">
            R {(availableCoins * coinToZarRate * 0.8).toLocaleString(undefined, { minimumFractionDigits: 2 })} ZAR
          </div>
          <span className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> (~${((availableCoins * coinToZarRate * 0.8) / 18.5).toFixed(2)} USD)
          </span>
        </div>

        <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-welele-muted">Telco Settlement SLA</span>
            <ProvenanceBadge tier="EXTERNAL_DATA" size="sm" />
          </div>
          <div className="text-2xl font-black text-white font-cinematic">Instant / &lt;10 mins</div>
          <span className="text-[10px] text-welele-muted">Automated MoMo & M-Pesa rails</span>
        </div>
      </div>

      {/* Carrier Settlement & Billing Disclosure Box */}
      <div className="p-4 rounded-[7px] bg-welele-surface-2 border border-sky-500/20 text-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-white">South African Telco & Airtime Pass Settlement Rules</span>
              <ProvenanceBadge tier="EXTERNAL_DATA" size="sm" />
            </div>
            <p className="text-[11px] text-welele-muted">
              Viewer micropayments made via MTN Airtime Pass or Vodacom Direct Carrier Billing are settled at standard SARB rates minus carrier pass shares. MoMo and Bank EFT payouts remit directly with 15% SARS tax withholding.
            </p>
          </div>
        </div>
        <div className="px-3 py-1 rounded-[7px] bg-sky-500/10 text-sky-300 text-[10px] font-mono border border-sky-500/30 whitespace-nowrap self-end md:self-center">
          Threshold: 1,000 Coins (R130 ZAR)
        </div>
      </div>

      {/* Payout Form */}
      <form
        onSubmit={handleRequestPayout}
        className="p-6 rounded-[7px] bg-[#14151B] border border-white/10 space-y-5 text-xs"
      >
        <h3 className="font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-[#FF2A6D]" />
          1. Select Mobile Money / Banking Rail
        </h3>

        {/* Adapter Selector */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <button
            type="button"
            onClick={() => {
              setPayoutRail('momo');
              setPayoutProvider('MTN Mobile Money (MoMo)');
            }}
            className={`p-4 rounded-[7px] text-left border transition-all ${
              payoutRail === 'momo'
                ? 'bg-yellow-500/15 border-yellow-500 text-white shadow'
                : 'bg-black/30 border-white/5 text-welele-muted hover:border-white/15'
            }`}
          >
            <Smartphone className="w-5 h-5 text-yellow-400 mb-2" />
            <div className="font-bold text-white text-xs">MTN MoMo</div>
            <p className="text-[10px] text-welele-muted mt-1">
              South Africa, Nigeria, Ghana, Uganda.
            </p>
          </button>

          <button
            type="button"
            onClick={() => {
              setPayoutRail('mpesa');
              setPayoutProvider('Vodacom M-Pesa');
            }}
            className={`p-4 rounded-[7px] text-left border transition-all ${
              payoutRail === 'mpesa'
                ? 'bg-red-500/15 border-red-500 text-white shadow'
                : 'bg-black/30 border-white/5 text-welele-muted hover:border-white/15'
            }`}
          >
            <Zap className="w-5 h-5 text-red-500 mb-2" />
            <div className="font-bold text-white text-xs">Vodacom M-Pesa</div>
            <p className="text-[10px] text-welele-muted mt-1">
              Kenya, Tanzania, Mozambique, SA.
            </p>
          </button>

          <button
            type="button"
            onClick={() => {
              setPayoutRail('chipper');
              setPayoutProvider('Chipper Cash Direct');
            }}
            className={`p-4 rounded-[7px] text-left border transition-all ${
              payoutRail === 'chipper'
                ? 'bg-purple-500/15 border-purple-500 text-white shadow'
                : 'bg-black/30 border-white/5 text-welele-muted hover:border-white/15'
            }`}
          >
            <CreditCard className="w-5 h-5 text-purple-400 mb-2" />
            <div className="font-bold text-white text-xs">Chipper Cash</div>
            <p className="text-[10px] text-welele-muted mt-1">
              Cross-border African multi-currency wallet.
            </p>
          </button>

          <button
            type="button"
            onClick={() => {
              setPayoutRail('bank');
              setPayoutProvider('Capitec / Standard Bank / FNB EFT');
            }}
            className={`p-4 rounded-[7px] text-left border transition-all ${
              payoutRail === 'bank'
                ? 'bg-emerald-500/15 border-emerald-500 text-white shadow'
                : 'bg-black/30 border-white/5 text-welele-muted hover:border-white/15'
            }`}
          >
            <Building className="w-5 h-5 text-emerald-400 mb-2" />
            <div className="font-bold text-white text-xs">Bank Wire EFT</div>
            <p className="text-[10px] text-welele-muted mt-1">
              Direct commercial bank transfer.
            </p>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-welele-muted block mb-1">Beneficiary Legal Name</label>
            <input
              type="text"
              value={accountName}
              onChange={(e) => setAccountName(e.target.value)}
              className="w-full bg-[#0B0C10] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-white focus:outline-none focus:border-welele-gold"
              required
            />
          </div>

          <div>
            <label className="text-welele-muted block mb-1">
              {payoutRail === 'bank'
                ? 'Bank Account Number / Branch Code'
                : 'MoMo / M-Pesa Phone Number (+27... / +234...)'}
            </label>
            <input
              type="text"
              value={accountIdentifier}
              onChange={(e) => setAccountIdentifier(e.target.value)}
              className="w-full bg-[#0B0C10] px-3.5 py-2.5 rounded-[7px] border border-white/10 text-white focus:outline-none focus:border-welele-gold"
              required
            />
          </div>
        </div>

        {/* Withdrawal Amount & Breakdown Calculator */}
        <div className="p-4 rounded-[7px] bg-[#0B0C10] border border-white/5 space-y-3">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <label className="text-welele-muted block mb-1">Withdrawal Amount (Coins)</label>
              <input
                type="number"
                min={1000}
                max={availableCoins}
                value={amountCoins}
                onChange={(e) => setAmountCoins(Number(e.target.value))}
                className="w-48 bg-[#14151B] px-3.5 py-2 rounded-[7px] border border-white/10 text-white font-bold focus:outline-none focus:border-welele-gold"
              />
            </div>

            <div className="text-right">
              <span className="text-[11px] text-welele-muted block">Net Payout to Your Wallet:</span>
              <span className="text-xl font-black text-emerald-400 font-cinematic">
                R {netZar.toFixed(2)} ZAR
              </span>
              <span className="text-[10px] text-welele-muted block font-mono">
                (~${estimatedUsd} USD)
              </span>
            </div>
          </div>

          {/* Fee & Tax Breakdown */}
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/5 text-[11px] text-welele-muted">
            <div>Gross Earnings: <strong className="text-white">R {grossZar.toFixed(2)}</strong></div>
            <div>Platform Fee (5%): <strong className="text-red-400">-R {platformFee.toFixed(2)}</strong></div>
            <div>SARS/Tax Withholding (15%): <strong className="text-red-400">-R {taxWithholding.toFixed(2)}</strong></div>
          </div>
        </div>

        {statusMsg && (
          <div className="p-3.5 rounded-[7px] bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{statusMsg}</span>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={isProcessing || amountCoins <= 0 || amountCoins > availableCoins}
          className="w-full py-3 rounded-[7px] bg-gradient-welele text-white font-bold text-xs shadow-lg shadow-orange-500/20 hover:brightness-110 active:scale-95 transition-all disabled:opacity-50"
        >
          {isProcessing ? 'Processing Telco Switch...' : `Dispatch Payout (R${netZar.toFixed(2)} ZAR via ${payoutProvider})`}
        </button>
      </form>

      {/* Payout History & Tax Invoices Ledger */}
      <div className="p-5 rounded-[7px] bg-[#14151B] border border-white/5 space-y-4">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FileText className="w-4 h-4 text-welele-gold" />
          Recent Payout Statements & Tax Invoices ({transactions.length})
        </h3>

        <div className="space-y-2">
          {transactions.map((tx) => (
            <div
              key={tx.id}
              className="p-3.5 rounded-[7px] bg-[#0B0C10] border border-white/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:border-white/15 transition-all text-xs"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white">{tx.provider_name}</span>
                  <span className="px-2 py-0.5 rounded-[7px] text-[10px] font-mono bg-emerald-500/20 text-emerald-400">
                    {tx.status.toUpperCase()}
                  </span>
                  <span className="text-welele-muted text-[10px] font-mono">{tx.invoice_number}</span>
                </div>
                <div className="text-[11px] text-welele-muted mt-0.5">
                  Ref: <span className="font-mono text-white/80">{tx.transaction_ref}</span> • {tx.account_identifier} • {tx.created_at}
                </div>
              </div>

              <div className="flex items-center gap-4 self-end sm:self-center">
                <div className="text-right">
                  <div className="font-bold text-emerald-400 font-cinematic text-sm">
                    +R {tx.net_payout_zar.toFixed(2)} ZAR
                  </div>
                  <div className="text-[10px] text-welele-muted">
                    🪙 {tx.coins_redeemed.toLocaleString()} coins
                  </div>
                </div>

                <button
                  onClick={() => setSelectedInvoice(tx)}
                  className="px-3 py-1.5 rounded-[7px] bg-white/5 hover:bg-white/10 text-white font-bold text-xs border border-white/10 flex items-center gap-1.5 transition-all"
                >
                  <FileText className="w-3.5 h-3.5 text-welele-gold" />
                  <span>Invoice</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* TAX INVOICE & RECEIPT MODAL */}
      {selectedInvoice && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-[7px] bg-[#14151B] border border-white/20 shadow-2xl p-6 space-y-5 text-white animate-scale-up">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-welele-gold" />
                <h3 className="text-base font-black uppercase tracking-wider font-cinematic">
                  Official Creator Payout Statement
                </h3>
              </div>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="p-1 rounded-[7px] hover:bg-white/10 text-welele-muted hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between text-welele-muted">
                <span>Invoice Number:</span>
                <span className="font-mono text-white font-bold">{selectedInvoice.invoice_number}</span>
              </div>
              <div className="flex justify-between text-welele-muted">
                <span>Transaction Reference:</span>
                <span className="font-mono text-white">{selectedInvoice.transaction_ref}</span>
              </div>
              <div className="flex justify-between text-welele-muted">
                <span>Settled Timestamp:</span>
                <span className="text-white">{selectedInvoice.settled_at || selectedInvoice.created_at}</span>
              </div>
              <div className="flex justify-between text-welele-muted">
                <span>Beneficiary:</span>
                <span className="text-white font-bold">{selectedInvoice.creator_name} ({selectedInvoice.account_identifier})</span>
              </div>
              <div className="flex justify-between text-welele-muted">
                <span>Payment Rail:</span>
                <span className="text-white">{selectedInvoice.provider_name}</span>
              </div>

              {/* Line items table */}
              <div className="mt-4 p-3.5 rounded-[7px] bg-black/40 border border-white/10 space-y-2">
                <div className="flex justify-between">
                  <span>Coins Redeemed:</span>
                  <span className="font-mono text-welele-gold">🪙 {selectedInvoice.coins_redeemed.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Gross Remittance:</span>
                  <span>R {selectedInvoice.gross_amount_zar.toFixed(2)} ZAR</span>
                </div>
                <div className="flex justify-between text-red-300">
                  <span>Platform Fee (5%):</span>
                  <span>-R {selectedInvoice.platform_fee_zar.toFixed(2)} ZAR</span>
                </div>
                <div className="flex justify-between text-red-300">
                  <span>Withholding Tax (15% SARS / FIRS):</span>
                  <span>-R {selectedInvoice.tax_withholding_zar.toFixed(2)} ZAR</span>
                </div>
                <div className="pt-2 border-t border-white/10 flex justify-between text-sm font-bold text-emerald-400">
                  <span>Net Dispatched to MoMo:</span>
                  <span>R {selectedInvoice.net_payout_zar.toFixed(2)} ZAR</span>
                </div>
              </div>

              <p className="text-[10px] text-welele-muted italic pt-1">
                Issued by Welele Media (Pty) Ltd. VAT Reg: 4920291048. Compliant with SA Reserve Bank & African Telco Settlement Regulations.
              </p>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={() => window.print()}
                className="flex-1 py-2.5 rounded-[7px] bg-welele-gold hover:bg-yellow-400 text-black font-bold text-xs flex items-center justify-center gap-2 shadow"
              >
                <Printer className="w-4 h-4" />
                <span>Print / Save Tax PDF</span>
              </button>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="px-4 py-2.5 rounded-[7px] bg-white/10 hover:bg-white/15 text-white font-bold text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
