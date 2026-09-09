import React, { useState, useEffect } from 'react';
import { creatorApi } from '../../services/api';
import { Creator } from '../../types';
import { CheckCircle2, Shield, Users } from 'lucide-react';

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
      <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
        <Users className="w-4 h-4 text-welele-orange" />
        Verified African Showrunners & Studios ({creators.length})
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        {creators.map((c) => (
          <div
            key={c.id}
            className="p-4 rounded-[7px] bg-welele-surface-2 border border-white/5 flex items-center gap-3"
          >
            <img
              src={c.avatar}
              alt={c.name}
              className="w-12 h-12 rounded-[7px] object-cover border border-welele-orange"
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-white truncate text-sm">{c.name}</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-welele-orange shrink-0" />
              </div>
              <span className="text-[11px] text-welele-muted">{c.handle} • {c.country}</span>
              <p className="text-[10px] text-welele-gold mt-1">
                🪙 {c.coin_earnings?.toLocaleString()} Coins earned
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
