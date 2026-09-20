/**
 * Welele Media™ — Viewer Telemetry Client Service (Phase 6 Measurement Layer)
 * Provides non-blocking, failure-isolated factual event tracking.
 * Invariant: TELEMETRY FAILURE → VIEWER CONTINUES.
 */

export type EventSpineFamily = 'OPEN' | 'WATCH' | 'CONTINUE' | 'REACT' | 'RETURN' | 'PAY';

export type ViewerEventType =
  | 'APP_OPEN'
  | 'FEED_IMPRESSION'
  | 'CONTENT_OPENED'
  | 'PLAYBACK_STARTED'
  | 'PLAYBACK_PROGRESS'
  | 'PLAYBACK_PAUSED'
  | 'PLAYBACK_RESUMED'
  | 'PLAYBACK_COMPLETED'
  | 'NEXT_EPISODE_SELECTED'
  | 'GATED_CONTENT_PRESENTED'
  | 'REACTION_ADDED'
  | 'REACTION_REMOVED'
  | 'COMMENT_SUBMITTED'
  | 'SHARE_INITIATED'
  | 'SESSION_RETURNED'
  | 'PAYMENT_INITIATED'
  | 'PAYMENT_SUCCEEDED'
  | 'PAYMENT_FAILED'
  | 'CONTENT_UNLOCKED';

export interface ViewerTelemetryEventPayload {
  event_id?: string;
  event_family: EventSpineFamily;
  event_type: ViewerEventType;
  occurred_at?: string;
  session_id?: string;
  viewer_id?: string;
  anonymous_id?: string;
  content_type?: string;
  content_id: string;
  series_id?: string;
  episode_id?: string;
  position_seconds?: number;
  duration_seconds?: number;
  milestone_pct?: 25 | 50 | 75 | 90 | 100;
  event_source?: 'CLIENT' | 'SERVER';
  event_version?: string;
  source?: string;
  environment?: 'production' | 'staging' | 'test';
  is_test?: boolean;
  metadata?: Record<string, any>;
}

class TelemetryService {
  private currentSessionId: string;
  private anonymousId: string;
  private emittedMilestones: Set<string> = new Set();
  private priorSessionDetected: boolean = false;

  constructor() {
    this.anonymousId = this.resolveAnonymousId();
    this.currentSessionId = this.initSession();
  }

  private resolveAnonymousId(): string {
    try {
      let anon = localStorage.getItem('welele_anonymous_id');
      if (!anon) {
        anon = `anon_${Math.random().toString(36).substring(2, 11)}_${Date.now()}`;
        localStorage.setItem('welele_anonymous_id', anon);
      }
      return anon;
    } catch {
      return `anon_${Math.random().toString(36).substring(2, 11)}`;
    }
  }

  private initSession(): string {
    try {
      const priorSession = sessionStorage.getItem('welele_session_id');
      const lastSession = localStorage.getItem('welele_last_session_id');

      if (priorSession) {
        return priorSession;
      }

      const newSession = `sess_${Math.random().toString(36).substring(2, 11)}_${Date.now()}`;
      sessionStorage.setItem('welele_session_id', newSession);

      if (lastSession && lastSession !== newSession) {
        this.priorSessionDetected = true;
      }
      localStorage.setItem('welele_last_session_id', newSession);
      return newSession;
    } catch {
      return `sess_${Math.random().toString(36).substring(2, 11)}`;
    }
  }

  public getSessionId(): string {
    return this.currentSessionId;
  }

  public resetSessionForNewContext(): string {
    this.emittedMilestones.clear();
    const newSession = `sess_${Math.random().toString(36).substring(2, 11)}_${Date.now()}`;
    try {
      sessionStorage.setItem('welele_session_id', newSession);
      localStorage.setItem('welele_last_session_id', newSession);
    } catch {
      // safe fallback
    }
    this.currentSessionId = newSession;
    return newSession;
  }

