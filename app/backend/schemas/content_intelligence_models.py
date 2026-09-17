"""
Welele Media™ — Content Intelligence Models (Phase 7)
Canonical downstream intelligence, observation, hypothesis, and decision-support contracts.
Governing Principle: Evidence First → Interpretation Second → Decision Third.
"""

import hashlib
import json
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# 1. ENUMS & TAXONOMIES
# =============================================================================

class FactClassification(str, Enum):
    """
    Explicit separation between empirical data, aggregates, interpretations, and hypotheses.
    """
    FACT = "FACT"                                     # Raw empirical event/data point (e.g. 34 viewers reached 90%)
    DERIVED_OBSERVATION = "DERIVED_OBSERVATION"       # Mathematical/normalized transformation of facts (e.g. 34% reached 90%)
    INFERENCE = "INFERENCE"                           # Reasoned contextual interpretation of evidence
    HYPOTHESIS = "HYPOTHESIS"                         # Testable creative or operational proposition


class IntelligenceDomain(str, Enum):
    """
    Four bounded intelligence domains for Welele Media.
    """
    CONTENT_INTELLIGENCE = "CONTENT_INTELLIGENCE"
    PRODUCTION_INTELLIGENCE = "PRODUCTION_INTELLIGENCE"
    VIEWER_EXPERIENCE_INTELLIGENCE = "VIEWER_EXPERIENCE_INTELLIGENCE"
    IP_STORY_INTELLIGENCE = "IP_STORY_INTELLIGENCE"


class ConfidenceLevel(str, Enum):
    """
    Contextual confidence based on evidence quality rather than mathematical fiction.
    """
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class DecisionStatus(str, Enum):
    """
    Institutional lifecycle of a deliberate Welele content/operational decision.
    """
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    EXECUTED = "EXECUTED"


class DecisionTargetLayer(str, Enum):
    """
    Downstream destination layer where the decision takes effect as a new objective.
    """
    STORY_FORGE = "STORY_FORGE"
    PRODUCTION_PIPELINE = "PRODUCTION_PIPELINE"
    VIEWER_EXPERIENCE = "VIEWER_EXPERIENCE"
    PLATFORM_OPERATIONS = "PLATFORM_OPERATIONS"


class BreakpointCategory(str, Enum):
    EVIDENCE_GAP = "EVIDENCE_GAP"
    LINEAGE_GAP = "LINEAGE_GAP"
    CLASSIFICATION_GAP = "CLASSIFICATION_GAP"
    CONTEXT_GAP = "CONTEXT_GAP"
    SAMPLE_GAP = "SAMPLE_GAP"
    INTERPRETATION_GAP = "INTERPRETATION_GAP"
    CAUSALITY_GAP = "CAUSALITY_GAP"
    DECISION_GAP = "DECISION_GAP"


class BreakpointSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKING = "BLOCKING"


class ResolutionType(str, Enum):
    EXISTING_EVIDENCE = "EXISTING_EVIDENCE"
    NEW_DATA_REQUIRED = "NEW_DATA_REQUIRED"
    NEW_PRODUCTION_DECISION = "NEW_PRODUCTION_DECISION"
    NEW_PRODUCT_DECISION = "NEW_PRODUCT_DECISION"
    MANUAL_ANALYSIS = "MANUAL_ANALYSIS"
    ARCHITECTURE_FIX = "ARCHITECTURE_FIX"
    DEFERRED = "DEFERRED"


# =============================================================================
# 2. CORE INTELLIGENCE MODELS
# =============================================================================

class ObservationRecord(BaseModel):
    """
    Individual observation unit strictly categorized as FACT, DERIVED_OBSERVATION, INFERENCE, or HYPOTHESIS.
    """
    observation_id: str = Field(description="Unique observation ID, e.g. obs_isibusiso_ep1_001")
    domain: IntelligenceDomain = Field(description="Intelligence domain")
    classification: FactClassification = Field(description="FACT | DERIVED_OBSERVATION | INFERENCE | HYPOTHESIS")
    statement: str = Field(description="Factual, derived, or inferred statement")
    metric_value: Optional[Any] = Field(default=None, description="Optional raw or aggregate value")
    sample_size: int = Field(default=0, description="Exact observed sample size (no imaginary populations)")
    observation_period: Optional[str] = Field(default=None, description="Timeframe or session window of observation")
    evidence_refs: List[str] = Field(default_factory=list, description="IDs of upstream evidence entities")
    source_entity_type: str = Field(description="TELEMETRY_EVENT | SESSION | PRODUCTION_BREAKPOINT | VIEWER_BREAKPOINT | STORY_PACKAGE")
    source_entity_id: str = Field(description="ID of specific entity observed")
    created_at: str = Field(description="ISO-8601 creation timestamp")


