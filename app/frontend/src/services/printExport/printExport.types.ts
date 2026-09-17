/**
 * Welele Media™ — Print Export Engine v1.0 Types
 * Read-only presentation and projection layer over canonical Welele state.
 * Establishes 3 strict output classes with metadata provenance tracking.
 */

export enum OutputClass {
  PRODUCTION_DOCUMENT = "PRODUCTION_DOCUMENT",
  EXECUTIVE_REPORT = "EXECUTIVE_REPORT",
  PRESENTATION_DECK = "PRESENTATION_DECK"
}

export type DocumentType =
  // Class 1: Production Documents
  | "STORY_PACKAGE_SPEC"
  | "PRODUCTION_BIBLE"
  | "EPISODE_PRODUCTION_PACK"
  | "CALL_SHEET"
  | "PRODUCTION_SCRIPT"
  | "PRODUCTION_REPORT"
  // Class 2: Executive / Business Reports
  | "PRODUCTION_STATUS_REPORT"
  | "PROJECT_REPORT"
  | "IP_VALUATION_REPORT"
  | "MILESTONE_REPORT"
  | "FINANCIAL_REPORT"
  // Class 3: Presentation Decks
  | "PITCH_DECK"
  | "TITLE_DECK"
  | "EPISODE_DECK"
  | "INVESTOR_PRESENTATION";

export interface DocumentMetadata {
  document_id: string;
  document_type: DocumentType;
  output_class: OutputClass;
  source_entity: string;        // e.g. "IP-ISIBUSISO" / "Isibusiso"
  source_version: string;       // e.g. "v1.0.0"
  generated_at: string;         // ISO timestamp
  generated_by: string;         // User or system agent ID
  forge_configuration_id?: string; // e.g. "CFG-001"
  lineage_hash?: string;        // SHA-256 hash
}

export interface WeleleBrandConfig {
  studioName?: string;
  studioTagline?: string;
  studioLogoUrl?: string;
  contactEmail?: string;
  website?: string;
  accentColor?: string; // e.g. '#FF6500' (Welele Orange) or '#c44d9c'
}

export interface PrintableProductionReportData {
  metadata: DocumentMetadata;
  brand: WeleleBrandConfig;
  titleIdentity: {
    title: string;
    franchiseCode: string;
    format: string;
    durationSeconds: number;
    primaryLanguage: string;
    secondaryLanguages: string[];
  };
  creativeDna: {
    logline: string;
    thematicPremise: string;
    genre: string;
    tonalAnchors: string[];
    dramaticEngine: string;
  };
  characterBible: Array<{
    name: string;
    role: string;
    archetype: string;
    coreMotivation: string;
    fatalFlaw: string;
    signatureDialogue: string;
    visualKey: string;
    wardrobePalette: string;
    costumeDistressRules: string;
    castingSpec: string;
    dialectGuidance: string;
    provenance: string;
  }>;
  locationBible: Array<{
    locationName: string;
    settingType: string;
    spatialLayout: string;
    lightingConditions: string;
    criteria: string;
    provenance: string;
  }>;
  worldRules: Array<{
    ruleKey: string;
    lawDescription: string;
    narrativeImpact: string;
    provenance: string;
  }>;
  visualLanguage: {
    aspectRatio: string;
    framingProtocols: string[];
    lightingGrammar: string;
    colorPalette: Array<{ color_name: string; hex: string; meaning: string }>;
    lut: string;
    lenses: Array<{ lens: string; use: string }>;
    provenance: string;
  };
  audioLanguage: {
    vernacularMatrix: Record<string, string>;
    foleyEvents: Array<{ event: string; timing: string; description: string }>;
    scoreTheme: string;
    bpm: number | string;
    dialogueMix: string;
    provenance: string;
  };
  continuityAndConstraints: {
    chronologySpine: Array<{ anchor_number: number; anchor_name: string; summary: string }>;
    plantsAndPayoffs: Array<{ plant: string; status: string; payoff_target: string }>;
    budgetTier: string;
    maxCastPerScene: number;
    maxSets: number;
    safetyLimits: string[];
    provenance: string;
  };
  promptConstitution: {
    governingLaws: string[];
    forbiddenMutations: string[];
    aspectRatioRule: string;
    canonOverrideRule: string;
    provenance: string;
  };
  episodePackSpecimen?: {
    episodeNumber: number;
    episodeTitle: string;
    durationSeconds: number;
    storyBrief: string;
    cliffhangerPrompt: string;
    beats: Array<{
      beatNumber: number;
      label: string;
      timestamps: string;
      intensity: number;
      actionSummary: string;
      cliffhanger: boolean;
      provenance: string;
    }>;
    fiveTracks: {
      track1Video: {
        scenes: Array<{ scene_id: string; timing: string; visual_action: string; framing: string; lighting: string }>;
        lightingExecution: string;
        provenance: string;
      };
      track2Dialogue: {
        lines: Array<{ speaker: string; line: string; subtext: string; timestamp_s: number; delivery_tone: string }>;
        provenance: string;
      };
      track3Narration: {
        hasNarration: boolean;
        openingHook: string;
        monologues: Array<{ character: string; vo_line: string }>;
        provenance: string;
      };
      track4Ambience: {
        roomTone: string;
        foley: Array<{ timestamp_s: number; foley: string }>;
        provenance: string;
      };
      track5Music: {
        scoreTheme: string;
        bpm: number | string;
        stems: Array<{ time: string; stem: string }>;
        paywallCut: string;
        provenance: string;
      };
    };
  };
}

// ── Presentation Deck Models (Class 3) ──────────────────────────────────
export interface ScriptSceneBeat {
  id: string;
  sceneNumber: string | number;
  slugline: string;
  summary: string;
  dialoguePreview?: string;
  visualCues?: string;
  storyboardImageUrl?: string;
  audioMusicCue?: string;
  estimatedDurationSeconds?: number;
  characters?: string[];
  locationNotes?: string;
}

export interface ProductionScriptDeckData {
  metadata?: DocumentMetadata;
  projectTitle: string;
  episodeOrVersion?: string;
  clientOrClientProject?: string;
  authorOrDirector?: string;
  logline?: string;
  synopsis?: string;
  date: string;
  brand: WeleleBrandConfig;
  scenes: ScriptSceneBeat[];
  productionNotes?: {
    castList?: string[];
    equipment?: string[];
    locations?: string[];
    specialEffects?: string[];
  };
}

// ── Executive / Business Report Models (Class 2) ────────────────────────
export interface ProductionReportMetric {
  label: string;
  value: string | number;
  changeOrNote?: string;
}

export interface ProductionDeliverableItem {
  id: string;
  title: string;
  category: "Video" | "Audio" | "Graphics" | "Mastering" | "Other";
  status: "Completed" | "In Progress" | "Pending Review" | "Planned";
  dueDate?: string;
  assignee?: string;
  notes?: string;
}

export interface ProductionReportData {
  metadata?: DocumentMetadata;
  reportTitle: string;
  projectReference: string;
  clientName: string;
  preparedBy: string;
  reportDate: string;
  periodOrMilestone: string;
  brand: WeleleBrandConfig;
  executiveSummary: string;
  kpiMetrics: ProductionReportMetric[];
  deliverables: ProductionDeliverableItem[];
  budgetSummary?: {
    budgetTotal: number;
    spendToDate: number;
    variance: number;
    currencySymbol?: string;
  };
  keyRisksOrNextSteps?: string[];
}
