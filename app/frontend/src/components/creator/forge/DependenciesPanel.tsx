import React, { useState } from 'react';
import { Dependency } from '../../../types/storyForge';
import {
  ListFilter,
  ShieldCheck,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Cpu,
  Layers,
  HelpCircle,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';

interface DependenciesPanelProps {
  dependencies: Dependency[];
}

export const DependenciesPanel: React.FC<DependenciesPanelProps> = ({
  dependencies = [],
}) => {
  const [showAdminMode, setShowAdminMode] = useState(false);
  const [filterType, setFilterType] = useState<string>('ALL');

  const unresolved = dependencies.filter(
    (d) => !['RESOLVED', 'DELIBERATELY_UNKNOWN', 'DEFERRED'].includes(d.status)
  );
  const resolved = dependencies.filter(
    (d) => ['RESOLVED', 'DELIBERATELY_UNKNOWN', 'DEFERRED'].includes(d.status)
  );

  const displayedList = dependencies.filter((d) => {
    if (filterType === 'ACTIVE') return !['RESOLVED', 'DELIBERATELY_UNKNOWN', 'DEFERRED'].includes(d.status);
    if (filterType === 'RESOLVED') return ['RESOLVED', 'DELIBERATELY_UNKNOWN', 'DEFERRED'].includes(d.status);
    return true;
  });

  return (
    <div className="h-full flex flex-col bg-[#12131C] border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
      {/* Top Header */}
      <div className="p-3.5 border-b border-white/5 bg-black/40 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FFA000]" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              Dependency Queue ({unresolved.length} Active)
            </h3>
          </div>

          {/* Admin Mode Toggle */}
          <button
            onClick={() => setShowAdminMode(!showAdminMode)}
            className="flex items-center gap-1.5 text-[11px] font-mono text-white/50 hover:text-white transition-colors"
          >
            <span>Dev Metrics</span>
            {showAdminMode ? (
              <ToggleRight className="w-4 h-4 text-[#FF6500]" />
            ) : (
              <ToggleLeft className="w-4 h-4 text-white/30" />
            )}
          </button>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 text-[11px] font-mono">
          <button
            onClick={() => setFilterType('ALL')}
            className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
              filterType === 'ALL' ? 'bg-[#FF6500] text-black' : 'bg-white/5 text-white/60 hover:text-white'
            }`}
          >
            All ({dependencies.length})
          </button>
          <button
            onClick={() => setFilterType('ACTIVE')}
            className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
              filterType === 'ACTIVE' ? 'bg-[#FF6500] text-black' : 'bg-white/5 text-white/60 hover:text-white'
            }`}
          >
            Active ({unresolved.length})
          </button>
          <button
            onClick={() => setFilterType('RESOLVED')}
            className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
              filterType === 'RESOLVED' ? 'bg-[#FF6500] text-black' : 'bg-white/5 text-white/60 hover:text-white'
            }`}
          >
            Resolved ({resolved.length})
          </button>
        </div>
      </div>

      {/* Dependency Items List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-2.5 custom-scrollbar">
        {displayedList.length === 0 ? (
          <div className="py-8 text-center text-xs text-white/40 font-mono">
            No dependencies matching filter.
          </div>
        ) : (
          displayedList.map((dep) => {
            const isResolved = ['RESOLVED', 'DELIBERATELY_UNKNOWN', 'DEFERRED'].includes(dep.status);

            return (
              <div
                key={dep.id || dep.dependency_key}
                className={`p-3 rounded-xl border transition-all space-y-2 ${
                  isResolved
                    ? 'bg-black/30 border-white/5 opacity-60'
                    : 'bg-black/50 border-white/10 hover:border-[#FFA000]/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-white/90 truncate max-w-[200px]">
                      {dep.dependency_key}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-white/10 text-[9px] font-mono font-bold text-white/70">
                      {dep.dependency_type}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {isResolved ? (
                      <span className="text-[10px] font-mono text-emerald-400 font-bold flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        {dep.status}
                      </span>
                    ) : (
                      <span className="text-[10px] font-mono text-[#FFA000] font-bold flex items-center gap-1">
                        <Clock className="w-3 h-3 animate-spin" />
                        {dep.status}
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-xs text-white/80 leading-relaxed">{dep.description}</p>

                {/* Creator-facing metadata */}
                <div className="flex items-center justify-between pt-1 border-t border-white/5 text-[11px] font-mono text-white/50">
                  <span className="flex items-center gap-1">
                    <Cpu className="w-3 h-3 text-[#FF6500]" />
                    {dep.suggested_skill}
                  </span>
                  <span>Target: {dep.target_entity}</span>
                </div>

                {/* Admin Mode Component Scores Breakdown */}
                {showAdminMode && dep.components && (
                  <div className="p-2 rounded-lg bg-black/80 border border-white/5 grid grid-cols-5 gap-1 text-[9px] font-mono text-center text-white/60">
                    <div>
                      <span className="block text-white/30">IMP</span>
                      <span className="text-[#FF6500] font-bold">{dep.components.impact}</span>
                    </div>
                    <div>
                      <span className="block text-white/30">URG</span>
                      <span className="text-[#FFA000] font-bold">{dep.components.urgency}</span>
                    </div>
                    <div>
                      <span className="block text-white/30">RSK</span>
                      <span className="text-rose-400 font-bold">{dep.components.risk}</span>
                    </div>
                    <div>
                      <span className="block text-white/30">LEV</span>
                      <span className="text-emerald-400 font-bold">{dep.components.leverage}</span>
                    </div>
                    <div>
                      <span className="block text-white/30">CST</span>
                      <span className="text-purple-400 font-bold">{dep.components.cost}</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
