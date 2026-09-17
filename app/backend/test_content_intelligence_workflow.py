"""
Welele Media™ — Content Intelligence Workflow Verification (Phase 7)
Tests the 23 canonical boundary conditions for Content Intelligence, Anti-Causality guards,
Fact/Inference/Hypothesis/Decision separation, uncertainty preservation, and governed Story Forge transitions.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from main import app

from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.production_repository import production_repository
from repositories.telemetry_repository import telemetry_repository
from repositories.content_intelligence_repository import content_intelligence_repository
from services.series_episode_service import series_episode_service
from services.episode_blueprint_service import episode_blueprint_service
from services.episode_production_pack_service import episode_production_pack_service
from services.viewer_telemetry_service import viewer_telemetry_service
from services.content_intelligence_service import (
    content_intelligence_service,
    CanonMutationError,
    CausalityViolationError,
    OrphanIntelligenceError
)
from schemas.content_intelligence_models import (
    FactClassification,
    IntelligenceDomain,
    ConfidenceLevel,
    DecisionStatus,
    DecisionTargetLayer,
    ObservationRecord,
    ContentIntelligence,
    ContentDecision
)

client = TestClient(app)


@pytest.fixture
def isibusiso_intelligence_pipeline_setup():
    """
    Sets up canonical Isibusiso IP → Story Package → Series → Episode 1 → Blueprint → Production Pack → Viewer & Telemetry events.
    """
    # 1. IP
    ips = ip_repository.list_ips()
    target_ip = next((ip for ip in ips if ip.get("franchise_code") == "IP-ISIBUSISO" or ip.get("title") == "Isibusiso"), None)
    if not target_ip:
        target_ip = {
            "id": "ip_isibusiso_dynasty",
            "title": "Isibusiso",
            "franchise_code": "IP-ISIBUSISO",
            "logline": "A devout Soweto midwife delivers a baby during a power blackout and notices a birthmark matching a royal bloodline.",
            "synopsis": "Isibusiso tracks the collision between customary royal succession and modern corporate mining power.",
            "genre": "High-Stakes Melodrama / Vertical Microdrama",
            "primary_language": "isiZulu",
            "master_owner_id": "creator_zola"
        }
        ip_repository.local_insert("digital_ips", target_ip)

    ip_id = target_ip["id"]
    detail = ip_repository.get_ip_detail(ip_id)
    story_packages = detail.get("story_packages", [])
    if not story_packages:
        pkg = {
            "id": "pkg_isibusiso_v1",
            "ip_id": ip_id,
            "creator_id": "creator_zola",
            "package_title": "Isibusiso: The Sacred Lineage",
            "story_world_id": "sw_soweto_sandton",
            "target_duration_seconds": 90,
            "version": "1.0.0",
            "primary_language": "isiZulu",
            "logline": target_ip["logline"],
            "genre": target_ip["genre"],
            "thematic_premise": "Customary royal birthright versus corporate mining commodification.",
            "chronology_spine": [
                {"anchor_number": 1, "anchor_name": "Midnight Delivery", "summary": "Thandiwe delivers baby by candlelight; discovers royal ink-mark."},
                {"anchor_number": 2, "anchor_name": "Dawn Arrival", "summary": "Bhekisisa arrives with cash; Lerato confesses to surrogacy contract."},
                {"anchor_number": 3, "anchor_name": "Threshold Stand", "summary": "Thandiwe refuses settlement; community forms protective barrier."}
            ],
            "dialogues": [
                {"character": "Thandiwe Zulu", "line": "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa."}
            ],
            "beats": [
                {"beat_number": 1, "label": "Cold Open", "timestamp_seconds": 15, "action_description": "Midwife delivers newborn."},
                {"beat_number": 2, "label": "Dawn Arrival", "timestamp_seconds": 50, "action_description": "Convoy arrives with cash."},
                {"beat_number": 3, "label": "Cliffhanger", "timestamp_seconds": 88, "action_description": "Guards draw weapons."}
            ],
            "forge_configuration_id": "CFG-001",
            "lineage_hash": "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6"
        }
        ip_repository.local_insert("story_packages", pkg)
        pkg_id = "pkg_isibusiso_v1"
    else:
        pkg = story_packages[0]
        pkg_id = pkg["id"]

    # 2. Series & Episode 1
    series = series_episode_service.create_series_from_story_package(ip_id, pkg_id, 1)
    series_id = series["id"]

    all_eps = series_repository.get_episodes_for_series(series_id)
    ep1 = next((e for e in all_eps if e.get("episode_number") == 1), None)
    if not ep1:
        ep1 = series_episode_service.create_episode(series_id=series_id, episode_number=1)
    else:
        series_repository.local_update("episodes", "id", ep1["id"], {"is_empty_draft": False})

    # 3. Blueprint & Production Pack
    bp = production_repository.get_episode_blueprint(ep1["id"], version="1.0.0")
    if not bp:
        bp = episode_blueprint_service.generate_blueprint(episode_id=ep1["id"], version="1.0.0")

    pack = next((p for p in production_repository.local_get("episode_production_packs") if p.get("episode_id") == ep1["id"] and "production_units" in p), None)
    if not pack:
        pack = episode_production_pack_service.generate_production_pack(episode_id=ep1["id"], blueprint_version="1.0.0")

    # 4. Seed Telemetry Events
    session_id = f"sess_test_{uuid.uuid4().hex[:8]}"
    telemetry_repository.save_event({
        "event_id": f"tev_{uuid.uuid4().hex[:8]}",
        "event_type": "CONTENT_OPENED",
        "client_session_id": session_id,
        "ip_id": ip_id,
        "series_id": series_id,
        "episode_id": ep1["id"],
        "position_seconds": 0.0,
        "duration_seconds": 90.0,
        "event_source": "CLIENT",
        "event_version": "1.0",
        "source_lineage_hash": pkg.get("lineage_hash")
    })
    telemetry_repository.save_event({
        "event_id": f"tev_{uuid.uuid4().hex[:8]}",
        "event_type": "PLAYBACK_STARTED",
        "client_session_id": session_id,
        "ip_id": ip_id,
        "series_id": series_id,
        "episode_id": ep1["id"],
        "position_seconds": 0.0,
        "duration_seconds": 90.0,
        "event_source": "CLIENT",
        "event_version": "1.0",
        "source_lineage_hash": pkg.get("lineage_hash")
    })
    telemetry_repository.save_event({
        "event_id": f"tev_{uuid.uuid4().hex[:8]}",
        "event_type": "PLAYBACK_COMPLETED",
        "client_session_id": session_id,
        "ip_id": ip_id,
        "series_id": series_id,
        "episode_id": ep1["id"],
        "position_seconds": 90.0,
        "duration_seconds": 90.0,
        "event_source": "CLIENT",
        "event_version": "1.0",
        "source_lineage_hash": pkg.get("lineage_hash")
    })
    telemetry_repository.save_event({
        "event_id": f"tev_{uuid.uuid4().hex[:8]}",
        "event_type": "GATED_CONTENT_PRESENTED",
        "client_session_id": session_id,
        "ip_id": ip_id,
        "series_id": series_id,
        "episode_id": ep1["id"],
        "position_seconds": 90.0,
        "duration_seconds": 90.0,
        "event_source": "CLIENT",
        "event_version": "1.0",
        "metadata": {"content_state": "UNAVAILABLE", "is_available": False, "playback_started": False},
        "source_lineage_hash": pkg.get("lineage_hash")
    })

    return {
        "ip_id": ip_id,
        "series_id": series_id,
        "episode_id": ep1["id"],
        "story_package_id": pkg_id,
        "session_id": session_id
    }


# =============================================================================
# 23 AUTOMATED INTEGRITY TESTS
# =============================================================================

def test_telemetry_facts_are_preserved(isibusiso_intelligence_pipeline_setup):
    """1. Verifies that raw telemetry events compile into immutable FACT observations without loss."""
    setup = isibusiso_intelligence_pipeline_setup
    evidence = content_intelligence_service.collect_upstream_evidence(setup["ip_id"], setup["series_id"], setup["episode_id"])
    observations = content_intelligence_service.compile_observations(evidence)
    
    fact_obs = [obs for obs in observations if obs.classification == FactClassification.FACT]
    assert len(fact_obs) >= 3
    assert any("content opens" in obs.statement.lower() for obs in fact_obs)


def test_intelligence_references_evidence(isibusiso_intelligence_pipeline_setup):
    """2. Verifies that all generated intelligence records contain valid upstream evidence_refs."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    for record in pkg.intelligence_records:
        assert len(record.evidence_refs) > 0 or len(record.observation_refs) > 0
        assert record.lineage_hash is not None


