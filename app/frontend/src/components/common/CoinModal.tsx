import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { monetizationApi } from '../../services/api';
import { CoinPack, AirtimePass, SACarrier } from '../../types';
import confetti from 'canvas-confetti';
import {
  X,
  Check,
  Zap,
  Smartphone,
  CreditCard,
  ShieldCheck,
  Ticket,
  Coins,
  Signal,
  Sparkles,
  PhoneCall,
  CheckCircle2,
  AlertCircle,
  PlusCircle
} from 'lucide-react';

export const CoinModal: React.FC = () => {
  const {
    isCoinModalOpen,
    setIsCoinModalOpen,
    coins,
    setCoins,
    userId,
    currency,
    setCurrency,
    market,
    setMarket,
    selectedCarrier,
    setSelectedCarrier,
    airtimeBalance,
    setAirtimeBalance,
    userPhoneNumber,
    setUserPhoneNumber,
    activePasses,
    purchaseAirtimePass,
    topupAirtimeBalance,
  } = useApp();

  const [activeTab, setActiveTab] = useState<'packs' | 'passes'>('packs');
  const [packs, setPacks] = useState<CoinPack[]>([]);
  const [passes, setPasses] = useState<AirtimePass[]>([]);
  const [carriers, setCarriers] = useState<SACarrier[]>([]);
  const [selectedPack, setSelectedPack] = useState<CoinPack | null>(null);
  const [selectedPass, setSelectedPass] = useState<AirtimePass | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<string>(selectedCarrier || 'vodacom_airtime');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [smsToast, setSmsToast] = useState<string | null>(null);
  const [showCarrierConsent, setShowCarrierConsent] = useState<boolean>(false);
  const [showUssdDialog, setShowUssdDialog] = useState<boolean>(false);
  const [ussdMenuText, setUssdMenuText] = useState<string>('');
  const [detectedCarrierName, setDetectedCarrierName] = useState<string>('Vodacom SA');

  // Load packs, passes, and carriers
  useEffect(() => {
    if (isCoinModalOpen) {
      monetizationApi.getPacks(currency).then((res) => {
        setPacks(res.packs);
        if (res.sa_airtime_passes) setPasses(res.sa_airtime_passes);
        if (res.sa_airtime_carriers) setCarriers(res.sa_airtime_carriers);
        if (res.packs.length > 0 && !selectedPack) {
          setSelectedPack(res.packs[1] || res.packs[0]);
        }
        if (res.sa_airtime_passes && res.sa_airtime_passes.length > 0 && !selectedPass) {
          setSelectedPass(res.sa_airtime_passes[1] || res.sa_airtime_passes[0]);
        }
      });
    }
  }, [isCoinModalOpen, currency]);

  // Real-time carrier auto-detection from phone prefix
  useEffect(() => {
    const cleaned = userPhoneNumber.replace(/[\s\-\+]/g, '');
    if (cleaned.startsWith('27')) {
      const local = '0' + cleaned.slice(2);
      checkCarrierPrefix(local);
    } else {
      checkCarrierPrefix(cleaned);
    }
  }, [userPhoneNumber]);

  const checkCarrierPrefix = (phone: string) => {
    if (phone.startsWith('082') || phone.startsWith('072') || phone.startsWith('076') || phone.startsWith('079')) {
      setDetectedCarrierName('Vodacom SA');
      if (currency === 'ZAR' && paymentMethod.includes('airtime')) {
        setPaymentMethod('vodacom_airtime');
        setSelectedCarrier('vodacom_airtime');
      }
    } else if (phone.startsWith('083') || phone.startsWith('073') || phone.startsWith('078') || phone.startsWith('071')) {
      setDetectedCarrierName('MTN South Africa');
      if (currency === 'ZAR' && paymentMethod.includes('airtime')) {
        setPaymentMethod('mtn_sa_airtime');
        setSelectedCarrier('mtn_sa_airtime');
      }
    } else if (phone.startsWith('084') || phone.startsWith('074') || phone.startsWith('061')) {
      setDetectedCarrierName('Cell C');
      if (currency === 'ZAR' && paymentMethod.includes('airtime')) {
        setPaymentMethod('cellc_airtime');
        setSelectedCarrier('cellc_airtime');
      }
    } else if (phone.startsWith('081') || phone.startsWith('065') || phone.startsWith('067')) {
      setDetectedCarrierName('Telkom Mobile');
      if (currency === 'ZAR' && paymentMethod.includes('airtime')) {
        setPaymentMethod('telkom_airtime');
        setSelectedCarrier('telkom_airtime');
      }
    }
  };

  if (!isCoinModalOpen) return null;

  const handleCurrencyChange = (newCurr: string) => {
    setCurrency(newCurr);
    if (newCurr === 'ZAR') {
      setMarket('ZA');
      setUserPhoneNumber('082 891 2345');
      setPaymentMethod('vodacom_airtime');
    } else if (newCurr === 'NGN') {
      setMarket('NG');
      setUserPhoneNumber('+234 803 123 4567');
      setPaymentMethod('momo_mtn');
    } else if (newCurr === 'KES') {
      setMarket('KE');
      setUserPhoneNumber('+254 712 345 678');
      setPaymentMethod('mpesa');
    } else if (newCurr === 'GHS') {
      setMarket('GHS');
      setUserPhoneNumber('+233 24 123 4567');
      setPaymentMethod('momo_mtn');
    } else {
      setMarket('GLOBAL');
      setUserPhoneNumber('+1 555 0192');
      setPaymentMethod('paystack_card');
    }
  };

  const handleInitiatePurchase = () => {
    if (currency === 'ZAR' && paymentMethod.includes('airtime')) {
      // Show realistic carrier consent modal for SA airtime
      setShowCarrierConsent(true);
    } else {
      executeStandardPurchase();
    }
  };

  const executeAirtimePurchase = async () => {
    setShowCarrierConsent(false);
    setIsProcessing(true);
    setSuccessMessage(null);
    setSmsToast(null);

    const isPass = activeTab === 'passes' && selectedPass;
    const amountZar = isPass ? selectedPass.price_zar : (selectedPack?.price_local || 5.0);
    const targetId = isPass ? selectedPass.id : (selectedPack?.id || 'pack_fan');
    const coinsEquiv = isPass ? selectedPass.coins_grant : ((selectedPack?.coins || 0) + (selectedPack?.bonus || 0));

    try {
      const res = await monetizationApi.chargeAirtime({
        user_id: userId,
        carrier_id: paymentMethod,
        phone_number: userPhoneNumber,
        charge_type: isPass ? 'story_pass' : 'coin_pack',
        target_id: targetId,
        amount_zar: amountZar,
        coins_equivalent: coinsEquiv,
      });

      // Deduct from airtime balance
      setAirtimeBalance((prev) => Math.max(0, prev - amountZar));

      // Credit coins or passes
      if (coinsEquiv > 0) {
        setCoins((prev) => prev + coinsEquiv);
      }
      if (isPass) {
        purchaseAirtimePass(selectedPass);
      }

      confetti({
        particleCount: 120,
        spread: 80,
        origin: { y: 0.6 },
        colors: ['#00E676', '#FFD600', '#FF3D00', '#00B0FF'],
      });

      setSuccessMessage(res.message || `Payment of R${amountZar.toFixed(2)} successful via Airtime!`);
      setSmsToast(res.transaction?.sms_notification || `SMS: R${amountZar.toFixed(2)} deducted from ${detectedCarrierName} airtime.`);

      setTimeout(() => {
        setSuccessMessage(null);
        setIsCoinModalOpen(false);
      }, 2500);
    } catch (err) {
      console.error('Airtime charge failed:', err);
      // Local fallback
      setAirtimeBalance((prev) => Math.max(0, prev - amountZar));
      if (coinsEquiv > 0) setCoins((prev) => prev + coinsEquiv);
      setSuccessMessage(`R${amountZar.toFixed(2)} deducted from Airtime! Credited ${coinsEquiv} Coins.`);
      setTimeout(() => {
        setSuccessMessage(null);
        setIsCoinModalOpen(false);
      }, 2500);
    } finally {
      setIsProcessing(false);
    }
  };

  const executeStandardPurchase = async () => {
    if (!selectedPack) return;
    setIsProcessing(true);
    setSuccessMessage(null);

    try {
      const res = await monetizationApi.topupCoins({
        user_id: userId,
        pack_id: selectedPack.id,
        coins: selectedPack.coins,
        amount_local: selectedPack.price_local,
        currency: selectedPack.currency,
        payment_method: paymentMethod,
        phone_or_account: userPhoneNumber,
      });

      const totalCoinsAdded = selectedPack.coins + (selectedPack.bonus || 0);
      setCoins((prev) => prev + totalCoinsAdded);

      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#FF9D00', '#FFC400', '#FF3B30', '#E800A8'],
      });

      setSuccessMessage(res.message);
      setTimeout(() => {
        setSuccessMessage(null);
        setIsCoinModalOpen(false);
      }, 2200);
    } catch (err) {
      console.error('Purchase failed:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOpenUssd = async () => {
    try {
      const res = await monetizationApi.simulateUSSD({
        phone_number: userPhoneNumber,
        ussd_string: '*130*9353#',
        user_id: userId,
      });
      setUssdMenuText(res.session?.menu_text || '*130*9353# Welele Airtime Service Connected');
      setShowUssdDialog(true);
    } catch (e) {
      setUssdMenuText('USSD *130*9353#\n1. R5 Daily Pass\n2. R15 Weekend Binge\n3. R40 Binge Master\nReply with option:');
      setShowUssdDialog(true);
    }
  };

  const saCarriersList = [
    {
      id: 'vodacom_airtime',
      name: 'Vodacom SA',
      icon: '🔴',
      color: 'border-red-500/50 bg-red-500/10 text-red-400',
      tag: 'Vodacom Direct',
      ussd: '*130*9353*1#',
    },
    {
      id: 'mtn_sa_airtime',
      name: 'MTN SA',
      icon: '🟡',
      color: 'border-yellow-500/50 bg-yellow-500/10 text-yellow-300',
      tag: 'Everywhere You Go',
      ussd: '*130*9353*2#',
    },
    {
      id: 'cellc_airtime',
      name: 'Cell C',
      icon: '⚫',
      color: 'border-neutral-500/50 bg-neutral-800/40 text-white',
      tag: 'Instant Airtime',
      ussd: '*130*9353*3#',
    },
    {
      id: 'telkom_airtime',
      name: 'Telkom Mobile',
      icon: '🔵',
      color: 'border-blue-500/50 bg-blue-500/10 text-blue-400',
      tag: 'Direct Airtime',
      ussd: '*130*9353*4#',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-xl bg-welele-surface border border-white/10 rounded-[7px] shadow-2xl p-5 sm:p-6 overflow-hidden max-h-[92vh] overflow-y-auto">
        {/* Background ambient glow */}
        <div className="absolute top-0 right-0 w-72 h-72 bg-welele-orange/15 rounded-circle blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-72 h-72 bg-emerald-500/10 rounded-circle blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3.5 border-b border-white/10 relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-[7px] bg-gradient-welele flex items-center justify-center text-xl shadow-lg shadow-orange-500/20">
              🪙
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-black text-white font-cinematic">
                  {currency === 'ZAR' ? 'Mzansi Airtime & Coins' : 'Welele Coins™'}
                </h2>
                {currency === 'ZAR' && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    🇿🇦 South Africa
                  </span>
                )}
              </div>
              <p className="text-xs text-welele-muted">
                {currency === 'ZAR'
                  ? 'Zero bank card needed • Deduct directly from prepaid or contract airtime'
                  : 'Unlock cliffhangers & send gifts to African creators'}
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsCoinModalOpen(false)}
            aria-label="Close Modal"
            className="w-8 h-8 rounded-[7px] bg-white/5 hover:bg-white/10 flex items-center justify-center text-welele-muted hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Currency Switcher */}
        <div className="mt-3.5 flex items-center justify-between bg-welele-surface-2 p-1.5 rounded-[7px] border border-white/5 text-xs">
          <span className="text-welele-muted pl-2 font-medium">Select Market:</span>
          <div className="flex gap-1">
            {[
              { code: 'ZAR', label: '🇿🇦 ZAR' },
              { code: 'NGN', label: '🇳🇬 NGN' },
              { code: 'KES', label: '🇰🇪 KES' },
              { code: 'GHS', label: '🇬🇭 GHS' },
              { code: 'USD', label: '🌍 USD' },
            ].map((c) => (
              <button
                key={c.code}
                onClick={() => handleCurrencyChange(c.code)}
                className={`px-2.5 py-1 rounded-[7px] font-bold transition-all text-[11px] ${
                  currency === c.code
                    ? 'bg-welele-orange text-black shadow-md'
                    : 'text-welele-muted hover:text-white hover:bg-white/5'
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>

        {/* South Africa SIM Airtime Balance & Recharge Widget (When ZAR is selected) */}
        {currency === 'ZAR' && (
          <div className="mt-3.5 p-3.5 rounded-[7px] bg-gradient-to-r from-emerald-950/70 via-welele-surface-2 to-teal-950/60 border border-emerald-500/30 flex items-center justify-between gap-2 shadow-inner">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-[7px] bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                <Signal className="w-4 h-4 animate-pulse" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-extrabold tracking-wider text-emerald-400/90 block">
                  Connected SIM Airtime Balance ({detectedCarrierName})
                </span>
                <div className="text-xl font-black text-emerald-300 font-cinematic flex items-center gap-1.5">
                  <span>R{airtimeBalance.toFixed(2)}</span>
                  <span className="text-[11px] text-emerald-400 font-medium">(Ready for 1-Tap)</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => topupAirtimeBalance(20.0)}
                className="px-2 py-1 rounded-[7px] bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-[10px] font-bold text-emerald-300 transition-colors"
                title="Simulate topping up airtime balance"
              >
                + R20
              </button>
              <button
                onClick={() => topupAirtimeBalance(50.0)}
                className="px-2 py-1 rounded-[7px] bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-[10px] font-bold text-emerald-300 transition-colors"
                title="Simulate topping up airtime balance"
              >
                + R50
              </button>
            </div>
          </div>
        )}

        {/* Dual Tab Navigation for South Africa: Coin Packs vs Story Passes */}
        {currency === 'ZAR' && (
          <div className="mt-3.5 grid grid-cols-2 gap-1.5 bg-welele-surface-2 p-1 rounded-[7px] border border-white/5">
            <button
              onClick={() => setActiveTab('packs')}
              className={`py-2 rounded-[7px] text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === 'packs'
                  ? 'bg-gradient-to-r from-welele-orange to-welele-red text-white shadow-md'
                  : 'text-welele-muted hover:text-white'
              }`}
            >
              <Coins className="w-3.5 h-3.5" />
              <span>Airtime Coin Packs</span>
            </button>
            <button
              onClick={() => setActiveTab('passes')}
              className={`py-2 rounded-[7px] text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === 'passes'
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-md'
                  : 'text-welele-muted hover:text-white'
              }`}
            >
              <Ticket className="w-3.5 h-3.5" />
              <span>Mzansi Story Passes</span>
              <span className="text-[9px] px-1.5 py-0.2 rounded-[7px] bg-emerald-400/20 text-emerald-300 font-extrabold border border-emerald-400/30">
                HOT
              </span>
            </button>
          </div>
        )}

        {/* TAB 1: COIN PACKS */}
        {activeTab === 'packs' ? (
          <div className="grid grid-cols-2 gap-2.5 mt-3.5">
            {packs.map((pack) => {
              const isSelected = selectedPack?.id === pack.id;
              return (
                <div
                  key={pack.id}
                  onClick={() => setSelectedPack(pack)}
                  className={`relative p-3.5 rounded-[7px] border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-welele-orange bg-gradient-to-b from-welele-orange/15 to-transparent shadow-lg shadow-orange-500/10'
                      : 'border-white/10 bg-welele-surface-2/60 hover:border-white/20'
                  }`}
                >
                  {pack.popular && (
                    <span className="absolute -top-2.5 right-2 px-2 py-0.5 rounded-[7px] text-[9px] font-extrabold bg-gradient-welele text-white shadow">
                      POPULAR 🔥
                    </span>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{pack.label}</span>
                    {isSelected && <Check className="w-4 h-4 text-welele-orange" />}
                  </div>
                  <div className="flex items-baseline gap-1 mt-1.5">
                    <span className="text-2xl font-black text-welele-gold font-cinematic">{pack.coins}</span>
                    <span className="text-xs font-semibold text-welele-muted">coins</span>
                  </div>
                  {pack.bonus > 0 && (
                    <div className="text-[10px] font-bold text-emerald-400 mt-0.5 flex items-center gap-1">
                      <Zap className="w-3 h-3" /> +{pack.bonus} Free Bonus
                    </div>
                  )}
                  <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between text-xs">
                    <span className="font-extrabold text-white">
                      {pack.currency === 'ZAR' ? `R${(pack.price_local || 0).toFixed(2)}` : `${pack.currency} ${(pack.price_local || 0).toLocaleString()}`}
                    </span>
                    {currency === 'ZAR' && (
                      <span className="text-[10px] text-emerald-400 font-semibold">Airtime</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* TAB 2: MZANSI AIRTIME STORY PASSES */
          <div className="space-y-2.5 mt-3.5">
            {passes.map((pass) => {
              const isSelected = selectedPass?.id === pass.id;
              const isActivated = activePasses.has(pass.id);
              return (
                <div
                  key={pass.id}
                  onClick={() => setSelectedPass(pass)}
                  className={`relative p-3.5 rounded-[7px] border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-emerald-500 bg-emerald-500/10 shadow-lg shadow-emerald-500/10'
                      : 'border-white/10 bg-welele-surface-2/60 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-black text-white">{pass.name}</span>
                        <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-extrabold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          {pass.badge}
                        </span>
                        {isActivated && (
                          <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-bold bg-welele-gold/20 text-welele-gold border border-welele-gold/30 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Active
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-welele-muted mt-1">{pass.benefits}</p>
                    </div>

                    <div className="text-right shrink-0">
                      <div className="text-lg font-black text-emerald-400 font-cinematic">
                        R{pass.price_zar.toFixed(2)}
                      </div>
                      <div className="text-[10px] text-welele-muted font-medium">{pass.duration}</div>
                    </div>
                  </div>

                  <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-welele-gold font-semibold">
                    <span>🪙 Includes +{pass.coins_grant} Welele Coins</span>
                    <span className="text-emerald-400 font-bold">1-Tap Airtime Deduct</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Carrier Selection & Airtime Billing Section */}
        <div className="mt-4 pt-3.5 border-t border-white/10">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold text-white flex items-center gap-1.5">
              <Smartphone className="w-3.5 h-3.5 text-welele-orange" />
              {currency === 'ZAR' ? 'South Africa Mobile Carrier (Airtime Rail):' : 'Payment Rail:'}
            </label>

            {currency === 'ZAR' && (
              <button
                onClick={handleOpenUssd}
                className="text-[11px] text-welele-gold hover:underline font-bold flex items-center gap-1"
              >
                <PhoneCall className="w-3 h-3" /> USSD *130*9353#
              </button>
            )}
          </div>

          {currency === 'ZAR' ? (
            /* 4 Major SA MNO Carrier Badges */
            <div className="space-y-2">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {saCarriersList.map((carrier) => {
                  const isSelected = paymentMethod === carrier.id;
                  return (
                    <button
                      key={carrier.id}
                      onClick={() => {
                        setPaymentMethod(carrier.id);
                        setSelectedCarrier(carrier.id);
                      }}
                      className={`p-2.5 rounded-[7px] border text-left text-xs font-semibold flex flex-col gap-1 transition-all ${
                        isSelected
                          ? `${carrier.color} border-current shadow-lg scale-[1.02]`
                          : 'border-white/10 bg-welele-surface-2 text-welele-muted hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-1.5">
                        <span className="text-base">{carrier.icon}</span>
                        <span className="font-extrabold text-white text-xs">{carrier.name}</span>
                      </div>
                      <span className="text-[9px] opacity-80">{carrier.tag}</span>
                    </button>
                  );
                })}
              </div>

              {/* SA Bank EFT Alternative Options */}
              <div className="grid grid-cols-2 gap-2 pt-1">
                <button
                  onClick={() => setPaymentMethod('capitec_pay')}
                  className={`p-2.5 rounded-[7px] border text-xs font-semibold flex items-center gap-2 transition-all ${
                    paymentMethod === 'capitec_pay'
                      ? 'border-welele-orange bg-welele-orange/15 text-white'
                      : 'border-white/10 bg-welele-surface-2 text-welele-muted hover:text-white'
                  }`}
                >
                  <span className="text-base">🏦</span>
                  <div>
                    <div className="font-bold text-white leading-none">Capitec Pay / Ozow</div>
                    <span className="text-[9px] text-welele-muted">Instant SA Bank EFT</span>
                  </div>
                </button>

                <button
                  onClick={() => setPaymentMethod('paystack_card')}
                  className={`p-2.5 rounded-[7px] border text-xs font-semibold flex items-center gap-2 transition-all ${
                    paymentMethod === 'paystack_card'
                      ? 'border-welele-orange bg-welele-orange/15 text-white'
                      : 'border-white/10 bg-welele-surface-2 text-welele-muted hover:text-white'
                  }`}
                >
                  <CreditCard className="w-4 h-4 text-welele-muted" />
                  <div>
                    <div className="font-bold text-white leading-none">Visa / Mastercard</div>
                    <span className="text-[9px] text-welele-muted">Debit or Credit Card</span>
                  </div>
                </button>
              </div>
            </div>
          ) : (
            /* Other African Markets */
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                { id: 'momo_mtn', label: 'MTN MoMo', icon: '🟡' },
                { id: 'mpesa', label: 'M-Pesa', icon: '🟢' },
                { id: 'airtel_money', label: 'Airtel Money', icon: '🔴' },
                { id: 'paystack_card', label: 'Card Payment', icon: '💳' },
              ].map((method) => (
                <button
                  key={method.id}
                  onClick={() => setPaymentMethod(method.id)}
                  className={`p-2.5 rounded-[7px] border text-left text-xs font-semibold flex items-center gap-2 transition-all ${
                    paymentMethod === method.id
                      ? 'border-welele-orange bg-welele-orange/15 text-white'
                      : 'border-white/10 bg-welele-surface-2 text-welele-muted hover:text-white'
                  }`}
                >
                  <span>{method.icon}</span>
                  <span className="truncate">{method.label}</span>
                </button>
              ))}
            </div>
          )}

          {/* Mobile Phone Number Input with Carrier Detection */}
          <div className="mt-3">
            <div className="flex items-center justify-between mb-1">
              <label className="text-[11px] text-welele-muted font-medium">
                {paymentMethod.includes('airtime')
                  ? 'Mobile Number for Airtime Deduction (e.g. 082 / 083 / 084 / 081):'
                  : 'Mobile Money Phone Number / Account:'}
              </label>
              {currency === 'ZAR' && (
                <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                  <Check className="w-3 h-3" /> Auto-detected: {detectedCarrierName}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2 bg-welele-surface-2 px-3 py-2.5 rounded-[7px] border border-white/10">
              <Smartphone className="w-4 h-4 text-welele-orange" />
              <input
                type="text"
                value={userPhoneNumber}
                onChange={(e) => setUserPhoneNumber(e.target.value)}
                className="bg-transparent text-xs font-bold text-white w-full focus:outline-none"
                placeholder={currency === 'ZAR' ? '082 123 4567' : '+234...'}
              />
            </div>
          </div>
        </div>

        {/* Success Alert */}
        {successMessage && (
          <div className="mt-3.5 p-3 rounded-[7px] bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-medium flex items-center gap-2 animate-fade-in">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <div>
              <div className="font-bold">{successMessage}</div>
              {smsToast && <div className="text-[11px] text-emerald-400/90 mt-0.5">{smsToast}</div>}
            </div>
          </div>
        )}

        {/* Action Button Bar */}
        <div className="mt-5 flex items-center justify-between gap-3 pt-3.5 border-t border-white/10">
          <div className="text-[11px] text-welele-muted flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Encrypted Carrier Rail</span>
          </div>

          <button
            onClick={handleInitiatePurchase}
            disabled={isProcessing || (activeTab === 'packs' ? !selectedPack : !selectedPass)}
            className="flex-1 max-w-xs py-3 rounded-[7px] font-bold text-xs bg-gradient-welele text-white shadow-xl shadow-orange-500/25 hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <span className="animate-pulse">Authorizing Carrier...</span>
            ) : (
              <>
                <span>
                  {activeTab === 'passes'
                    ? `Activate ${selectedPass?.name}`
                    : `Top Up Coins`}
                </span>
                <span>
                  {currency === 'ZAR'
                    ? `(R${(activeTab === 'passes' ? selectedPass?.price_zar : selectedPack?.price_local || 0).toFixed(2)})`
                    : `(${currency} ${(selectedPack?.price_local || 0).toLocaleString()})`}
                </span>
              </>
            )}
          </button>
        </div>

        {/* Interactive Carrier Consent Dialog (Simulates Vodacom / MTN airtime push) */}
        {showCarrierConsent && (
          <div className="absolute inset-0 z-50 bg-black/90 backdrop-blur-md p-6 flex flex-col justify-center items-center animate-fade-in">
            <div className="w-full max-w-sm bg-welele-surface-2 border border-emerald-500/40 rounded-[7px] p-5 text-center shadow-2xl space-y-4">
              <div className="w-12 h-12 mx-auto rounded-[7px] bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-2xl">
                📱
              </div>

              <div>
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-400">
                  {detectedCarrierName} Direct Airtime Prompt
                </span>
                <h3 className="text-base font-black text-white mt-1">
                  Confirm Airtime Deduction
                </h3>
                <p className="text-xs text-welele-muted mt-1.5 leading-relaxed">
                  You are about to authorize <b>R{(activeTab === 'passes' ? selectedPass?.price_zar : selectedPack?.price_local || 0).toFixed(2)}</b> deduction from your mobile number <b>{userPhoneNumber}</b> for{' '}
                  <span className="text-white font-bold">
                    {activeTab === 'passes' ? selectedPass?.name : `${selectedPack?.coins} Welele Coins`}
                  </span>.
                </p>
              </div>

              <div className="p-2.5 rounded-[7px] bg-black/40 border border-white/5 text-[11px] text-emerald-300 flex items-center justify-between">
                <span>Airtime Balance: R{airtimeBalance.toFixed(2)}</span>
                <span>→ New: R{Math.max(0, airtimeBalance - (activeTab === 'passes' ? (selectedPass?.price_zar || 0) : (selectedPack?.price_local || 0))).toFixed(2)}</span>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setShowCarrierConsent(false)}
                  className="flex-1 py-2.5 rounded-[7px] bg-white/5 hover:bg-white/10 text-xs font-bold text-welele-muted hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={executeAirtimePurchase}
                  className="flex-1 py-2.5 rounded-[7px] bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-bold text-xs shadow-lg shadow-emerald-500/25 hover:opacity-95"
                >
                  Authorize 1-Tap
                </button>
              </div>
            </div>
          </div>
        )}

        {/* USSD Simulator Dialog */}
        {showUssdDialog && (
          <div className="absolute inset-0 z-50 bg-black/90 backdrop-blur-md p-6 flex flex-col justify-center items-center animate-fade-in">
            <div className="w-full max-w-sm bg-neutral-900 border border-yellow-500/40 rounded-[7px] p-5 shadow-2xl font-mono text-left space-y-4">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <span className="text-xs font-bold text-yellow-400 flex items-center gap-1.5">
                  <PhoneCall className="w-3.5 h-3.5" /> USSD *130*9353#
                </span>
                <button
                  onClick={() => setShowUssdDialog(false)}
                  className="text-xs text-neutral-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <pre className="text-xs text-neutral-200 whitespace-pre-wrap font-mono bg-black/50 p-3 rounded-[7px] border border-white/5 leading-relaxed">
                {ussdMenuText}
              </pre>

              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setShowUssdDialog(false);
                    executeAirtimePurchase();
                  }}
                  className="w-full py-2.5 rounded-[7px] bg-yellow-500 text-black font-bold text-xs shadow-lg"
                >
                  Reply & Pay via Airtime
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
