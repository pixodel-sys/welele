"""
Welele Media™ — Creator Payout & Ledger Reconciliation Test (P1)
Validates:
1. Idempotent payout requests.
2. Balance validation & atomic deduction.
3. Canonical projection via GET /api/creators/{creator_id}/transactions without secondary store.
4. COMMERCE domain audit event emission.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from main import app
from database import db
from services.rbac_service import create_access_token
from services.audit_service import audit_service

client = TestClient(app)

def get_creator_headers():
    token = create_access_token(user_id="creator_zola", role="creator", creator_id="creator_zola")
    return {"Authorization": f"Bearer {token}"}

def test_creator_payout_and_ledger_reconciliation():
    headers = get_creator_headers()
    creator_id = "creator_zola"

    # Seed creator balance
    creators = db.get("creators")
    creator = next((c for c in creators if c["id"] == creator_id), None)
    if not creator:
        creator = {
            "id": creator_id,
            "name": "Zola Dlamini",
            "coin_earnings": 10000
        }
        db.insert("creators", creator)
    else:
        db.update("creators", creator_id, {"coin_earnings": 10000})

    initial_coins = 10000
    payout_coins = 2000
    idemp_key = f"idemp_test_{uuid.uuid4().hex[:8]}"

    # 1. Successful Payout Request
    payout_payload = {
        "creator_id": creator_id,
        "amount_coins": payout_coins,
        "amount_local": 260.00,
        "currency": "ZAR",
        "payout_method": "MTN MoMo (+27830000001)",
        "account_details": "Zola Dlamini",
        "idempotency_key": idemp_key
    }

    res = client.post("/api/monetization/payout", json=payout_payload)
    assert res.status_code == 200, f"Payout failed: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert data["remaining_coin_balance"] == initial_coins - payout_coins
    payout_id = data["payout_id"]

    # 2. Idempotency Test: Replaying same request returns identical payout record without second deduction
    res_replay = client.post("/api/monetization/payout", json=payout_payload)
    assert res_replay.status_code == 200
    replay_data = res_replay.json()
    assert replay_data["is_idempotent_replay"] is True
    assert replay_data["payout_id"] == payout_id

    # Verify creator balance remains 8000 (not 6000)
    creator_after = next(c for c in db.get("creators") if c["id"] == creator_id)
    assert creator_after["coin_earnings"] == 8000

    # 3. Overdraft Rejection Test: Requesting more than available balance must fail
    res_overdraft = client.post("/api/monetization/payout", json={
        "creator_id": creator_id,
        "amount_coins": 50000,
        "amount_local": 6500.00,
        "currency": "ZAR",
        "payout_method": "MTN MoMo",
        "account_details": "Zola Dlamini",
        "idempotency_key": f"idemp_fail_{uuid.uuid4().hex[:8]}"
    })
    assert res_overdraft.status_code == 400
    assert "Insufficient coin balance" in res_overdraft.text

    # 4. Projection Test: GET /api/creators/{creator_id}/transactions returns the canonical payout
    res_txs = client.get(f"/api/creators/{creator_id}/transactions", headers=headers)
    assert res_txs.status_code == 200
    txs_data = res_txs.json()
    assert txs_data["total"] >= 1
    matching_tx = next((t for t in txs_data["transactions"] if t["id"] == payout_id), None)
    assert matching_tx is not None
    assert matching_tx["settlement_status"] == "Settlement Pending (External Rails Unproven)"
    assert matching_tx["idempotency_key"] == idemp_key

    # 5. Audit Trail Verification
    audit_chain = audit_service.local_get("security_audit_ledger")
    payout_audit = next((a for a in audit_chain if a.get("target_id") == payout_id), None)
    assert payout_audit is not None
    assert payout_audit["domain"] == "COMMERCE"
    assert payout_audit["event_type"] == "commerce.payout_requested"
