import React, { Component, ErrorInfo, ReactNode } from 'react';
import { WeleleLogo } from './WeleleLogo';
import { RefreshCw, AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[Welele ErrorBoundary caught an unhandled error]:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#0B0C0E] text-[#FFF5EA] flex flex-col items-center justify-center p-6 selection:bg-[#FF6B00] selection:text-black">
          {/* Ambient Glow */}
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-orange-500/10 rounded-full blur-[120px] pointer-events-none" />

          <div className="relative z-10 max-w-md w-full bg-welele-surface-2/90 border border-white/10 rounded-2xl p-8 backdrop-blur-xl shadow-2xl flex flex-col items-center text-center space-y-6">
            <div className="relative">
              <WeleleLogo variant="stacked" size="md" showTagline={false} />
            </div>

            <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <AlertTriangle className="w-6 h-6 stroke-[2.2]" />
            </div>

            <div className="space-y-2">
              <h2 className="text-lg font-black tracking-tight text-white">
                {this.props.fallbackTitle || 'Something interrupted your story'}
              </h2>
              <p className="text-xs text-welele-muted leading-relaxed">
                {this.props.fallbackMessage ||
                  'An unexpected display issue occurred. You can retry loading the screen or reload the app.'}
              </p>
            </div>

            {this.state.error?.message && (
              <div className="w-full bg-black/40 border border-white/5 rounded-lg p-3 text-left overflow-x-auto">
                <p className="text-[10px] text-red-400 font-mono break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center gap-3 w-full pt-2">
              <button
                onClick={this.handleReset}
                className="w-full py-2.5 px-4 rounded-[7px] bg-white/10 hover:bg-white/15 text-white font-bold text-xs transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={this.handleReload}
                className="w-full py-2.5 px-4 rounded-[7px] bg-gradient-welele hover:opacity-90 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-orange-500/20 transition-all"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Reload App
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
