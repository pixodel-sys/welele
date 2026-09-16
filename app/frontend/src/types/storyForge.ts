export type AuthorityMode = 'ASK' | 'INFER' | 'PROPOSE' | 'RECORD_PRODUCTION_DECISION' | 'STOP';

export type SkillEnum = 
  | 'EXCAVATOR'
  | 'CONNECTOR'
  | 'CHALLENGER'
  | 'PROPAGATOR'
  | 'CONTINUITY_ENGINE'
  | 'PRIORITISER'
  | 'FORGER'
  | 'ORCHESTRATOR'
  | 'FORGE_JUDGE';

export type CharacterRole = 'PROTAGONIST' | 'ANTAGONIST' | 'SUPPORTING' | 'MINOR' | 'UNRESOLVED';
export type StateStatus = 'FACT' | 'PROPOSAL' | 'UNKNOWN' | 'DELIBERATELY_UNKNOWN';
export type MilestoneEnum = 'PREMISE_LOCK' | 'DRAMATIC_ENGINE_LOCK' | 'EPISODIC_ARC_LOCK' | 'FORGE_COMPLETE';
export type ReadinessStatus = 'NOT_READY' | 'PREMISE_LOCK' | 'DRAMATIC_ENGINE_LOCK' | 'EPISODIC_ARC_LOCK' | 'DEPENDENCIES_RESOLVED' | 'FORGE_COMPLETE';

export interface CharacterRelationship {
  target_character: string;
  relation_type: string;
  dynamic: string;
  tension_level: number;
}

export interface CharacterState {
  name: string;
  role: CharacterRole;
  status: StateStatus;
  core_motivation?: string | null;
  secret_desire?: string | null;
  fatal_flaw?: string | null;
  relationships: CharacterRelationship[];
}

export interface WorldSetting {
  arena: string;
  rules_and_lore: string[];
}

export interface NarrativePlant {
  element_code: string;
  plant_name?: string | null;
  description: string;
  planted_at_version: number;
  intended_payoff?: string | null;
  payoff_status: 'PLANTED' | 'PAYOFF_DEFERRED' | 'RESOLVED';
}

export interface ChronologyEvent {
  story_id: string;
  event_sequence: number;
  story_time?: string | null;
  headline: string;
  description: string;
  participants: string[];
  location?: string | null;
}

export interface StoryState {
  story_id: string;
  state_version: number;
  previous_state_version?: number | null;
  title: string;
  logline?: string | null;
  theme?: string | null;
  tone?: string | null;
  characters: Record<string, CharacterState>;
  world: WorldSetting;
  plants: NarrativePlant[];
}

export interface PriorityComponents {
  impact: number;
  urgency: number;
  risk: number;
  leverage: number;
  cost: number;
}

export interface Dependency {
  id: string;
  story_id: string;
  dependency_key: string;
  dependency_type: 'NARRATIVE' | 'CHARACTER' | 'CAUSAL' | 'TEMPORAL' | 'KNOWLEDGE' | 'PRODUCTION' | 'CANON';
  status: 'DETECTED' | 'ASSESSED' | 'PRIORITISED' | 'ACTIVE' | 'RESOLVED' | 'DELIBERATELY_UNKNOWN' | 'DEFERRED';
  target_entity: string;
  description: string;
  components: PriorityComponents;
  priority_score: number;
  priority_rationale?: string | null;
  suggested_skill: string;
}

export interface StateMutation {
  mutation_id: string;
  target_path: string;
  old_value?: any;
  new_value: any;
  mutation_type: 'CREATE' | 'UPDATE' | 'DELETE' | 'STATUS_CHANGE';
  rationale?: string | null;
}

export interface Consequence {
  consequence_id: string;
  description: string;
  impacted_entity: string;
  derived_mutation?: StateMutation | null;
  new_dependency_detected?: string | null;
}

export interface Provenance {
  creator_id?: string | null;
  session_id?: string | null;
  adapter_name: string;
  adapter_version: string;
  confidence: number;
  assumptions: string[];
  evidence: string[];
  latency_ms?: number | null;
  timestamp: string;
  state_version_before: number;
  state_version_after: number;
}

export interface ForgeTransition {
  transition_id: string;
  story_id: string;
  trace_id: string;
  sequence: number;
  creator_input?: string | null;
  interpretation: string;
  skill: SkillEnum;
  active_dependency_id?: string | null;
  priority_score?: number | null;
  authority_mode: AuthorityMode;
  question_asked?: string | null;
  proposal?: string | null;
  creator_response?: string | null;
  state_changes: StateMutation[];
  consequences: Consequence[];
  validation_status: string;
  validation_errors: string[];
  provenance: Provenance;
  created_at: string;
}

export interface ForgeCompletionAssessment {
  assessment_id: string;
  story_id: string;
  assessed_state_version: number;
  status: ReadinessStatus;
  current_milestone?: MilestoneEnum | null;
  target_milestone: MilestoneEnum;
  satisfied_milestones: MilestoneEnum[];
  missing_invariants: string[];
  unresolved_narrative_count: number;
  unresolved_causal_count: number;
  unresolved_temporal_count: number;
  production_decisions_count: number;
  blocking_dependencies: string[];
  assessment_notes?: string | null;
  assessed_by: string;
  assessed_at: string;
}

export interface StorySummary {
  id: string;
  title: string;
  owner_id: string;
  digital_ip_id?: string | null;
  logline?: string | null;
  primary_language: string;
  status: string;
  current_state_version: number;
}

export interface CurrentAction {
  session_id: string;
  story_id: string;
  state_version: number;
  action: AuthorityMode;
  skill: SkillEnum;
  question?: string | null;
  proposal?: string | null;
  active_dependency_key?: string | null;
  active_dependency_description?: string | null;
  unresolved_dependencies_count: number;
  is_paused: boolean;
  requires_creator: boolean;
}

export interface ForgeCycleResult {
  story_id: string;
  session_id: string;
  state_version: number;
  action: AuthorityMode;
  active_question?: string | null;
  transition: ForgeTransition;
  current_state: StoryState;
  unresolved_dependencies_count: number;
}

export interface IntelligenceProjection {
  story_id: string;
  state_version: number;
  current_milestone?: string | null;
  target_milestone: string;
  satisfied_milestones: string[];
  readiness_status: string;
  core_understanding: {
    title: string;
    logline?: string | null;
    protagonists: string[];
    antagonists: string[];
    supporting_characters: string[];
    chronology_anchors_count: number;
    narrative_plants_count: number;
    production_decisions_count: number;
  };
  strengths: string[];
  unresolved_risks: string[];
  missing_invariants: string[];
  next_needed_decisions: Array<{
    dependency_id: string;
    key: string;
    type: string;
    target: string;
    description: string;
    priority_score: number;
    suggested_skill: string;
  }>;
  total_dependencies: number;
  resolved_dependencies_count: number;
}