class ContentIntelligence(BaseModel):
    """
    Traceable, reasoned intelligence artifact derived from verified evidence.
    Never an orphan; always links back to authoritative evidence and observations.
    """
    intelligence_id: str = Field(description="Unique intelligence record ID, e.g. int_isibusiso_s1_ep1_01")
    domain: IntelligenceDomain = Field(description="Domain of intelligence")
    scope: str = Field(description="Scope description, e.g. 'Isibusiso Season 1 Episode 1 Empirical Viewer Specimen'")
    ip_id: str = Field(description="Root Digital IP ID")
    series_id: Optional[str] = Field(default=None, description="Parent Series ID")
    episode_id: Optional[str] = Field(default=None, description="Target Episode ID")
    
    # Traceability Chain
    observation_refs: List[str] = Field(default_factory=list, description="Referenced observation IDs")
    evidence_refs: List[str] = Field(default_factory=list, description="Authoritative upstream evidence IDs")
    
    # Reasoning & Synthesis
    interpretation: str = Field(description="Reasoned interpretation of the evidence")
    hypothesis: Optional[str] = Field(default=None, description="Testable hypothesis (if applicable)")
    
    # Uncertainty & Contextual Limitations
    confidence: ConfidenceLevel = Field(description="HIGH | MEDIUM | LOW | INSUFFICIENT_EVIDENCE")
    confidence_basis: str = Field(description="Explicit explanation of why this confidence level was assigned")
    sample_size: int = Field(default=0, description="Total observed sample count")
    assumptions: List[str] = Field(default_factory=list, description="Explicit assumptions made in interpretation")
    limitations: List[str] = Field(default_factory=list, description="Known limitations (e.g. small sample, no control group)")
    unknowns: List[str] = Field(default_factory=list, description="Questions/reasons that remain unknown from telemetry alone")
    
    # Downstream Decision Implications
    decision_implications: List[str] = Field(default_factory=list, description="Potential operational or creative choices")
    
    # Lineage & Integrity
    source_versions: Dict[str, str] = Field(default_factory=dict, description="Versions of referenced upstream sources")
    source_lineage_hash: str = Field(description="Lineage hash of upstream source material")
    lineage_hash: str = Field(description="SHA-256 hash identifying this specific intelligence artifact")
    created_at: str = Field(description="ISO-8601 creation timestamp")

    @classmethod
    def compute_lineage_hash(
        cls,
        intelligence_id: str,
        domain: str,
        interpretation: str,
        evidence_refs: List[str],
        source_lineage_hash: str
    ) -> str:
        """Deterministic SHA-256 hash guaranteeing provenance traceability."""
        refs_str = ",".join(sorted(evidence_refs))
        payload = f"{intelligence_id}|{domain}|{interpretation}|{refs_str}|{source_lineage_hash}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class ContentDecision(BaseModel):
    """
    A deliberate institutional decision chosen by Welele based on intelligence and evidence.
    Transitions into a New Objective for Story Forge, Production, or Viewer Experience.
    """
    decision_id: str = Field(description="Unique decision ID, e.g. dec_isibusiso_ep2_continuation_01")
    decision_type: str = Field(description="CREATIVE_OBJECTIVE | PRODUCTION_STANDARD | VIEWER_EXPERIENCE_POLISH | EXPERIMENTAL_TEST")
    target_layer: DecisionTargetLayer = Field(description="Target destination layer")
    intelligence_refs: List[str] = Field(default_factory=list, description="IDs of supporting intelligence records")
    evidence_refs: List[str] = Field(default_factory=list, description="IDs of underlying evidence entities")
    decision_statement: str = Field(description="What Welele chooses to do")
    rationale: str = Field(description="Why this decision was made based on intelligence")
    decision_owner: str = Field(description="Responsible person or team, e.g. 'Creator Zola / Welele Editorial'")
    status: DecisionStatus = Field(default=DecisionStatus.PROPOSED)
    transition_payload: Dict[str, Any] = Field(default_factory=dict, description="New objective payload for target layer")
    result: Optional[str] = Field(default=None, description="Outcome of decision execution")
    lineage_hash: str = Field(description="SHA-256 hash representing decision identity")
    created_at: str = Field(description="ISO-8601 creation timestamp")
    updated_at: str = Field(description="ISO-8601 update timestamp")

    @classmethod
    def compute_lineage_hash(
        cls,
        decision_id: str,
        target_layer: str,
        decision_statement: str,
        intelligence_refs: List[str]
    ) -> str:
        """Deterministic SHA-256 hash identifying this decision."""
        int_str = ",".join(sorted(intelligence_refs))
        payload = f"{decision_id}|{target_layer}|{decision_statement}|{int_str}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


