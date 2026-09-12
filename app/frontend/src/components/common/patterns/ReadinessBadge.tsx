import React from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Ban } from 'lucide-react';

export type ReadinessLevel = 'READY' | 'READY_WITH_WARNINGS' | 'NEEDS_INPUT' | 'BLOCKED';

interface ReadinessBadgeProps {
  level: ReadinessLevel;
  label?: string;
  missingItems?: string[];
  size?: 'xs' | 'sm' | 'md';
  className?: string;
}

const READINESS_CONFIG: Record<
  ReadinessLevel,
  { defaultLabel: string; bg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  READY: {
    defaultLabel: 'Ready for Release',
    bg: 'bg-emerald-950/70',
    text: 'text-emerald-400',
    border: 'border-emerald-500/40',
    icon: CheckCircle2,
  },
  READY_WITH_WARNINGS: {
    defaultLabel: 'Ready with Warnings',
    bg: 'bg-amber-950/70',
    text: 'text-amber-300',
    border: 'border-amber-500/40',
    icon: AlertTriangle,
  },
  NEEDS_INPUT: {
    defaultLabel: 'Needs Creator Input',
    bg: 'bg-orange-950/70',
    text: 'text-orange-400',
    border: 'border-orange-500/40',
    icon: AlertCircle,
  },
  BLOCKED: {
    defaultLabel: 'Blocked / Pre-flight Error',
    bg: 'bg-rose-950/70',
    text: 'text-rose-400',
    border: 'border-rose-500/40',
    icon: Ban,
  },
};

export const ReadinessBadge: React.FC<ReadinessBadgeProps> = ({
  level,
  label,
  missingItems,
  size = 'xs',
  className = '',
}) => {
  const config = READINESS_CONFIG[level] || READINESS_CONFIG.NEEDS_INPUT;
  const Icon = config.icon;
  const displayText = label || config.defaultLabel;

  const sizeClasses = {
    xs: 'text-[9px] px-2 py-0.5 gap-1',
    sm: 'text-[10px] px-2.5 py-1 gap-1.5',
    md: 'text-xs px-3 py-1.5 gap-2',
  }[size];

  const iconSizes = {
    xs: 'w-3 h-3',
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-black uppercase tracking-wider rounded-[6px] border backdrop-blur-md shadow-sm ${config.bg} ${config.text} ${config.border} ${sizeClasses} ${className}`}
      title={missingItems && missingItems.length > 0 ? `Missing: ${missingItems.join(', ')}` : displayText}
    >
      <Icon className={`${iconSizes} shrink-0 stroke-[2.2]`} />
      <span>{displayText}</span>
    </span>
  );
};
