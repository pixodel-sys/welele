import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { adminApi } from '../../services/api';
import { ModerationQueue } from './ModerationQueue';
import { CreatorVerification } from './CreatorVerification';
import { WeleleAdminStudio } from './WeleleAdminStudio';
import { Shield, Users, Video, Coins, Activity, CheckCircle, AlertTriangle, Layers } from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const { stories } = useApp();
  const [metrics, setMetrics] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'studio' | 'moderation' | 'verification'>('overview');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    adminApi
      .getMetrics()
      .then((res) => setMetrics(res))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-welele-muted">Loading Admin Console...</div>;
  }

  return (
    <div className="space-y-6 pb-20 max-w-[1440px] w-full mx-auto px-3 sm:px-6">
      {/* Header */}
      <div className="p-6 rounded-[7px] bg-gradient-to-r from-emerald-950/40 via-welele-surface-2 to-welele-surface border border-emerald-500/20 shadow-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-[7px] bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-black shadow-lg">
            <Shield className="w-6 h-6 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-black text-white font-cinematic">Welele Media™ Admin Console</h1>
              <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                LIVE
              </span>
            </div>
            <p className="text-xs text-welele-muted">Platform rights, AI safety moderation & African payment volume</p>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="flex flex-wrap gap-1.5 bg-welele-surface-2 p-1.5 rounded-[7px] border border-white/5 text-xs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1.5 rounded-[7px] font-semibold transition-all ${
              activeTab === 'overview'
                ? 'bg-emerald-500 text-black font-bold'
                : 'text-welele-muted hover:text-white'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('studio')}
            className={`px-3 py-1.5 rounded-[7px] font-semibold transition-all flex items-center gap-1.5 ${
              activeTab === 'studio'
                ? 'bg-welele-orange text-black font-bold'
                : 'text-welele-orange/80 hover:text-welele-orange'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Admin Studio (WEE)
          </button>
          <button
            onClick={() => setActiveTab('moderation')}
            className={`px-3 py-1.5 rounded-[7px] font-semibold transition-all ${
              activeTab === 'moderation'
                ? 'bg-emerald-500 text-black font-bold'
                : 'text-welele-muted hover:text-white'
            }`}
          >
            AI Moderation Queue
          </button>
          <button
            onClick={() => setActiveTab('verification')}
            className={`px-3 py-1.5 rounded-[7px] font-semibold transition-all ${
              activeTab === 'verification'
                ? 'bg-emerald-500 text-black font-bold'
                : 'text-welele-muted hover:text-white'
            }`}
          >
            Creator KYC
          </button>
        </div>
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Metrics KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-1">
              <span className="text-[11px] text-welele-muted">Daily Active Viewers</span>
              <div className="text-2xl font-black text-white font-cinematic">
                {metrics?.metrics?.daily_active_users?.toLocaleString() || '184,500'}
              </div>
              <span className="text-[10px] text-emerald-400 font-bold">+18.2% this week</span>
            </div>

            <div className="p-4 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-1">
              <span className="text-[11px] text-welele-muted">Active Video Series</span>
              <div className="text-2xl font-black text-white font-cinematic">
                {metrics?.metrics?.total_stories || 3} Shows
              </div>
              <span className="text-[10px] text-welele-orange">African Microdramas</span>
            </div>

            <div className="p-4 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-1">
              <span className="text-[11px] text-welele-muted">Total Video Streams</span>
              <div className="text-2xl font-black text-white font-cinematic">
                {metrics?.metrics?.total_views?.toLocaleString() || '4.2M'}
              </div>
              <span className="text-[10px] text-welele-gold">9:16 Canonical Vertical</span>
            </div>

            <div className="p-4 rounded-[7px] bg-welele-surface-2 border border-white/5 space-y-1">
              <span className="text-[11px] text-welele-muted">MoMo Daily Volume</span>
              <div className="text-2xl font-black text-emerald-400 font-cinematic">
                ${metrics?.revenue_velocity?.momo_daily_usd?.toLocaleString() || '4,820'}
              </div>
              <span className="text-[10px] text-welele-muted">MTN, M-Pesa, Airtel</span>
            </div>
          </div>

          {/* Quick links to queue */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              onClick={() => setActiveTab('moderation')}
              className="p-5 rounded-[7px] bg-welele-surface-2 hover:bg-welele-surface-3 border border-white/5 cursor-pointer transition-all space-y-2 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-welele-orange" />
                  AI Content Safety Queue
                </span>
                <span className="px-2 py-0.5 rounded-[7px] bg-welele-orange/20 text-welele-orange text-[10px] font-bold">
                  2 Pending
                </span>
              </div>
              <p className="text-xs text-welele-muted">
                Inspect AI safety flags, aspect ratio compliance, and cliffhanger drops.
              </p>
            </div>

            <div
              onClick={() => setActiveTab('verification')}
              className="p-5 rounded-[7px] bg-welele-surface-2 hover:bg-welele-surface-3 border border-white/5 cursor-pointer transition-all space-y-2 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  Creator Verification (KYC)
                </span>
                <span className="px-2 py-0.5 rounded-[7px] bg-emerald-500/20 text-emerald-400 text-[10px] font-bold">
                  4 Verified
                </span>
              </div>
              <p className="text-xs text-welele-muted">
                Approve verified blue-check badges for African showrunners and studios.
              </p>
            </div>
          </div>
        </>
      )}

      {activeTab === 'studio' && <WeleleAdminStudio stories={stories} />}
      {activeTab === 'moderation' && <ModerationQueue />}
      {activeTab === 'verification' && <CreatorVerification />}
    </div>
  );
};
