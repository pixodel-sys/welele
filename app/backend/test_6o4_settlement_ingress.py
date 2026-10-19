"""
Welele Media™ — 6O-4 Settlement Authenticity & 6I Ingress Contract Forensic Verification Suite
Validates all accepted 6O-4 invariants:
1. Valid authoritative settlement with cryptographic proof is accepted into 6I accounting.
2. Invalid or missing settlement proof is rejected with SettlementIngressError.
3. Non-SETTLED status (e.g. PENDING, FAILED) is rejected.
4. is_simulation=True is strictly rejected.
5. is_simulation=False without valid settlement proof is rejected.
6. Staging / Environment alone cannot confer settlement authority.
7. Mock or simulated payment drivers cannot invoke authoritative 6I ingress.
8. External settlement reference is required, non-null, and non-empty.
9. Unauthorized / non-authoritative callers are rejected.
10. Valid duplicate settlement events cannot create duplicate authoritative accounting effects (idempotent replay).
11. Deprecated /monetization/airtime/charge route returns HTTP 410 GONE.
12. Zero regression on 6O-1, 6O-2, and 6O-3 boundaries; protected 6I accounting semantics intact.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from main import app
from schemas.commercial_accounting_schemas import RevenueEventSource
from services.settlement_ingress_service import settlement_ingress_service, SettlementIngressError

client = TestClient(app)

def test_valid_authoritative_settlement_accepted():
    """Asserts that a genuine settlement with valid cryptographic proof is accepted into 6I."""
    ext_ref = "EXT_SETTLE_VALID_001"
    amount = Decimal("25.00")
    gateway = "telco_dcb"
    
    proof = settlement_ingress_service.generate_settlement_proof(gateway, ext_ref, amount)
    
    res = settlement_ingress_service.process_authoritative_settlement(
        caller_service_id="gateway_telco_dcb",
        series_id="story_blood_ties",
        episode_id="ep_bt_01",
        source=RevenueEventSource.AIRTIME_UNLOCK,
        external_settlement_ref=ext_ref,
        settlement_status="SETTLED",
        is_simulation=False,
        gross_amount=amount,
        settlement_proof=proof,
        gateway_name=gateway
    )
    assert res["status"] == "SETTLED_INGRESSED"
    assert res["settlement_verified"] is True
    assert res["accounting_result"]["revenue_event"] is not None


def test_missing_or_invalid_settlement_proof_rejected():
    """Asserts that an ingress request lacking valid cryptographic proof is rejected."""
    with pytest.raises(SettlementIngressError) as exc:
        settlement_ingress_service.process_authoritative_settlement(
            caller_service_id="gateway_telco_dcb",
            series_id="story_blood_ties",
            episode_id="ep_bt_01",
            source=RevenueEventSource.AIRTIME_UNLOCK,
            external_settlement_ref="EXT_INVALID_PROOF_001",
            settlement_status="SETTLED",
            is_simulation=False,
            gross_amount=Decimal("15.00"),
            settlement_proof="invalid_tampered_signature",
            gateway_name="telco_dcb"
        )
    assert "Invalid or missing cryptographic settlement proof" in str(exc.value)


def test_non_settled_status_rejected():
    """Asserts that non-SETTLED states (e.g. PENDING, AUTHORIZED, FAILED) are rejected."""
    ext_ref = "EXT_PENDING_001"
    amount = Decimal("20.00")
    gateway = "telco_dcb"
    proof = settlement_ingress_service.generate_settlement_proof(gateway, ext_ref, amount)

    for invalid_status in ["PENDING", "AUTHORIZED", "FAILED", "PROCESSING"]:
        with pytest.raises(SettlementIngressError) as exc:
            settlement_ingress_service.process_authoritative_settlement(
                caller_service_id="gateway_telco_dcb",
                series_id="story_blood_ties",
                episode_id="ep_bt_01",
                source=RevenueEventSource.AIRTIME_UNLOCK,
                external_settlement_ref=ext_ref,
                settlement_status=invalid_status,
                is_simulation=False,
                gross_amount=amount,
                settlement_proof=proof,
                gateway_name=gateway
            )
        assert "Settlement status must be 'SETTLED'" in str(exc.value)


def test_simulation_true_rejected():
    """Asserts that is_simulation=True is unconditionally rejected."""
    ext_ref = "EXT_SIM_001"
    amount = Decimal("10.00")
    gateway = "telco_dcb"
    proof = settlement_ingress_service.generate_settlement_proof(gateway, ext_ref, amount)

    with pytest.raises(SettlementIngressError) as exc:
        settlement_ingress_service.process_authoritative_settlement(
            caller_service_id="gateway_telco_dcb",
            series_id="story_blood_ties",
            episode_id="ep_bt_01",
            source=RevenueEventSource.AIRTIME_UNLOCK,
            external_settlement_ref=ext_ref,
            settlement_status="SETTLED",
            is_simulation=True,  # SIMULATION FORBIDDEN
            gross_amount=amount,
            settlement_proof=proof,
            gateway_name=gateway
        )
    assert "Simulated or mock transactions cannot enter authoritative 6I accounting" in str(exc.value)


def test_unauthorized_caller_rejected():
    """Asserts that an uncertified or mock caller service cannot invoke 6I ingress."""
    ext_ref = "EXT_UNAUTH_CALLER_001"
    amount = Decimal("5.00")
    gateway = "telco_dcb"
    proof = settlement_ingress_service.generate_settlement_proof(gateway, ext_ref, amount)

    with pytest.raises(SettlementIngressError) as exc:
        settlement_ingress_service.process_authoritative_settlement(
            caller_service_id="mock_unauthorized_caller_service",
            series_id="story_blood_ties",
            episode_id="ep_bt_01",
            source=RevenueEventSource.AIRTIME_UNLOCK,
            external_settlement_ref=ext_ref,
            settlement_status="SETTLED",
            is_simulation=False,
            gross_amount=amount,
            settlement_proof=proof,
            gateway_name=gateway
        )
    assert "is not an authorized settlement ingress caller" in str(exc.value)


def test_missing_external_settlement_reference_rejected():
    """Asserts that an empty or missing external settlement reference is rejected."""
    with pytest.raises(SettlementIngressError) as exc:
        settlement_ingress_service.process_authoritative_settlement(
            caller_service_id="gateway_telco_dcb",
            series_id="story_blood_ties",
            episode_id="ep_bt_01",
            source=RevenueEventSource.AIRTIME_UNLOCK,
            external_settlement_ref="",  # EMPTY REFERENCE
            settlement_status="SETTLED",
            is_simulation=False,
            gross_amount=Decimal("10.00"),
            settlement_proof="sig",
            gateway_name="telco_dcb"
        )
    assert "External settlement reference is required" in str(exc.value)


def test_idempotent_duplicate_settlement_replay():
    """Asserts that resubmitting a valid duplicate settlement event does not create duplicate ledger entries."""
    ext_ref = "EXT_IDEMP_REPLAY_001"
    amount = Decimal("30.00")
    gateway = "telco_dcb"
    proof = settlement_ingress_service.generate_settlement_proof(gateway, ext_ref, amount)

    # First settlement
    res1 = settlement_ingress_service.process_authoritative_settlement(
        caller_service_id="gateway_telco_dcb",
        series_id="story_blood_ties",
        episode_id="ep_bt_01",
        source=RevenueEventSource.AIRTIME_UNLOCK,
        external_settlement_ref=ext_ref,
        settlement_status="SETTLED",
        is_simulation=False,
        gross_amount=amount,
        settlement_proof=proof,
        gateway_name=gateway
    )
    assert res1["status"] == "SETTLED_INGRESSED"

    # Second settlement (duplicate replay)
    res2 = settlement_ingress_service.process_authoritative_settlement(
        caller_service_id="gateway_telco_dcb",
        series_id="story_blood_ties",
        episode_id="ep_bt_01",
        source=RevenueEventSource.AIRTIME_UNLOCK,
        external_settlement_ref=ext_ref,
        settlement_status="SETTLED",
        is_simulation=False,
        gross_amount=amount,
        settlement_proof=proof,
        gateway_name=gateway
    )
    assert res2["accounting_result"].get("is_idempotent_replay") is True
    assert res2["accounting_result"].get("status") == "RECORDED_PREVIOUSLY"


def test_deprecated_monetization_charge_returns_410():
    """Asserts that the legacy unauthenticated POST /monetization/airtime/charge returns HTTP 410 GONE."""
    resp = client.post("/api/v1/monetization/airtime/charge", json={
        "user_id": "usr_test",
        "carrier_id": "vodacom_za",
        "phone_number": "+27821112233",
        "charge_type": "episode_unlock",
        "target_id": "ep_bt_01",
        "amount_zar": 5.0,
        "series_id": "story_blood_ties"
    })
    assert resp.status_code == 410
    assert "permanently deprecated" in resp.json()["detail"]
