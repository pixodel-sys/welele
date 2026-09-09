import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { monetizationApi } from '../../services/api';
import { VirtualGift } from '../../types';
import confetti from 'canvas-confetti';
import { X, Flame, Sparkles, Send } from 'lucide-react';

export const GiftModal: React.FC = () => {
  const { isGiftModalOpen, setIsGiftModalOpen, currentStory, currentEpisode, coins, setCoins, userId, setIsCoinModalOpen } = useApp();
  const [gifts, setGifts] = useState<VirtualGift[]>([]);
  const [selectedGift, setSelectedGift] = useState<VirtualGift | null>(null);
  const [message, setMessage] = useState<string>('');
  const [isSending, setIsSending] = useState<boolean>(false);
  const [celebrationText, setCelebrationText] = useState<string | null>(null);

  useEffect(() => {
    if (isGiftModalOpen) {
      monetizationApi.getPacks('USD').then((res) => {
        setGifts(res.gifts);
        if (res.gifts.length > 0 && !selectedGift) {
          setSelectedGift(res.gifts[0]);
        }
      });
    }
  }, [isGiftModalOpen]);

  if (!isGiftModalOpen || !currentStory || !currentEpisode) return null;

  const handleSendGift = async () => {
    if (!selectedGift) return;

    if (coins < selectedGift.cost) {
      setIsCoinModalOpen(true);
      return;
    }

    setIsSending(true);
    try {
      await monetizationApi.sendGift({
        user_id: userId,
        creator_id: currentStory.creator_id,
        series_id: currentStory.id,
        episode_id: currentEpisode.id,
        gift_id: selectedGift.id,
        gift_name: selectedGift.name,
        gift_icon: selectedGift.icon,
        coin_cost: selectedGift.cost,
        message,
      });

      setCoins((prev) => Math.max(0, prev - selectedGift.cost));

      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.5 },
        colors: ['#FF9D00', '#FF3B30', '#E800A8', '#FFC400'],
      });

      setCelebrationText(`Sent ${selectedGift.name} ${selectedGift.icon} to ${currentStory.creator_name}!`);
      setTimeout(() => {
        setCelebrationText(null);
        setIsGiftModalOpen(false);
      }, 2000);
    } catch (err) {
      console.error('Gift sending failed:', err);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-md bg-welele-surface border border-white/10 rounded-[7px] shadow-2xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-[7px] bg-gradient-welele flex items-center justify-center text-lg shadow">
              🔥
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Send Creator Gift</h3>
              <p className="text-xs text-welele-muted">
                Support <span className="text-welele-orange font-semibold">{currentStory.creator_name}</span>
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsGiftModalOpen(false)}
            aria-label="Close Gift Modal"
            className="w-8 h-8 rounded-[7px] bg-white/5 hover:bg-white/10 flex items-center justify-center text-welele-muted hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Gifts Grid */}
        <div className="grid grid-cols-3 gap-2.5 mt-4">
          {gifts.map((gift) => {
            const isSelected = selectedGift?.id === gift.id;
            return (
              <div
                key={gift.id}
                onClick={() => setSelectedGift(gift)}
                className={`p-3 rounded-[7px] border text-center cursor-pointer transition-all ${
                  isSelected
                    ? 'border-welele-orange bg-welele-orange/15 scale-105 shadow-lg shadow-orange-500/20'
                    : 'border-white/10 bg-welele-surface-2/70 hover:border-white/20'
                }`}
              >
                <div className="text-3xl mb-1 filter drop-shadow">{gift.icon}</div>
                <div className="text-xs font-bold text-white truncate">{gift.name}</div>
                <div className="text-[11px] font-extrabold text-welele-gold mt-0.5 flex items-center justify-center gap-0.5">
                  🪙 {gift.cost}
                </div>
              </div>
            );
          })}
        </div>

        {/* Optional Fan Message */}
        <div className="mt-4">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Add an encouraging message (optional)..."
            className="w-full bg-welele-surface-2 px-3 py-2 rounded-[7px] border border-white/10 text-xs text-white placeholder-welele-muted focus:outline-none focus:border-welele-orange"
          />
        </div>

        {/* Celebration Notification */}
        {celebrationText && (
          <div className="mt-3 p-2.5 rounded-[7px] bg-gradient-welele text-white text-xs font-bold text-center shadow">
            {celebrationText}
          </div>
        )}

        {/* Bottom Actions */}
        <div className="mt-5 flex items-center justify-between gap-3 pt-3 border-t border-white/10">
          <div className="text-xs">
            <span className="text-welele-muted">Balance: </span>
            <span className="font-bold text-welele-gold">{coins} coins</span>
          </div>

          <button
            onClick={handleSendGift}
            disabled={isSending || !selectedGift}
            className="flex-1 max-w-[180px] py-2.5 rounded-[7px] font-bold text-xs bg-gradient-welele text-white shadow-lg shadow-orange-500/20 hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-1.5"
          >
            {isSending ? (
              <span>Sending...</span>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Send {selectedGift?.cost || 0} Coins</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