# =============================================================================
# 3. BREAKPOINT & REWORK LEDGERS
# =============================================================================

class IntelligenceBreakpoint(BaseModel):
    """
    Records gaps, classification ambiguities, sample limitations, or causality violations.
    """
    breakpoint_id: str = Field(description="Unique breakpoint ID, e.g. IBP-01")
    domain: IntelligenceDomain = Field(description="Domain where gap was detected")
    category: BreakpointCategory = Field(description="Gap category")
    severity: BreakpointSeverity = Field(description="Severity")
    description: str = Field(description="Detailed explanation of the issue")
    source_reference: str = Field(description="Path or ID of evidence that triggered the breakpoint")
    resolution: str = Field(description="Non-mutating resolution applied")
    resolution_type: ResolutionType = Field(description="Resolution category")
    blocking: bool = Field(default=False)


class IntelligenceReworkEntry(BaseModel):
    """
    Tracks adjustments made during intelligence generation to preserve truth and prevent hallucination.
    """
    rework_id: str = Field(description="Unique rework ID, e.g. IRW-01")
    area: str = Field(description="Area of rework (e.g. CAUSALITY_FILTER, UNCERTAINTY_DISCLOSURE)")
    observation: str = Field(description="What was observed that required intervention")
    intervention: str = Field(description="What modification was made to ensure integrity")
    result: str = Field(description="Resulting outcome")
    repeatable: bool = Field(default=True)


class IntelligenceIntegrityCheckResult(BaseModel):
    """
    Verification result for one of the 10 Content Intelligence Integrity Checks.
    """
    check_id: str = Field(description="1 through 10")
    check_name: str = Field(description="Name of the check")
    status: str = Field(default="PASSED", description="PASSED | FAILED | NOT_EXERCISED")
    findings: str = Field(description="Empirical observations and audit outcome")
    evidence_details: Dict[str, Any] = Field(default_factory=dict, description="Machine-verifiable supporting metrics")


# =============================================================================
# 4. CONTENT INTELLIGENCE EVIDENCE PACKAGE
# =============================================================================

class ContentIntelligenceEvidencePackage(BaseModel):
    """
    Comprehensive, immutable evidence package compiling all evidence sources, observations,
    derived metrics, intelligence records, decisions, ledgers, and integrity check results.
    """
    package_id: str = Field(description="Unique evidence package ID, e.g. cie_isibusiso_s1_ep1_v1")
    ip_id: str = Field(description="Root Digital IP ID")
    series_id: str = Field(description="Parent Series ID")
    episode_id: str = Field(description="Target Episode ID")
    
    # Evidence Sources (Referenced, Not Duplicated)
    evidence_sources: Dict[str, Any] = Field(description="Map of upstream entity IDs and versions")
    evidence_scope: Dict[str, Any] = Field(description="Sample counts, session ranges, timeframes")
    
    # Layer 1: Observations
    observations: List[ObservationRecord] = Field(default_factory=list)
    
    # Layer 2: Traceable Intelligence
    intelligence_records: List[ContentIntelligence] = Field(default_factory=list)
    
    # Layer 3: Decisions & Next Objectives
    decisions: List[ContentDecision] = Field(default_factory=list)
    
    # Ledgers & Checks
    breakpoint_ledger: List[IntelligenceBreakpoint] = Field(default_factory=list)
    rework_ledger: List[IntelligenceReworkEntry] = Field(default_factory=list)
    intelligence_integrity_checks: List[IntelligenceIntegrityCheckResult] = Field(default_factory=list)
    
    # Summary Metrics
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Lineage
    source_lineage_hash: str = Field(description="Upstream source lineage hash")
    package_lineage_hash: str = Field(description="SHA-256 hash of entire package")
    created_at: str = Field(description="ISO-8601 creation timestamp")
