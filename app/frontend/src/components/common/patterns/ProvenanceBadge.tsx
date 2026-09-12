import React from 'react';
import {
  UserCheck,
  Sparkles,
  Eye,
  Cpu,
  BarChart2,
  Brain,
  ShieldCheck,
  ExternalLink,
  Info
} from 'lucide-react';

export type ProvenanceTier =
  | 'CREATOR_DECLARED'
  | 'AI_ASSIST'
  | 'AI_OBSERVED'
  | 'MEDIA_OBSERVED'
  | 'SYSTEM_DERIVED'
  | 'ANALYTICAL'
  | 'INTELLIGENCE'
  | 'ADMIN_CONTROLLED'
  | 'EXTERNAL_DATA';

interface ProvenanceBadgeProps {
  tier: ProvenanceTier;
  label?: string;
  evidence?: string;
  size?: 'xs' | 'sm' | 'md';
  className?: string;
}

const TIER_CONFIG: Record<
  ProvenanceTier,
  { defaultLabel: string; bg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  CREATOR_DECLARED: {
    defaultLabel: 'Creator Declared',
    bg: 'bg-emerald-950/60',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
    icon: UserCheck,
  },
  AI_ASSIST: {
    defaultLabel: 'AI Assist',
    bg: 'bg-purple-950/60',
    text: 'text-purple-300',
    border: 'border-purple-500/30',
    icon: Sparkles,
  },
  AI_OBSERVED: {
    defaultLabel: 'AI Observed',
    bg: 'bg-indigo-950/60',
    text: 'text-indigo-300',
    border: 'border-indigo-500/30',
    icon: Eye,
  },
  MEDIA_OBSERVED: {
    defaultLabel: 'Media Observed',
    bg: 'bg-blue-950/60',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
    icon: Cpu,
  },
  SYSTEM_DERIVED: {
    defaultLabel: 'System Derived',
    bg: 'bg-zinc-900/80',
    text: 'text-zinc-400',
    border: 'border-zinc-700/50',
    icon: Info,
  },
  ANALYTICAL: {
    defaultLabel: 'Telemetry Analytical',
    bg: 'bg-cyan-950/60',
    text: 'text-cyan-300',
    border: 'border-cyan-500/30',
    icon: BarChart2,
  },
  INTELLIGENCE: {
    defaultLabel: 'IP Intelligence',
    bg: 'bg-amber-950/60',
    text: 'text-amber-300',
    border: 'border-amber-500/30',
    icon: Brain,
  },
  ADMIN_CONTROLLED: {
    defaultLabel: 'Admin Controlled',
    bg: 'bg-rose-950/60',
    text: 'text-rose-400',
    border: 'border-rose-500/30',
    icon: ShieldCheck,
  },
  EXTERNAL_DATA: {
    defaultLabel: 'External Gateway',
    bg: 'bg-amber-950/50',
    text: 'text-yellow-400',
    border: 'border-yellow-500/30',
    icon: ExternalLink,
  },
};

export const ProvenanceBadge: React.FC<ProvenanceBadgeProps> = ({
  tier,
  label,
  evidence,
  size = 'xs',
  className = '',
}) => {
  const config = TIER_CONFIG[tier] || TIER_CONFIG.SYSTEM_DERIVED;
  const Icon = config.icon;
  const displayText = label || config.defaultLabel;

  const sizeClasses = {
    xs: 'text-[9px] px-1.5 py-0.5 gap-1',
    sm: 'text-[10px] px-2 py-0.5 gap-1.5',
    md: 'text-xs px-2.5 py-1 gap-1.5',
  }[size];

  const iconSizes = {
    xs: 'w-2.5 h-2.5',
    sm: 'w-3 h-3',
    md: 'w-3.5 h-3.5',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-mono font-semibold uppercase tracking-wider rounded-[5px] border backdrop-blur-sm ${config.bg} ${config.text} ${config.border} ${sizeClasses} ${className}`}
      title={evidence ? `${displayText} • Evidence: ${evidence}` : displayText}
    >
      <Icon className={`${iconSizes} shrink-0`} />
      <span className="truncate">{displayText}</span>
    </span>
  );
};
