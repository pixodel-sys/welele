import React from 'react';

export type EntityStatus =
  | 'DRAFT'
  | 'PROCESSING'
  | 'READY'
  | 'UNDER_REVIEW'
  | 'PUBLISHED'
  | 'LIVE'
  | 'BLOCKED'
  | 'ARCHIVED';

interface StatusBadgeProps {
  status: EntityStatus | string;
  size?: 'xs' | 'sm' | 'md';
  className?: string;
}

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; dot: string; border: string }> = {
  DRAFT: {
    label: 'Draft',
    bg: 'bg-zinc-800/80',
    text: 'text-zinc-300',
    dot: 'bg-zinc-400',
    border: 'border-zinc-700/60',
  },
  PROCESSING: {
    label: 'Processing Media',
    bg: 'bg-blue-950/70',
    text: 'text-blue-300',
    dot: 'bg-blue-400 animate-pulse',
    border: 'border-blue-500/40',
  },
  UNDER_REVIEW: {
    label: 'Under Moderation',
    bg: 'bg-amber-950/70',
    text: 'text-amber-300',
    dot: 'bg-amber-400 animate-pulse',
    border: 'border-amber-500/40',
  },
  READY: {
    label: 'Ready',
    bg: 'bg-teal-950/70',
    text: 'text-teal-300',
    dot: 'bg-teal-400',
    border: 'border-teal-500/40',
  },
  PUBLISHED: {
    label: 'Published',
    bg: 'bg-emerald-950/70',
    text: 'text-emerald-300',
    dot: 'bg-emerald-400',
    border: 'border-emerald-500/40',
  },
  LIVE: {
    label: 'Live on Stream',
    bg: 'bg-emerald-950/80',
    text: 'text-emerald-200 font-black',
    dot: 'bg-emerald-400 shadow-md shadow-emerald-400/50',
    border: 'border-emerald-400/60',
  },
  BLOCKED: {
    label: 'Blocked',
    bg: 'bg-rose-950/80',
    text: 'text-rose-300',
    dot: 'bg-rose-500',
    border: 'border-rose-500/40',
  },
  ARCHIVED: {
    label: 'Archived',
    bg: 'bg-zinc-900/60',
    text: 'text-zinc-500',
    dot: 'bg-zinc-600',
    border: 'border-zinc-800',
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'xs',
  className = '',
}) => {
  const normalized = status ? status.toUpperCase().replace(/\s+/g, '_') : 'DRAFT';
  const config = STATUS_CONFIG[normalized] || STATUS_CONFIG.DRAFT;

  const sizeClasses = {
    xs: 'text-[9px] px-2 py-0.5 gap-1.5',
    sm: 'text-[10px] px-2.5 py-0.5 gap-1.5',
    md: 'text-xs px-3 py-1 gap-2',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-bold tracking-wider uppercase rounded-[5px] border backdrop-blur-sm ${config.bg} ${config.text} ${config.border} ${sizeClasses} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${config.dot}`} />
      <span>{config.label}</span>
    </span>
  );
};
