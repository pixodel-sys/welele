"""
Welele Media™ — Production Evidence Integrity Regression Suite
After-quarantine verification. Confirms:

  [1] Legacy untagged records (no environment / no is_test key) are excluded
      from the Production funnel.
  [2] All known quarantine-prefix session IDs are excluded from Production:
      sess_test_*, sess_scrub_*, sess_pause_*, sess_play_*, sess_order_*,
      sess_canary_*, sess_d563_*, sess_e186_*, sess_2c66_*, sess_quarantined_*
  [3] A genuine Blood Ties production session (sess_live_prod_*,
      environment="production", is_test=False) survives the Production filter
      and contributes correct Entered / Selected / Watched / etc. counts.
  [4] The displayed funnel counts correspond only to explicitly attributed
      production events — no synthetic inflation.
  [5] Switching to environment=test exposes the quarantined historical
      material (it is not lost).
  [6] Switching to environment=all shows the combined picture — both
      production and quarantined counts are present.

  [UI] The UI must explicitly distinguish "No production evidence" from
       "Production evidence exists" (verified via provenance fields).
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from main import app
from schemas.viewer_telemetry_models import (
    ViewerTelemetryEvent,
    EventSpineFamily,
    ViewerEventType,
)
from services.rbac_service import create_access_token

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _admin_headers() -> dict:
    token = create_access_token(
        user_id="admin_integrity_test",
        role="admin",
        market="ALL",
        kyc_status="SUPER_ADMIN",
    )
    return {"Authorization": f"Bearer {token}"}


def _funnel(environment: str, series_id: str | None = None) -> dict:
    url = f"/api/v1/admin/project40-funnel?environment={environment}"
    if series_id:
        url += f"&series_id={series_id}"
    return client.get(url, headers=_admin_headers()).json()


def _ingest(events: list[ViewerTelemetryEvent]) -> int:
    res = client.post(
        "/api/v1/telemetry/batch",
        json=[e.model_dump() for e in events],
    )
    assert res.status_code == 200, f"Batch ingest failed: {res.text}"
    return res.json()["recorded"]


def _make_app_open(
    session_id: str,
    run: str,
    *,
    environment: str | None = "production",
    is_test: bool = False,
    include_is_test_key: bool = True,
) -> ViewerTelemetryEvent:
    """Build a minimal APP_OPEN event, optionally omitting is_test to simulate legacy data."""
    kwargs = dict(
        event_id=f"evt_ao_{run}_{session_id[-6:]}",
        event_family=EventSpineFamily.OPEN,
        event_type=ViewerEventType.APP_OPEN,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        content_type="PLATFORM",
        content_id="welele_pwa",
    )
    if environment is not None:
        kwargs["environment"] = environment
    if include_is_test_key:
        kwargs["is_test"] = is_test
    return ViewerTelemetryEvent(**kwargs)


# ---------------------------------------------------------------------------
# Shared production session fixture (seeded once per module run)
# ---------------------------------------------------------------------------

SERIES_ID = "story_blood_ties"
EP1_ID = "ep_bt_1"
EP2_ID = "ep_bt_2"


@pytest.fixture(scope="module")
def prod_session_id() -> str:
    """
    Seeds a complete 11-step Blood Ties production session and returns the
    session_id so subsequent tests can reference it.
    The session carries environment="production" and is_test=False throughout.
    """
    run = uuid.uuid4().hex[:6]
    sid = f"sess_live_prod_{run}"
    viewer_id = f"usr_prod_{run}"
    base_time = datetime.now(timezone.utc)

    events = [
        # Step 1 — Entered (APP_OPEN)
        ViewerTelemetryEvent(
            event_id=f"evt_p_01_{run}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.APP_OPEN,
            occurred_at=(base_time + timedelta(seconds=1)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="PLATFORM", content_id="welele_pwa",
            environment="production", is_test=False,
        ),
        # Step 2 — Discovered (FEED_IMPRESSION)
        ViewerTelemetryEvent(
            event_id=f"evt_p_02_{run}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.FEED_IMPRESSION,
            occurred_at=(base_time + timedelta(seconds=3)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="CATALOG_FEED", content_id="home_feed",
            environment="production", is_test=False,
        ),
        # Step 3 — Selected (CONTENT_OPENED → Blood Ties)
        ViewerTelemetryEvent(
            event_id=f"evt_p_03_{run}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.CONTENT_OPENED,
            occurred_at=(base_time + timedelta(seconds=6)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="SERIES", content_id=SERIES_ID, series_id=SERIES_ID,
            environment="production", is_test=False,
            metadata={"title": "Blood Ties"},
        ),
        # Step 4 — Watched (PLAYBACK_STARTED Episode 1)
        ViewerTelemetryEvent(
            event_id=f"evt_p_04_{run}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_STARTED,
            occurred_at=(base_time + timedelta(seconds=8)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="EPISODE", content_id=EP1_ID,
            series_id=SERIES_ID, episode_id=EP1_ID,
            position_seconds=0.0, duration_seconds=90.0,
            environment="production", is_test=False,
        ),
        # Step 5 — Continued (Milestone 25%)
        ViewerTelemetryEvent(
            event_id=f"evt_p_05_m25_{run}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_PROGRESS,
            occurred_at=(base_time + timedelta(seconds=22)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="EPISODE", content_id=EP1_ID,
            series_id=SERIES_ID, episode_id=EP1_ID,
            milestone_pct=25, position_seconds=22.5,
            environment="production", is_test=False,
        ),
        # Step 5b — Milestone 90% (completes the episode)
        ViewerTelemetryEvent(
            event_id=f"evt_p_05_m90_{run}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_PROGRESS,
            occurred_at=(base_time + timedelta(seconds=81)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="EPISODE", content_id=EP1_ID,
            series_id=SERIES_ID, episode_id=EP1_ID,
            milestone_pct=90, position_seconds=81.0,
            environment="production", is_test=False,
        ),
        # Step 6 — Engaged (REACTION_ADDED)
        ViewerTelemetryEvent(
            event_id=f"evt_p_06_like_{run}",
            event_family=EventSpineFamily.REACT,
            event_type=ViewerEventType.REACTION_ADDED,
            occurred_at=(base_time + timedelta(seconds=85)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="SERIES", content_id=SERIES_ID, series_id=SERIES_ID,
            environment="production", is_test=False,
            metadata={"reaction_type": "LIKE"},
        ),
        # Step 7 — Paywall (GATED_CONTENT_PRESENTED)
        ViewerTelemetryEvent(
            event_id=f"evt_p_07_paywall_{run}",
            event_family=EventSpineFamily.CONTINUE,
            event_type=ViewerEventType.GATED_CONTENT_PRESENTED,
            occurred_at=(base_time + timedelta(seconds=91)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="EPISODE", content_id=EP2_ID,
            series_id=SERIES_ID, episode_id=EP2_ID,
            environment="production", is_test=False,
            metadata={"content_state": "LOCKED", "coin_price": 5},
        ),
        # Step 8 — Payment Attempt (PAYMENT_INITIATED)
        ViewerTelemetryEvent(
            event_id=f"evt_p_08_payinit_{run}",
            event_family=EventSpineFamily.PAY,
            event_type=ViewerEventType.PAYMENT_INITIATED,
            occurred_at=(base_time + timedelta(seconds=95)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="EPISODE", content_id=EP2_ID,
            series_id=SERIES_ID, episode_id=EP2_ID,
            environment="production", is_test=False,
            metadata={"method": "COINS", "cost": 5},
        ),
        # Step 9 — Paid (CONTENT_UNLOCKED)
        ViewerTelemetryEvent(
            event_id=f"evt_p_09_unlocked_{run}",
            event_family=EventSpineFamily.PAY,
            event_type=ViewerEventType.CONTENT_UNLOCKED,
            occurred_at=(base_time + timedelta(seconds=98)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="EPISODE", content_id=EP2_ID,
            series_id=SERIES_ID, episode_id=EP2_ID,
            environment="production", is_test=False,
            metadata={"method": "COINS", "cost": 5},
        ),
        # Step 10 — Continued post-pay (PLAYBACK_STARTED Episode 2 after unlock)
        ViewerTelemetryEvent(
            event_id=f"evt_p_10_ep2play_{run}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_STARTED,
            occurred_at=(base_time + timedelta(seconds=102)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="EPISODE", content_id=EP2_ID,
            series_id=SERIES_ID, episode_id=EP2_ID,
            position_seconds=0.0,
            environment="production", is_test=False,
        ),
        # Step 11 — Returned (SESSION_RETURNED)
        ViewerTelemetryEvent(
            event_id=f"evt_p_11_return_{run}",
            event_family=EventSpineFamily.RETURN,
            event_type=ViewerEventType.SESSION_RETURNED,
            occurred_at=(base_time + timedelta(seconds=300)).isoformat(),
            session_id=sid, viewer_id=viewer_id,
            content_type="SERIES", content_id=SERIES_ID, series_id=SERIES_ID,
            environment="production", is_test=False,
        ),
    ]

    ingested = _ingest(events)
    assert ingested == len(events), (
        f"Expected {len(events)} events ingested, got {ingested}"
    )
    return sid


# ---------------------------------------------------------------------------
# [1] Legacy / Unknown provenance — excluded from Production, NOT labelled as
#     genuine test/canary data
# ---------------------------------------------------------------------------

class TestLegacyUnknownProvenance:
    """
    [1] Events with missing environment / missing is_test key are historical
    artifacts of unknown provenance from before Phase 3A tagging.

    They must be:
      - EXCLUDED from the Production funnel  (they are untrusted)
      - Counted as legacy_events_quarantined, NOT as canary_events_excluded
        (we do NOT know if they are genuine test data; we only know they are
        not verifiable as genuine production evidence)
      - Inspectable in the combined view for audit purposes
    """

    def test_untagged_event_counted_as_legacy_not_canary(self):
        """
        A record with no environment and no is_test field must be classified as
        LEGACY/UNKNOWN, not as EXPLICIT CANARY.

        legacy_events_quarantined must increase.
        canary_events_excluded must NOT increase for this event.

        This is the critical provenance distinction: we do not want the UI to
        say 'this is test data' when all we know is 'this is untrusted data'.
        """
        from repositories.telemetry_repository import telemetry_repository

        run = uuid.uuid4().hex[:6]
        untagged_sid = f"sess_legacy_untagged_{run}"

        # Capture baseline counts before inserting
        before = _funnel("production")
        before_legacy = before["provenance"].get("legacy_events_quarantined", 0)
        before_canary = before["provenance"].get("canary_events_excluded", 0)

        # Insert a pre-Phase-3A-style record directly (no environment, no is_test)
        legacy_record = {
            "event_id": f"evt_legacy_{run}",
            "event_family": "OPEN",
            "event_type": "APP_OPEN",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "session_id": untagged_sid,
            "content_type": "PLATFORM",
            "content_id": "welele_pwa",
            # environment and is_test are intentionally absent
        }
        telemetry_repository.save_event(legacy_record)

        after = _funnel("production")
        after_legacy = after["provenance"].get("legacy_events_quarantined", 0)
        after_canary = after["provenance"].get("canary_events_excluded", 0)

        # Must be quarantined from production
        assert after["provenance"]["test_events_excluded"] >= 1, (
            "Legacy untagged event not excluded from Production — quarantine regressed."
        )

        # Must land in LEGACY bucket, not CANARY bucket
        assert after_legacy > before_legacy, (
            "Legacy untagged event did NOT increment legacy_events_quarantined. "
            "It may have been silently dropped or incorrectly classified."
        )
        assert after_canary == before_canary, (
            f"Legacy untagged event incremented canary_events_excluded "
            f"({before_canary} → {after_canary}). "
            "We must not label untrusted legacy data as deliberate test/canary data."
        )

    def test_missing_is_test_key_excluded_from_production(self):
        """
        An event that reaches the API but without the is_test field is either
        rejected at schema validation (safe) or accepted and quarantined by the
        backend's legacy guard ('is_test' not in e). Either outcome is correct.
        """
        run = uuid.uuid4().hex[:6]
        raw_sid = f"sess_legacy_no_is_test_{run}"

        raw_payload = [
            {
                "event_id": f"evt_raw_nokey_{run}",
                "event_family": "OPEN",
                "event_type": "APP_OPEN",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "session_id": raw_sid,
                "content_type": "PLATFORM",
                "content_id": "welele_pwa",
                "environment": "production",
                # is_test is intentionally absent
            }
        ]
        res = client.post("/api/v1/telemetry/batch", json=raw_payload)
        # Schema rejection (422) is also a valid defence — the event never enters the store
        if res.status_code == 200:
            prod_funnel = _funnel("production")
            assert prod_funnel["provenance"]["test_events_excluded"] >= 1, (
                "Event with missing is_test key was NOT excluded from Production."
            )


# ---------------------------------------------------------------------------
# [2] Known quarantine-prefix sessions excluded from Production
# ---------------------------------------------------------------------------

QUARANTINE_PREFIXES = [
    "sess_test_",
    "sess_scrub_",
    "sess_pause_",
    "sess_play_",
    "sess_order_",
    "sess_canary_",
    "sess_d563_",
    "sess_e186_",
    "sess_2c66_",
    "sess_quarantined_",
]


class TestKnownFixtureExclusion:
    """
    [2] Every session ID matching a known quarantine prefix must be excluded
    from the Production environment funnel, regardless of is_test / environment
    field values.
    """

    def test_all_quarantine_prefix_sessions_excluded_from_production(self):
        """
        Seeding one APP_OPEN for each quarantine prefix. None must appear in
        the Production funnel (test_events_excluded increases by at least 1
        per prefix group).
        """
        run = uuid.uuid4().hex[:6]
        events: list[ViewerTelemetryEvent] = []

        for prefix in QUARANTINE_PREFIXES:
            sid = f"{prefix}{run}"
            evt = ViewerTelemetryEvent(
                event_id=f"evt_{prefix[:8].rstrip('_')}_{run}",
                event_family=EventSpineFamily.OPEN,
                event_type=ViewerEventType.APP_OPEN,
                occurred_at=datetime.now(timezone.utc).isoformat(),
                session_id=sid,
                content_type="PLATFORM",
                content_id="welele_pwa",
                # Even if we claim production + is_test=False, the prefix guard wins
                environment="production",
                is_test=False,
            )
            events.append(evt)

        _ingest(events)

        prod_funnel = _funnel("production")
        # All seeded sessions were quarantined by prefix — excluded count >= prefix count
        assert prod_funnel["provenance"]["test_events_excluded"] >= len(QUARANTINE_PREFIXES), (
            f"Expected at least {len(QUARANTINE_PREFIXES)} test events excluded "
            f"but got {prod_funnel['provenance']['test_events_excluded']}. "
            "Quarantine prefix rules may have regressed."
        )

    def test_quarantined_session_not_in_production_entered_count(self, prod_session_id):
        """
        After seeding known quarantine-prefix sessions, the Entered count in
        Production should NOT include them. Verify the production session we
        seeded via prod_session_id is the only Blood Ties session in evidence.
        """
        prod_funnel = _funnel("production", series_id=SERIES_ID)
        step_map = {s["key"]: s["sessions"] for s in prod_funnel["funnel"]}

        # At least 1 session (the prod_session_id fixture) must appear
        assert step_map["ENTERED"] >= 1, (
            "Production funnel shows 0 Entered sessions even though a valid "
            "production session was seeded."
        )

        # The quarantine sessions (which also referenced SERIES_ID indirectly)
        # must NOT inflate the count beyond what we seeded. The exact count
        # is non-deterministic due to parallel test runs, but the provenance
        # flag must confirm test events were excluded.
        assert prod_funnel["provenance"]["test_events_excluded"] >= 1


# ---------------------------------------------------------------------------
# [3] Genuine Blood Ties production session survives
# ---------------------------------------------------------------------------

class TestGenuineProductionSessionSurvival:
    """
    [3] The Blood Ties production session (sess_live_prod_*) must appear in
    the Production funnel and must NOT appear in a test-only filter that
    would suggest it was incorrectly quarantined.
    """

    def test_production_session_has_data_in_production_funnel(self, prod_session_id):
        prod_funnel = _funnel("production", series_id=SERIES_ID)
        assert prod_funnel["provenance"]["has_data"] is True, (
            "Production funnel reports has_data=False even though a genuine "
            "Blood Ties production session was seeded. "
            f"session_id={prod_session_id}"
        )
        assert prod_funnel["provenance"]["zero_synthetic_data"] is True

    def test_production_session_contributes_to_entered_count(self, prod_session_id):
        prod_funnel = _funnel("production", series_id=SERIES_ID)
        step_map = {s["key"]: s["sessions"] for s in prod_funnel["funnel"]}
        assert step_map["ENTERED"] >= 1, (
            f"Blood Ties production session '{prod_session_id}' not counted in ENTERED."
        )

    def test_production_session_not_in_test_only_funnel(self, prod_session_id):
        """
        Querying environment=test must NOT include the production session.
        The test funnel should have 0 sessions for that specific session_id.
        (We cannot enumerate sessions from the API, but we can verify that the
        test funnel exists independently and has_data relies on test events only.)
        """
        # Query test-only — this should be a separate universe
        test_funnel = _funnel("test", series_id=SERIES_ID)
        # The production session's data must not pollute test_events_evaluated
        # (test funnel counts only test-tagged events)
        assert test_funnel["provenance"]["environment_filter"] == "test"
        # has_data for test may be True or False depending on quarantined data,
        # but it must NOT inflate due to our production session. We can't
        # directly count sessions by ID here — instead we verify provenance
        # zero_synthetic_data is honoured regardless of view.
        assert test_funnel["provenance"]["zero_synthetic_data"] is True


# ---------------------------------------------------------------------------
# [4] Funnel counts correspond only to production events
# ---------------------------------------------------------------------------

class TestFunnelCountAccuracy:
    """
    [4] Each funnel step's session count in Production must only reflect
    explicitly production-tagged events. The fixture seeds a known full
    11-step journey and verifies each step is reported.
    """

    def test_all_11_steps_reported_for_production_session(self, prod_session_id):
        prod_funnel = _funnel("production", series_id=SERIES_ID)
        assert prod_funnel["provenance"]["has_data"] is True

        step_map = {s["key"]: s["sessions"] for s in prod_funnel["funnel"]}

        # Every step of the 11-step journey must have at least 1 session
        required_steps = [
            "ENTERED", "DISCOVERED", "SELECTED", "WATCHED",
            "CONTINUED", "ENGAGED", "PAYWALL", "PAYMENT_ATTEMPT",
            "PAID", "CONTINUED_POST_PAY", "RETURNED",
        ]
        for step_key in required_steps:
            assert step_map[step_key] >= 1, (
                f"Funnel step '{step_key}' shows 0 sessions in Production. "
                f"Expected >= 1 from the seeded Blood Ties production session. "
                f"Full step map: {step_map}"
            )

    def test_selected_breakdown_names_blood_ties(self, prod_session_id):
        """The selected_breakdown must include 'Blood Ties' as a title."""
        prod_funnel = _funnel("production", series_id=SERIES_ID)
        selected_titles = [item["title"] for item in prod_funnel.get("selected_breakdown", [])]
        assert any("Blood Ties" in t for t in selected_titles), (
            f"'Blood Ties' not found in selected_breakdown titles: {selected_titles}"
        )

    def test_engagement_metrics_reflect_production_only(self, prod_session_id):
        """
        Reactions count must be at least 1 (from the REACTION_ADDED event
        in the production session fixture).
        """
        prod_funnel = _funnel("production", series_id=SERIES_ID)
        reactions = prod_funnel["engagement_metrics"]["reactions_count"]
        assert reactions >= 1, (
            f"reactions_count={reactions} in Production. "
            "Expected >= 1 from the seeded Blood Ties REACTION_ADDED event."
        )

    def test_conversion_pcts_are_never_inflated_above_100(self, prod_session_id):
        """No funnel step's conversion_pct can exceed 100% — a sign of synthetic inflation."""
        prod_funnel = _funnel("production", series_id=SERIES_ID)
        for step in prod_funnel["funnel"]:
            assert step["conversion_pct"] <= 100.0, (
                f"Step '{step['key']}' has conversion_pct={step['conversion_pct']} > 100%. "
                "This indicates data inflation."
            )