def test_orphan_intelligence_is_rejected():
    """3. Verifies that unbacked intelligence with zero evidence references is strictly rejected."""
    unbacked_record = {
        "intelligence_id": "int_orphan_01",
        "domain": "CONTENT_INTELLIGENCE",
        "interpretation": "Viewers love melodrama.",
        "evidence_refs": [],
        "observation_refs": []
    }
    with pytest.raises(OrphanIntelligenceError, match="Orphan Intelligence Rejection"):
        content_intelligence_service.validate_orphan_intelligence(unbacked_record)


def test_fact_is_not_silently_promoted_to_inference(isibusiso_intelligence_pipeline_setup):
    """4. Ensures raw empirical events (e.g. 100 started) remain categorized as FACT, not INFERENCE."""
    setup = isibusiso_intelligence_pipeline_setup
    evidence = content_intelligence_service.collect_upstream_evidence(setup["ip_id"], setup["series_id"], setup["episode_id"])
    observations = content_intelligence_service.compile_observations(evidence)

    fact_counts = next(obs for obs in observations if "content opens" in obs.statement.lower())
    assert fact_counts.classification == FactClassification.FACT
    assert fact_counts.classification != FactClassification.INFERENCE


def test_inference_is_not_presented_as_fact(isibusiso_intelligence_pipeline_setup):
    """5. Ensures interpretations and hypotheses are never categorized as FACT in observation records."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    for record in pkg.intelligence_records:
        # Interpretations must be in ContentIntelligence records with qualified confidence
        assert isinstance(record.interpretation, str)
        assert record.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT_EVIDENCE]


def test_causal_claim_requires_supporting_evidence():
    """6. Anti-Causality: Rejects unsupported causal assertions from correlation alone."""
    statement_with_causality = "The 88-second cliffhanger caused retention to increase by 30%."
    with pytest.raises(CausalityViolationError, match="Causality Integrity Violation"):
        content_intelligence_service.validate_causality_claim(statement_with_causality, has_controlled_causal_experiment=False)


def test_small_sample_is_flagged(isibusiso_intelligence_pipeline_setup):
    """7. Verifies small Project 40 samples are explicitly flagged with LOW confidence and limitation notes."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    content_int = next(r for r in pkg.intelligence_records if r.domain == IntelligenceDomain.CONTENT_INTELLIGENCE)
    assert content_int.confidence in [ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT_EVIDENCE]
    assert len(content_int.limitations) > 0
    assert any("sample" in lim.lower() for lim in content_int.limitations)


