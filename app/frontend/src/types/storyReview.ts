/**
 * Welele Media™ — Story Review™ Type Definitions
 * Creator-facing assistant and IP Pipeline intake contracts.
 *
 * Governing Principle:
 * "Same intelligence infrastructure where appropriate. Different product, different audience, different authority, different exposure."
 */

export interface StoryDraft {
  id?: string;
  draft_id?: string;
  creator_id?: string;
  creator_name?: string;
  title: string;
  logline: string;
  target_format: 'VERTICAL_MICRODRAMA' | 'SHORT_SERIES' | 'FEATURE';
  tone: string;
  themes: string[];
  protagonist_name: string;
  protagonist_want: string;
  protagonist_need: string;
  counterforce_or_antagonist: string;
  world_setting: string;
  episode_hooks: string[];
  full_draft_text: string;
  version: number;
  created_at?: string;
  updated_at?: string;
}

export interface DimensionEvaluation {
  score: number;
  strengths: string[];
  critique: string;
}

export interface ActionableTip {
  title: string;
  description: string;
  impact_area: string;
}

export interface ChecklistItem {
  item: string;
  passed: boolean;
  recommendation: string;
}

export interface StoryReviewDiagnostic {
  draft_id?: string;
  readiness_score: number; // 0 - 100
  readiness_tier: 'READY_FOR_SUBMISSION' | 'SOLID_FOUNDATION' | 'NEEDS_REVISION';
  evaluation_mode?: 'AI_ASSISTED' | 'BASELINE_HEURISTIC';
  premise_and_hook: DimensionEvaluation;
  character_tension: DimensionEvaluation;
  episodic_structure: DimensionEvaluation;
  production_feasibility: DimensionEvaluation;
  actionable_tips: ActionableTip[];
  submission_checklist: ChecklistItem[];
  pitch_summary: string;
  evaluated_at: string;
}

export interface PitchSubmitPayload {
  draft_id?: string;
  creator_id?: string;
  creator_name?: string;
  title: string;
  logline: string;
  target_format: string;
  pitch_package: {
    synopsis: string;
    target_audience: string;
    primary_locations: string;
    estimated_episodes: number;
    key_characters: Array<{ name: string; role: string; arc: string }>;
  };
  diagnostic_score: number;
  creator_notes?: string;
}

export interface CreatorSubmission {
  submission_id: string;
  creator_id: string;
  creator_name: string;
  title: string;
  status: 'SUBMITTED_FOR_REVIEW' | 'UNDER_EDITORIAL_EVALUATION' | 'SELECTED_FOR_DEVELOPMENT' | 'REVISION_REQUESTED' | 'DECLINED';
  submitted_at: string;
  diagnostic_summary: {
    readiness_score: number;
    evaluated_at: string;
  };
  submission_package: Record<string, any>;
  message: string;
}