  public resolveEnvironment(): 'production' | 'staging' | 'test' {
    try {
      const host = window.location.hostname.toLowerCase();
      if (host.includes('test') || window.location.search.includes('test=true') || window.location.search.includes('is_test=true')) {
        return 'test';
      }
      if (host === 'localhost' || host === '127.0.0.1' || host.includes('staging')) {
        return 'staging';
      }
      return 'production';
    } catch {
      return 'production';
    }
  }

  /**
   * Primary Telemetry Ingestion Interface
   * Strictly non-blocking: network/backend errors are completely isolated.
   */
  public async track(event: ViewerTelemetryEventPayload): Promise<void> {
    try {
      const sessionId = event.session_id || this.currentSessionId;
      const contentId = event.content_id;
      const env = event.environment || this.resolveEnvironment();
      const isTest = event.is_test ?? (env === 'test' || window.location.search.includes('test=true'));

      // Milestone Once-Per-Session Guard
      if (event.event_type === 'PLAYBACK_PROGRESS' && event.milestone_pct) {
        const milestoneKey = `${sessionId}:${contentId}:${event.milestone_pct}`;
        if (this.emittedMilestones.has(milestoneKey)) {
          return; // Suppress duplicate milestone emission
        }
        this.emittedMilestones.add(milestoneKey);
      }

      const fullEvent = {
        event_id: event.event_id || `evt_${Math.random().toString(36).substring(2, 11)}_${Date.now()}`,
        event_family: event.event_family,
        event_type: event.event_type,
        occurred_at: event.occurred_at || new Date().toISOString(),
        session_id: sessionId,
        viewer_id: event.viewer_id,
        anonymous_id: event.anonymous_id || this.anonymousId,
        content_type: event.content_type || 'EPISODE',
        content_id: contentId,
        series_id: event.series_id,
        episode_id: event.episode_id,
        position_seconds: event.position_seconds ?? 0.0,
        duration_seconds: event.duration_seconds ?? 0.0,
        milestone_pct: event.milestone_pct,
        event_source: event.event_source || 'CLIENT',
        event_version: event.event_version || '1.0',
        source: event.source || 'WELELE_VIEWER',
        environment: env,
        is_test: isTest,
        metadata: event.metadata || {}
      };

      // Non-blocking fire-and-forget network request
      fetch('/api/v1/telemetry/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fullEvent)
      }).catch((err) => {
        // Telemetry Failure Isolation Invariant: Failure must never interrupt playback
        console.warn('[Welele Telemetry] Non-blocking delivery beacon deferred/failed:', err?.message || err);
      });
    } catch (err) {
      // Isolate unexpected runtime exceptions
      console.warn('[Welele Telemetry] Non-blocking track error caught:', err);
    }
  }

  /**
   * Fires initial APP_OPEN once per browser session.
   */
  public trackAppOpen(metadata?: Record<string, any>): void {
    try {
      const hasTrackedOpen = sessionStorage.getItem('welele_app_open_tracked');
      if (hasTrackedOpen) return;
      sessionStorage.setItem('welele_app_open_tracked', 'true');
      this.track({
        event_family: 'OPEN',
        event_type: 'APP_OPEN',
        content_type: 'PLATFORM',
        content_id: 'welele_pwa',
        source: 'APP_INIT',
        metadata: {
          userAgent: navigator.userAgent,
          screen: `${window.innerWidth}x${window.innerHeight}`,
          ...metadata
        }
      });
    } catch (e) {}
  }

  /**
   * Helper to check and emit return event upon qualified content action
   */
  public checkAndEmitReturn(seriesId?: string): void {
    if (this.priorSessionDetected) {
      this.priorSessionDetected = false;
      this.track({
        event_family: 'RETURN',
        event_type: 'SESSION_RETURNED',
        content_type: 'SERIES',
        content_id: seriesId || 'welele_catalog',
        series_id: seriesId,
        metadata: { return_type: 'QUALIFIED_CONTENT_ENGAGEMENT' }
      });
    }
  }
}

export const telemetryService = new TelemetryService();