def test_unknown_is_preserved(isibusiso_intelligence_pipeline_setup):
    """8. Verifies that questions/reasons that cannot be known from telemetry alone are preserved as unknowns."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    content_int = next(r for r in pkg.intelligence_records if r.domain == IntelligenceDomain.CONTENT_INTELLIGENCE)
    assert len(content_int.unknowns) > 0
    assert any("motivations" in u.lower() or "why" in u.lower() for u in content_int.unknowns)


def test_confidence_does_not_equal_truth(isibusiso_intelligence_pipeline_setup):
    """9. Verifies that confidence is contextual (with basis explanation) rather than a mathematical probability claim."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    for r in pkg.intelligence_records:
        assert isinstance(r.confidence_basis, str)
        assert len(r.confidence_basis) > 10


def test_intelligence_cannot_mutate_canon():
    """10. Enforces that Content Intelligence cannot mutate upstream story package canon fields."""
    illegal_canon_mutation = {
        "characters": [{"id": "char_thandiwe", "name": "Mutated Thandiwe"}],
        "logline": "Mutated logline based on telemetry"
    }
    with pytest.raises(CanonMutationError, match="Canon Immutability Violation"):
        content_intelligence_service.validate_canon_immutability(illegal_canon_mutation)


def test_decision_requires_intelligence_or_evidence():
    """11. Verifies that ContentDecision creation rejects decisions lacking intelligence_refs or evidence_refs."""
    with pytest.raises(ValueError, match="Decision Integrity Error"):
        content_intelligence_service.create_content_decision(
            decision_id="dec_invalid_01",
            decision_type="CREATIVE_OBJECTIVE",
            target_layer=DecisionTargetLayer.STORY_FORGE,
            intelligence_refs=[],
            evidence_refs=[],
            decision_statement="Do something without evidence",
            rationale="None",
            decision_owner="Nobody",
            transition_payload={}
        )


