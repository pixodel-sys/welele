"""
Welele Media™ — Digital IP Domain Tests (GAP-001 & GAP-005)
Validates: IP Creation, Story World rules, Character bibles, and Rights split boundary validation (<= 100%).
"""

import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from repositories.ip_repository import ip_repository
from services.rbac_service import create_access_token

client = TestClient(app)

def test_digital_ip_domain():
    print("\n--- Running Digital IP Domain Tests ---")

    creator_token = create_access_token(user_id="creator_lerato", role="creator")
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    # 1. List Digital IPs
    res_list = client.get("/api/ip/list")
    assert res_list.status_code == 200
    ips = res_list.json()
    assert len(ips) > 0
    print(f"[PASS] Digital IP List: Found {len(ips)} canonical franchise(s).")

    # 2. Get IP Detail (Full Hierarchy)
    res_detail = client.get("/api/ip/ip_blood_ties")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert "story_world" in detail
    assert "characters" in detail
    assert "rights_ledger" in detail
    assert len(detail["characters"]) >= 2
    assert len(detail["rights_ledger"]) >= 2
    print(f"[PASS] IP Detail: Loaded '{detail['ip']['title']}' with {len(detail['characters'])} character bibles and {len(detail['rights_ledger'])} rights splits.")

    # 3. Create New Digital IP with Rights Splits
    new_ip_payload = {
        "title": "Queen of Jozi: Golden Crown",
        "franchise_code": "IP-QUEEN-JOZI",
        "logline": "A nightlife queenpin navigates high-stakes corporate espionage and street loyalty.",
        "synopsis": "Set in the exclusive clubs of Rosebank and hidden underground vaults of Braamfontein.",
        "genre": "High Fashion Crime Drama",
        "primary_language": "isiZulu",
        "master_owner_id": "creator_lerato",
        "story_world": {
            "world_name": "The Jozi Nightlife Syndicate",
            "geographical_setting": "Rosebank & Braamfontein, Johannesburg",
            "time_period": "Contemporary",
            "mythology_and_rules": "Loyalty to the house supersedes blood; club receipts hide offshore banking routing.",
            "cultural_context": "High-fashion urban glam with deep township grit."
        },
        "characters": [
            {
                "name": "Queen Nomsa",
                "role": "protagonist",
                "archetype": "The Sovereign Nightclub Queen",
                "secret_motivation": "Protect her sister from the diamond cartel.",
                "fatal_flaw": "Trusts her head of security too deeply.",
                "signature_quote": "In my club, even the shadows pay tax."
            }
        ],
        "rights_splits": [
            {
                "beneficiary_user_id": "creator_lerato",
                "stakeholder_role": "Showrunner",
                "royalty_split_pct": 60.0,
                "territory": "GLOBAL",
                "medium": "ALL_MEDIA",
                "contract_ref": "WELELE-QJ-001"
            },
            {
                "beneficiary_user_id": "creator_zola",
                "stakeholder_role": "Co-Producer",
                "royalty_split_pct": 40.0,
                "territory": "GLOBAL",
                "medium": "ALL_MEDIA",
                "contract_ref": "WELELE-QJ-002"
            }
        ]
    }

    res_create = client.post("/api/ip/create", json=new_ip_payload, headers=creator_headers)
    assert res_create.status_code == 200, f"IP creation failed: {res_create.text}"
    created_ip = res_create.json()
    assert created_ip["ip"]["franchise_code"] == "IP-QUEEN-JOZI"
    assert len(created_ip["rights_ledger"]) == 2
    print(f"[PASS] IP Creation: Registered franchise '{created_ip['ip']['title']}' (Code: {created_ip['ip']['franchise_code']}).")

    # 4. Validate Rights Split Overflow Protection (> 100%)
    invalid_splits_payload = dict(new_ip_payload)
    invalid_splits_payload["franchise_code"] = "IP-INVALID-OVERFLOW"
    invalid_splits_payload["rights_splits"] = [
        {"beneficiary_user_id": "u1", "stakeholder_role": "Showrunner", "royalty_split_pct": 80.0, "territory": "GLOBAL", "medium": "ALL", "contract_ref": "C1"},
        {"beneficiary_user_id": "u2", "stakeholder_role": "Co-Producer", "royalty_split_pct": 40.0, "territory": "GLOBAL", "medium": "ALL", "contract_ref": "C2"}
    ]
    res_invalid = client.post("/api/ip/create", json=invalid_splits_payload, headers=creator_headers)
    assert res_invalid.status_code == 400, "Rights split overflow (> 100%) was not properly rejected by validation"
    print(f"[PASS] Rights Validation: Successfully rejected 120% royalty split overflow with 400 Bad Request.")

    print("=======================================================")
    print("ALL DIGITAL IP DOMAIN TESTS PASSED (100% SUCCESS)")
    print("=======================================================\n")

if __name__ == "__main__":
    test_digital_ip_domain()

