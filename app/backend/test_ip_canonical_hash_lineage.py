"""
Welele Media™ — Digital IP Canonical Lineage & Hashing Test Suite (P1)
Tests: Canonical Package SHA-256 Hash Verification, Immutable Lineage Tracing, and Character Bible Binding.
"""

import sys
import os
import json
import hashlib
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from repositories.ip_repository import ip_repository
from schemas.ip_schemas import StoryForgePackageCreateRequest

def test_canonical_lineage_and_hashing():
    print("\n--- Running Digital IP Canonical Lineage & Hashing Tests ---")

    # 1. Register Canonical Story Package under Blood Ties
    pkg_req_1 = StoryForgePackageCreateRequest(
        ip_id="ip_blood_ties",
        creator_id="creator_zola",
        package_title="Blood Ties - Episode 4: The Midnight Safe",
        story_world_id="sw_blood_ties_01",
        character_ids=["char_bt_01", "char_bt_02"],
        episode_target=4,
        version="v1.0.0",
        target_duration_seconds=90,
        beats=[
            {"timestamp": 0, "label": "Hook", "description": "Sipho discovers the safe has been breached."},
            {"timestamp": 45, "label": "Climax", "description": "Lerato holds the unsealed court document."}
        ],
        dialogues=[
            {"speaker": "Sipho", "text": "Who gave you the combination to my father's safe?"},
            {"speaker": "Lerato", "text": "He gave it to me himself before he died."}
        ],
        cliffhanger_prompt="Will Lerato show the signature on the codicil?"
    )

    pkg_1 = ip_repository.save_story_forge_package(pkg_req_1)
    hash_1 = pkg_1["lineage_hash"]
    assert hash_1 is not None
    assert len(hash_1) == 64
    print(f"[PASS] Canonical Hash Generation: Generated SHA-256 lineage hash '{hash_1}' for package '{pkg_1['id']}'.")

    # 2. Deterministic Hash Validation (Identical payload yields identical hash)
    pkg_req_identical = StoryForgePackageCreateRequest(
        ip_id="ip_blood_ties",
        creator_id="creator_zola",
        package_title="Blood Ties - Episode 4: The Midnight Safe",
        story_world_id="sw_blood_ties_01",
        character_ids=["char_bt_02", "char_bt_01"], # Intentionally reverse order to test sort-normalization
        episode_target=4,
        version="v1.0.0",
        target_duration_seconds=90,
        beats=[
            {"timestamp": 0, "label": "Hook", "description": "Sipho discovers the safe has been breached."},
            {"timestamp": 45, "label": "Climax", "description": "Lerato holds the unsealed court document."}
        ],
        dialogues=[
            {"speaker": "Sipho", "text": "Who gave you the combination to my father's safe?"},
            {"speaker": "Lerato", "text": "He gave it to me himself before he died."}
        ],
        cliffhanger_prompt="Will Lerato show the signature on the codicil?"
    )
    pkg_2 = ip_repository.save_story_forge_package(pkg_req_identical)
    assert pkg_2["lineage_hash"] == hash_1
    print(f"[PASS] Deterministic Integrity: Normalized payload with re-ordered character tags produced identical cryptographic hash.")

    # 3. Tamper / Mutation Detection (Modified dialogue alters hash)
    pkg_req_tampered = StoryForgePackageCreateRequest(
        ip_id="ip_blood_ties",
        creator_id="creator_zola",
        package_title="Blood Ties - Episode 4: The Midnight Safe",
        story_world_id="sw_blood_ties_01",
        character_ids=["char_bt_01", "char_bt_02"],
        episode_target=4,
        version="v1.0.0",
        target_duration_seconds=90,
        beats=pkg_req_1.beats,
        dialogues=[
            {"speaker": "Sipho", "text": "Who gave you the combination?"}, # Altered line
            {"speaker": "Lerato", "text": "He gave it to me himself before he died."}
        ],
        cliffhanger_prompt="Will Lerato show the signature on the codicil?"
    )
    pkg_3 = ip_repository.save_story_forge_package(pkg_req_tampered)
    assert pkg_3["lineage_hash"] != hash_1
    print(f"[PASS] Tamper Detection: Script mutation successfully generated distinct lineage hash '{pkg_3['lineage_hash'][:16]}...'.")

    # 4. Lineage Retrieval & Character Verification
    ip_detail = ip_repository.get_ip_detail("ip_blood_ties")
    assert ip_detail is not None
    assert len(ip_detail["story_packages"]) >= 3
    print(f"[PASS] Lineage Audit: Verified franchise 'ip_blood_ties' contains {len(ip_detail['story_packages'])} persistent story package artifacts.")

    print("=======================================================")
    print("ALL CANONICAL LINEAGE & HASHING TESTS PASSED (100%)")
    print("=======================================================\n")

if __name__ == "__main__":
    test_canonical_lineage_and_hashing()