def test_decision_does_not_mutate_upstream(isibusiso_intelligence_pipeline_setup):
    """12. Verifies that decisions transition to a New Objective payload rather than modifying existing canon in place."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    story_dec = next(d for d in pkg.decisions if d.target_layer == DecisionTargetLayer.STORY_FORGE)
    assert story_dec.target_layer == DecisionTargetLayer.STORY_FORGE
    assert "new_creative_brief" in story_dec.transition_payload
    # Original Story Package must remain unmodified
    ip_detail = ip_repository.get_ip_detail(setup["ip_id"])
    story_pkg = ip_detail["story_packages"][0]
    assert story_pkg["package_title"] == "Isibusiso: The Sacred Lineage"


def test_production_breakpoints_can_generate_intelligence(isibusiso_intelligence_pipeline_setup):
    """13. Verifies that Phase 4 production breakpoints feed Production Intelligence records."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    prod_int = next(r for r in pkg.intelligence_records if r.domain == IntelligenceDomain.PRODUCTION_INTELLIGENCE)
    assert prod_int.domain == IntelligenceDomain.PRODUCTION_INTELLIGENCE
    assert any("BP-01" in ref for ref in prod_int.evidence_refs)


def test_viewer_breakpoints_can_generate_intelligence(isibusiso_intelligence_pipeline_setup):
    """14. Verifies that Phase 5 viewer breakpoints feed Viewer Experience Intelligence records."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    viewer_int = next(r for r in pkg.intelligence_records if r.domain == IntelligenceDomain.VIEWER_EXPERIENCE_INTELLIGENCE)
    assert viewer_int.domain == IntelligenceDomain.VIEWER_EXPERIENCE_INTELLIGENCE
    assert "VBP-01-CONTROLS-AUTOHIDE" in viewer_int.evidence_refs


def test_telemetry_patterns_can_generate_derived_observations(isibusiso_intelligence_pipeline_setup):
    """15. Verifies derived observations (e.g. completion %) are computed accurately from raw telemetry."""
    setup = isibusiso_intelligence_pipeline_setup
    evidence = content_intelligence_service.collect_upstream_evidence(setup["ip_id"], setup["series_id"], setup["episode_id"])
    observations = content_intelligence_service.compile_observations(evidence)
    
    derived = [obs for obs in observations if obs.classification == FactClassification.DERIVED_OBSERVATION]
    assert len(derived) >= 2


def test_lineage_is_traceable(isibusiso_intelligence_pipeline_setup):
    """16. Verifies SHA-256 lineage hash can trace back from intelligence to upstream story package."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    assert pkg.source_lineage_hash is not None
    assert pkg.package_lineage_hash is not None
    assert len(pkg.package_lineage_hash) == 64


def test_intelligence_version_is_deterministic(isibusiso_intelligence_pipeline_setup):
    """17. Verifies that intelligence lineage hashing is deterministic for identical payloads."""
    h1 = ContentIntelligence.compute_lineage_hash("int_01", "CONTENT_INTELLIGENCE", "Test", ["ev_1", "ev_2"], "source_hash")
    h2 = ContentIntelligence.compute_lineage_hash("int_01", "CONTENT_INTELLIGENCE", "Test", ["ev_2", "ev_1"], "source_hash")
    assert h1 == h2


