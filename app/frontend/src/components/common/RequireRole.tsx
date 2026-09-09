import React from 'react';
import { useApp } from '../../context/AppContext';
import { ShieldAlert, Lock, UserCheck, ArrowRight } from 'lucide-react';
import { AppMode } from '../../types';

interface RequireRoleProps {
  allowedRoles: Array<'viewer' | 'creator' | 'admin'>;
  fallbackMode?: AppMode;
  children: React.ReactNode;
}

export const RequireRole: React.FC<RequireRoleProps> = ({
  allowedRoles,
  fallbackMode = 'viewer',
  children,
}) => {
  const { user, setMode } = useApp();

  const userRole = user?.role || 'viewer';
  const hasAccess = userRole === 'admin' || allowedRoles.includes(userRole);

  if (hasAccess) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-6 animate-fade-in text-white">
      <div className="max-w-md w-full p-6 rounded-[7px] bg-[#14151B] border border-welele-orange/30 shadow-2xl space-y-5 text-center">
        <div className="w-14 h-14 rounded-full bg-welele-orange/10 border border-welele-orange/40 flex items-center justify-center mx-auto text-welele-orange animate-pulse">
          <ShieldAlert className="w-7 h-7" />
        </div>

        <div className="space-y-1.5">
          <h3 className="text-lg font-black font-cinematic uppercase tracking-wider text-white">
            Restricted Operational Surface
          </h3>
          <p className="text-xs text-welele-muted">
            This workstation requires <strong className="text-welele-orange uppercase">{allowedRoles.join(' or ')}</strong> credentials. Your active session is currently authenticated as <strong className="text-white font-mono uppercase">{userRole}</strong>.
          </p>
        </div>

        <div className="p-3.5 rounded-[7px] bg-black/40 border border-white/10 text-left space-y-1 text-xs">
          <div className="flex items-center gap-2 text-welele-gold font-bold">
            <Lock className="w-3.5 h-3.5" />
            <span>Institutional Trust & Tenant Boundary</span>
          </div>
          <p className="text-[11px] text-welele-muted">
            All access attempts across Welele Media™ are cryptographically signed and recorded to the append-only security audit ledger.
          </p>
        </div>

        <div className="pt-2 flex flex-col gap-2">
          <button
            onClick={() => setMode(fallbackMode)}
            className="w-full py-2.5 rounded-[7px] bg-gradient-to-r from-welele-orange to-pink-600 hover:from-orange-600 hover:to-pink-700 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-lg"
          >
            <span>Return to {fallbackMode === 'viewer' ? 'Consumer Streaming' : 'Safe Surface'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