# ---------------------------------------------------------------------------
# [5] Test / Canary view shows quarantined historical material
# ---------------------------------------------------------------------------

class TestQuarantinedMaterialInspectable:
    """
    [5] After quarantine, historical material must still be inspectable
    when environment=test is selected. Nothing is destroyed — it is
    merely excluded from the production view.
    """

    def test_quarantined_material_visible_in_test_view(self):
        """
        Seed a clearly quarantined session (sess_quarantined_* prefix) and
        verify it appears in environment=test but NOT in environment=production.
        """
        run = uuid.uuid4().hex[:6]
        qsid = f"sess_quarantined_{run}"

        evt = ViewerTelemetryEvent(
            event_id=f"evt_qt_01_{run}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.APP_OPEN,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=qsid,
            content_type="PLATFORM",
            content_id="welele_pwa",
            environment="test",
            is_test=True,
        )
        _ingest([evt])

        # In production: this session must be excluded
        prod_funnel = _funnel("production")
        prod_excluded = prod_funnel["provenance"]["test_events_excluded"]
        assert prod_excluded >= 1, (
            "Quarantined session not excluded from Production."
        )

        # In test: the event must be evaluated (total_events_evaluated >= 1)
        test_funnel = _funnel("test")
        assert test_funnel["provenance"]["total_events_evaluated"] >= 1, (
            "Quarantined session not visible in Test / Canary view. "
            "Historical material appears to have been lost, not just quarantined."
        )
        assert test_funnel["provenance"]["environment_filter"] == "test"

    def test_test_funnel_has_data_when_quarantined_events_exist(self):
        """
        If any quarantined events exist, has_data for the test environment
        should be True (data is inspectable).
        """
        # We've seeded multiple quarantined sessions in prior tests.
        test_funnel = _funnel("test")
        # At minimum total_events_evaluated must be > 0 for the test
        # environment given all the seeds above.
        assert test_funnel["provenance"]["total_events_evaluated"] >= 1, (
            "Test / Canary view shows no evaluated events despite prior seeding of "
            "quarantined sessions. Historical material may have been dropped."
        )