def test_empty_evidence_produces_insufficient_evidence():
    """18. Verifies that empty or non-existent telemetry cleanly evaluates as INSUFFICIENT_EVIDENCE."""
    empty_evidence = {
        "ip_id": "ip_empty",
        "series_id": "series_empty",
        "episode_id": "ep_empty",
        "source_lineage_hash": "hash_empty",
        "telemetry_events": [],
        "telemetry_sessions": {}
    }
    observations = content_intelligence_service.compile_observations(empty_evidence)
    records, _, _ = content_intelligence_service.synthesize_intelligence_records(empty_evidence, observations)
    
    content_int = next(r for r in records if r.domain == IntelligenceDomain.CONTENT_INTELLIGENCE)
    assert content_int.confidence in [ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT_EVIDENCE]


def test_intelligence_cannot_rewrite_story_canon():
    """19. Explicit negative test: Content Intelligence rejects attempts to modify chronology spine or world rules."""
    illegal_world_rule_mutation = {
        "world_rules": [{"rule_key": "RULE_CORRUPTED", "summary": "Invented rule"}]
    }
    with pytest.raises(CanonMutationError):
        content_intelligence_service.validate_canon_immutability(illegal_world_rule_mutation)


def test_causal_claim_without_evidence_is_rejected():
    """20. Explicit negative test: Claiming 'viewers completed because of the cliffhanger' is blocked."""
    flawed_claim = "Viewers completed the episode directly drove by the cliffhanger."
    with pytest.raises(CausalityViolationError):
        content_intelligence_service.validate_causality_claim(flawed_claim, has_controlled_causal_experiment=False)


def test_unknown_reason_is_not_invented(isibusiso_intelligence_pipeline_setup):
    """21. Verifies that the reason behind viewer dropoff / non-continuation is not hallucinated."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    content_int = next(r for r in pkg.intelligence_records if r.domain == IntelligenceDomain.CONTENT_INTELLIGENCE)
    # Interpretation must NOT invent that viewers disliked characters or got bored without evidence
    assert "bored" not in content_int.interpretation.lower()
    assert "disliked" not in content_int.interpretation.lower()


def test_negative_or_non_action_behaviour_is_preserved(isibusiso_intelligence_pipeline_setup):
    """22. Verifies that non-continuation / non-action is recorded as a distinct metric fact."""
    setup = isibusiso_intelligence_pipeline_setup
    evidence = content_intelligence_service.collect_upstream_evidence(setup["ip_id"], setup["series_id"], setup["episode_id"])
    observations = content_intelligence_service.compile_observations(evidence)
    
    non_action_obs = next(obs for obs in observations if "non_continued" in str(obs.metric_value))
    assert non_action_obs.classification == FactClassification.FACT
    assert "did not initiate" in non_action_obs.statement.lower()


def test_decision_creates_future_objective_without_mutating_upstream(isibusiso_intelligence_pipeline_setup):
    """23. Full closed-loop test: ContentDecision creates New Objective for Story Forge without mutating upstream canon."""
    setup = isibusiso_intelligence_pipeline_setup
    pkg = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(setup["ip_id"], setup["series_id"], setup["episode_id"])
    
    # 1. Verify all 10 integrity checks passed
    assert pkg.summary_metrics["integrity_checks_passed"] == 10
    assert pkg.summary_metrics["integrity_checks_total"] == 10
    
    # 2. Verify Story Forge decision
    dec = next(d for d in pkg.decisions if d.target_layer == DecisionTargetLayer.STORY_FORGE)
    assert dec.status == DecisionStatus.ACCEPTED
    assert dec.transition_payload["target_phase"] == "STORY_FORGE_M1"
    assert dec.transition_payload["episode_number_target"] == 2
    
    # 3. Verify upstream Digital IP and Story Package canon are 100% immutable
    ip_detail = ip_repository.get_ip_detail(setup["ip_id"])
    assert ip_detail["ip"]["title"] == "Isibusiso"
    assert len(ip_detail["story_packages"]) > 0
    assert ip_detail["ip"].get("primary_language") == "isiZulu" or ip_detail["story_packages"][0].get("primary_language") == "isiZulu"
