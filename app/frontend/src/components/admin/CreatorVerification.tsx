import React, { useState, useEffect } from 'react';
import { creatorApi } from '../../services/api';
import { Creator } from '../../types';
import { ProvenanceBadge } from '../common/patterns/ProvenanceBadge';
import { CheckCircle2, Shield, Users, Globe, Award } from 'lucide-react';

export const CreatorVerification: React.FC = () => {
  const [creators, setCreators] = useState<Creator[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    creatorApi
      .listCreators()
      .then((res) => setCreators(res.creators))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-welele-muted">Loading creator verification lists...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
          <Users className="w-4 h-4 text-welele-orange" />
          Verified African Showrunners & Studios ({creators.length})
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-welele-muted flex items-center gap-1 font-mono">
            <Globe className="w-3 h-3 text-emerald-400" /> Market: ZA (South Africa Primary)
          </span>
          <ProvenanceBadge tier="ADMIN_CONTROLLED" size="sm" />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        {creators.map((c) => (
          <div
            key={c.id}
            className="p-4 rounded-[7px] bg-welele-surface-2 border border-white/5 flex items-center justify-between gap-3 shadow-md hover:border-white/20 transition-all"
          >
            <div className="flex items-center gap-3 min-w-0">
              <img
                src={c.avatar}
                alt={c.name}
                className="w-12 h-12 rounded-[7px] object-cover border border-welele-orange shrink-0"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="font-bold text-white truncate text-sm">{c.name}</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-welele-orange shrink-0" />
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    KYC VERIFIED
                  </span>
                </div>
                <span className="text-[11px] text-welele-muted">{c.handle} • {c.country || 'South Africa (ZA)'}</span>
                <p className="text-[10px] text-welele-gold mt-1 font-mono">
                  🪙 {(c.coin_earnings || 0).toLocaleString()} Coins earned
                </p>
              </div>
            </div>

            <div className="flex flex-col items-end gap-1 shrink-0">
              <ProvenanceBadge tier="EXTERNAL_DATA" size="sm" />
              <span className="text-[9px] text-welele-muted font-mono">ID / Passport Confirmed</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