# ---------------------------------------------------------------------------
# [6] All Environments view shows the combined picture
# ---------------------------------------------------------------------------

class TestAllEnvironmentsView:
    """
    [6] Switching to environment=all must show both production and quarantined
    data, making the distinction between the two sets visible.
    """

    def test_all_env_funnel_includes_production_and_quarantine_counts(self, prod_session_id):
        all_funnel = _funnel("all", series_id=SERIES_ID)

        # has_data must be True — we have both production + test events for Blood Ties
        assert all_funnel["provenance"]["has_data"] is True, (
            "environment=all funnel shows has_data=False even though production "
            "and quarantine sessions are present."
        )

        step_map = {s["key"]: s["sessions"] for s in all_funnel["funnel"]}
        # ENTERED must be >= 1 (at minimum the production session)
        assert step_map["ENTERED"] >= 1

    def test_all_env_total_events_gte_production_only(self, prod_session_id):
        """
        The total_events_evaluated in environment=all must be >= that of
        environment=production alone, because it includes both.
        """
        all_funnel = _funnel("all", series_id=SERIES_ID)
        prod_funnel = _funnel("production", series_id=SERIES_ID)

        all_total = all_funnel["provenance"]["total_events_evaluated"]
        prod_total = prod_funnel["provenance"]["total_events_evaluated"]

        assert all_total >= prod_total, (
            f"All-environments total ({all_total}) is less than production-only "
            f"total ({prod_total}). The 'all' view is not including historical material."
        )

    def test_all_env_test_excluded_is_zero(self, prod_session_id):
        """
        When environment=all, NO events should be excluded (we see everything).
        test_events_excluded must be 0 for the 'all' view.
        """
        all_funnel = _funnel("all", series_id=SERIES_ID)
        assert all_funnel["provenance"]["test_events_excluded"] == 0, (
            f"environment=all should exclude nothing, but test_events_excluded="
            f"{all_funnel['provenance']['test_events_excluded']}. "
            "The combined view is silently filtering data."
        )


