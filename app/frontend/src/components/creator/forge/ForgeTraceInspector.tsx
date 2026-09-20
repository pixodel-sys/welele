import React, { useState, useEffect } from 'react';
import { storyForgeApi } from '../../../services/storyForgeApi';
import { ForgeTransition } from '../../../types/storyForge';
import {
  Activity,
  Cpu,
  Clock,
  CheckCircle,
  HelpCircle,
  GitPullRequest,
  FileCheck,
  RefreshCw,
  ToggleLeft,
  ToggleRight,
  Sparkles
} from 'lucide-react';

interface ForgeTraceInspectorProps {
  storyId: string;
}

export const ForgeTraceInspector: React.FC<ForgeTraceInspectorProps> = ({ storyId }) => {
  const [trace, setTrace] = useState<ForgeTransition[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showAdminMode, setShowAdminMode] = useState(false);

  const fetchTrace = async () => {
    if (!storyId) return;
    setIsLoading(true);
    try {
      const data = await storyForgeApi.getTrace(storyId);
      setTrace(data);
    } catch (e) {
      console.warn('Could not fetch story forge trace:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTrace();
  }, [storyId]);

  return (
    <div className="h-full flex flex-col bg-[#12131C] border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
      {/* Top Header */}
      <div className="p-3.5 border-b border-white/5 bg-black/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#FF6500]" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
            Forge Audit Trace ({trace.length} Cycles)
          </h3>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAdminMode(!showAdminMode)}
            className="flex items-center gap-1.5 text-[11px] font-mono text-white/50 hover:text-white transition-colors"
          >
            <span>Admin View</span>
            {showAdminMode ? (
              <ToggleRight className="w-4 h-4 text-[#FF6500]" />
            ) : (
              <ToggleLeft className="w-4 h-4 text-white/30" />
            )}
          </button>
          <button
            onClick={fetchTrace}
            disabled={isLoading}
            className="text-xs text-white/50 hover:text-white flex items-center gap-1"
          >
            <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Trace Stream Viewport */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 custom-scrollbar text-xs">
        {trace.length === 0 ? (
          <div className="py-8 text-center text-xs text-white/40 font-mono">
            No trace transitions recorded yet.
          </div>
        ) : (
          trace.map((tr) => {
            return (
              <div
                key={tr.transition_id || tr.sequence}
                className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2 font-sans"
              >
                {/* Header Sequence & Badges */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-white/10 text-[10px] font-mono font-bold flex items-center justify-center text-white/80">
                      {tr.sequence}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        tr.authority_mode === 'ASK'
                          ? 'bg-[#FF6500]/20 text-[#FF6500]'
                          : tr.authority_mode === 'INFER'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : tr.authority_mode === 'PROPOSE'
                          ? 'bg-purple-500/20 text-purple-300'
                          : 'bg-blue-500/20 text-blue-300'
                      }`}
                    >
                      {tr.authority_mode}
                    </span>
                    <span className="text-[10px] font-mono text-white/40 flex items-center gap-1">
                      <Cpu className="w-3 h-3 text-[#FF6500]" />
                      {tr.skill}
                    </span>
                  </div>

                  {tr.provenance?.latency_ms != null && (
                    <span className="text-[10px] font-mono text-white/30">
                      {Math.round(tr.provenance.latency_ms)}ms
                    </span>
                  )}
                </div>

                {/* Question asked if ASK */}
                {tr.question_asked && (
                  <div className="p-2.5 rounded-lg bg-black/60 border border-white/5 text-white/90">
                    <span className="text-[10px] font-mono font-bold text-[#FF6500] uppercase block mb-0.5">
                      Question Asked:
                    </span>
                    <p className="font-medium">{tr.question_asked}</p>
                  </div>
                )}

                {/* Creator Response if present */}
                {tr.creator_response && (
                  <div className="p-2.5 rounded-lg bg-[#FF6500]/5 border border-[#FF6500]/20 text-white/90">
                    <span className="text-[10px] font-mono font-bold text-[#FFA000] uppercase block mb-0.5">
                      Creator Decision:
                    </span>
                    <p className="italic">"{tr.creator_response}"</p>
                  </div>
                )}

                {/* Interpretation */}
                <p className="text-[11px] text-white/70 leading-relaxed">
                  <span className="text-white/40 font-mono">Interpretation:</span> {tr.interpretation}
                </p>

                {/* State Mutations */}
                {tr.state_changes && tr.state_changes.length > 0 && (
                  <div className="pt-1.5 border-t border-white/5 space-y-1 font-mono text-[10px]">
                    <span className="text-white/40 uppercase block">State Mutations:</span>
                    {tr.state_changes.map((m, idx) => (
                      <div key={idx} className="text-emerald-300/90 flex items-center gap-1.5">
                        <span className="text-[#FF6500]">[{m.mutation_type}]</span>
                        <span>{m.target_path}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Admin Mode Full Provenance Inspector */}
                {showAdminMode && tr.provenance && (
                  <div className="p-2 rounded-lg bg-black/80 border border-white/5 text-[9px] font-mono text-white/50 space-y-0.5">
                    <div>Adapter: {tr.provenance.adapter_name} v{tr.provenance.adapter_version}</div>
                    <div>Confidence: {(tr.provenance.confidence * 100).toFixed(0)}%</div>
                    <div>State Version: v{tr.provenance.state_version_before} → v{tr.provenance.state_version_after}</div>
                    {tr.provenance.evidence?.length > 0 && (
                      <div>Evidence: {tr.provenance.evidence.join(', ')}</div>
                    )}
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