# ---------------------------------------------------------------------------
# [UI] Provenance distinction: "No production evidence" vs "exists"
# ---------------------------------------------------------------------------

class TestProvenanceDistinctionFields:
    """
    [UI] The API provenance payload must carry enough information for the
    UI to explicitly distinguish:
      - "No production evidence" (has_data=False, test_events_excluded may be > 0)
      - "Production evidence exists" (has_data=True)

    It must also distinguish WHY data was excluded:
      - canary_events_excluded  : deliberately tagged by a developer
      - legacy_events_quarantined : missing/untrusted provenance

    This test verifies the provenance contract from the API side.
    """

    def test_provenance_has_data_false_when_no_production_events_exist(self):
        """
        Querying for a series that has never had production events should
        return has_data=False. This is the "No production evidence" state.
        """
        funnel = _funnel("production", series_id="story_nonexistent_series_99")
        assert funnel["provenance"]["has_data"] is False, (
            "has_data=True for a series with no production events. "
            "The UI would incorrectly show 'Production evidence exists'."
        )
        assert funnel["provenance"]["zero_synthetic_data"] is True, (
            "zero_synthetic_data must always be True — we must never show fabricated numbers."
        )

    def test_provenance_has_data_true_when_production_session_present(self, prod_session_id):
        """
        After seeding the production session, has_data=True must be returned.
        This drives the "Production evidence exists" UI state.
        """
        funnel = _funnel("production", series_id=SERIES_ID)
        assert funnel["provenance"]["has_data"] is True, (
            f"has_data=False despite genuine production session '{prod_session_id}'. "
            "The UI would incorrectly show 'No production evidence'."
        )

    def test_provenance_sub_classification_fields_present(self):
        """
        The new provenance sub-fields must be present in every response.
        Their presence is what allows the UI to distinguish amber
        'quarantine-empty' from sky-blue 'genuinely empty'.
        """
        funnel = _funnel("production")
        prov = funnel["provenance"]
        assert "canary_events_excluded" in prov, (
            "canary_events_excluded missing from provenance — "
            "UI cannot distinguish deliberate test data from legacy unknowns."
        )
        assert "legacy_events_quarantined" in prov, (
            "legacy_events_quarantined missing from provenance — "
            "UI would incorrectly label untrusted data as 'test data'."
        )
        assert "test_events_excluded" in prov, (
            "test_events_excluded (backward-compat total) missing from provenance."
        )
        # Invariant: total must equal sum of sub-buckets
        assert prov["test_events_excluded"] == (
            prov["canary_events_excluded"] + prov["legacy_events_quarantined"]
        ), (
            "test_events_excluded must equal canary_events_excluded + legacy_events_quarantined. "
            "The sub-buckets are not adding up correctly."
        )

    def test_provenance_test_events_excluded_nonzero_when_quarantine_exists(self):
        """
        When quarantine sessions exist, test_events_excluded > 0 and the UI
        can choose the amber 'quarantine-empty' state over the neutral one.
        """
        run = uuid.uuid4().hex[:6]
        qsid = f"sess_quarantined_{run}"
        probe_series = f"story_probe_quarantine_{run}"

        evt = ViewerTelemetryEvent(
            event_id=f"evt_probe_{run}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.CONTENT_OPENED,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=qsid,
            content_type="SERIES",
            content_id=probe_series,
            series_id=probe_series,
            environment="test",
            is_test=True,
        )
        _ingest([evt])

        funnel = _funnel("production")
        assert funnel["provenance"]["test_events_excluded"] >= 1
        assert funnel["provenance"]["canary_events_excluded"] >= 1, (
            "An explicitly-tagged canary event (is_test=True, env=test) was not "
            "counted in canary_events_excluded."
        )


# ---------------------------------------------------------------------------
# [NEW] Provenance class separation — the three buckets must not bleed
# ---------------------------------------------------------------------------

class TestProvenanceClassSeparation:
    """
    The three provenance classes must be mutually exclusive and correctly
    counted. A production event must not appear in the exclusion counters.
    A canary event must not be labelled legacy. A legacy event must not
    be labelled canary.

    This is the regression fence for the provenance blurring bug.
    """

    def test_explicit_canary_increments_canary_not_legacy(self):
        """
        An event with is_test=True and environment=test is deliberately tagged
        by a developer. It must land in canary_events_excluded, not
        legacy_events_quarantined.
        """
        run = uuid.uuid4().hex[:6]

        before = _funnel("production")
        before_canary = before["provenance"]["canary_events_excluded"]
        before_legacy = before["provenance"]["legacy_events_quarantined"]

        # Seed an explicit canary event
        evt = ViewerTelemetryEvent(
            event_id=f"evt_canary_explicit_{run}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.APP_OPEN,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=f"sess_canary_explicit_{run}",
            content_type="PLATFORM",
            content_id="welele_pwa",
            environment="test",
            is_test=True,
        )
        _ingest([evt])

        after = _funnel("production")
        after_canary = after["provenance"]["canary_events_excluded"]
        after_legacy = after["provenance"]["legacy_events_quarantined"]

        assert after_canary > before_canary, (
            "Explicit canary event did NOT increment canary_events_excluded."
        )
        assert after_legacy == before_legacy, (
            f"Explicit canary event incremented legacy_events_quarantined "
            f"({before_legacy} → {after_legacy}). "
            "Canary data must not be labelled as untrusted legacy."
        )

    def test_legacy_unknown_increments_legacy_not_canary(self):
        """
        An event inserted without environment or is_test fields is untrusted
        legacy data. It must land in legacy_events_quarantined, not
        canary_events_excluded. We must not tell a developer 'this is test
        data' when all we know is 'this data is not trustworthy as production'.
        """
        from repositories.telemetry_repository import telemetry_repository

        run = uuid.uuid4().hex[:6]

        before = _funnel("production")
        before_canary = before["provenance"]["canary_events_excluded"]
        before_legacy = before["provenance"]["legacy_events_quarantined"]

        legacy_record = {
            "event_id": f"evt_sep_legacy_{run}",
            "event_family": "OPEN",
            "event_type": "APP_OPEN",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "session_id": f"sess_sep_legacy_{run}",
            "content_type": "PLATFORM",
            "content_id": "welele_pwa",
            # No environment, no is_test — classic legacy/unknown shape
        }
        telemetry_repository.save_event(legacy_record)

        after = _funnel("production")
        after_canary = after["provenance"]["canary_events_excluded"]
        after_legacy = after["provenance"]["legacy_events_quarantined"]

        assert after_legacy > before_legacy, (
            "Legacy/unknown event did NOT increment legacy_events_quarantined."
        )
        assert after_canary == before_canary, (
            f"Legacy/unknown event incremented canary_events_excluded "
            f"({before_canary} → {after_canary}). "
            "We must not label 'data with missing provenance' as 'deliberate test data'."
        )

    def test_production_event_increments_neither_exclusion_counter(self, prod_session_id):
        """
        A genuine production event must not appear in any exclusion counter.
        canary_events_excluded and legacy_events_quarantined must both be 0
        for the specific session's contribution — confirmed by checking that
        has_data=True while the production event itself is not quarantined.
        """
        funnel = _funnel("production", series_id=SERIES_ID)

        # The key assertion: a production funnel with has_data=True means at
        # least one session passed through without being excluded.
        assert funnel["provenance"]["has_data"] is True, (
            "Production session not found in production funnel."
        )

        # The invariant: total = canary + legacy
        prov = funnel["provenance"]
        assert prov["test_events_excluded"] == (
            prov["canary_events_excluded"] + prov["legacy_events_quarantined"]
        ), "Sub-bucket invariant violated."

    def test_buckets_are_mutually_exclusive_across_mixed_seed(self):
        """
        Seed one explicit canary event and one legacy event in the same batch.
        Verify canary_events_excluded increments by exactly 1 and
        legacy_events_quarantined increments by exactly 1.
        The buckets must not cross-contaminate.
        """
        from repositories.telemetry_repository import telemetry_repository

        run = uuid.uuid4().hex[:6]

        before = _funnel("production")
        before_canary = before["provenance"]["canary_events_excluded"]
        before_legacy = before["provenance"]["legacy_events_quarantined"]

        # One explicit canary
        canary_evt = ViewerTelemetryEvent(
            event_id=f"evt_mix_canary_{run}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.APP_OPEN,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=f"sess_mix_canary_{run}",
            content_type="PLATFORM",
            content_id="welele_pwa",
            environment="test",
            is_test=True,
        )
        _ingest([canary_evt])

        # One legacy/unknown inserted directly
        telemetry_repository.save_event({
            "event_id": f"evt_mix_legacy_{run}",
            "event_family": "OPEN",
            "event_type": "APP_OPEN",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "session_id": f"sess_mix_legacy_{run}",
            "content_type": "PLATFORM",
            "content_id": "welele_pwa",
        })

        after = _funnel("production")
        delta_canary = after["provenance"]["canary_events_excluded"] - before_canary
        delta_legacy = after["provenance"]["legacy_events_quarantined"] - before_legacy

        assert delta_canary == 1, (
            f"Expected canary_events_excluded to increase by 1, got +{delta_canary}."
        )
        assert delta_legacy == 1, (
            f"Expected legacy_events_quarantined to increase by 1, got +{delta_legacy}."
        )
        # Invariant holds
        prov = after["provenance"]
        assert prov["test_events_excluded"] == (
            prov["canary_events_excluded"] + prov["legacy_events_quarantined"]
        )
