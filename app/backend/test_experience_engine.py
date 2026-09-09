"""
Welele Media™ — Experience Engine (WEE) Automated Compliance Test
Validates Manifest delivery, catalog hydration, draft authoring, and simulated preview.
"""

from fastapi.testclient import TestClient
from main import app
from services.experience_engine import ExperienceEngine

client = TestClient(app)

def test_experience_engine_lifecycle():
    print("Testing Welele Experience Engine (WEE)...")

    # 1. Managed Pages
    res = client.get("/api/experience/pages")
    assert res.status_code == 200, f"Failed listing pages: {res.text}"
    pages = res.json().get("pages", [])
    assert any(p["page_id"] == "home" for p in pages), "Home page missing from managed pages"
    print("[PASS] WEE Layer 3 (API): Managed pages listed successfully.")

    # 2. Live Page Experience Delivery
    res_home = client.get("/api/experience/page/home")
    assert res_home.status_code == 200, f"Failed getting live home manifest: {res_home.text}"
    manifest = res_home.json()
    assert manifest["page_id"] == "home"
    assert len(manifest["sections"]) > 0
    print(f"[PASS] WEE Layer 4 (Manifest): Live home manifest resolved with {len(manifest['sections'])} sections.")

    # Verify Hero section hydration
    hero_sec = next((s for s in manifest["sections"] if s["type"] == "HERO_CAROUSEL"), None)
    assert hero_sec is not None, "Hero carousel section missing"
    assert len(hero_sec["items"]) > 0, "Hero slots empty"
    first_slot = hero_sec["items"][0]
    assert "story" in first_slot, "Catalog hydration failed: slot missing attached story object"
    assert first_slot.get("headline_override") is not None or "title" in first_slot["story"], "Slot story or headline missing"
    print(f"[PASS] WEE Layer 2 (Engine): Catalog hydration verified on slot '{first_slot['slot_id']}' with story '{first_slot['story']['title']}'.")

    # 3. Draft authoring & Simulated Time-Travel Preview
    preview_res = client.get("/api/experience/preview/home?state=draft&simulated_time=2026-10-01T12:00:00Z")
    assert preview_res.status_code == 200, "Preview endpoint failed"
    preview_manifest = preview_res.json()
    assert preview_manifest["page_id"] == "home"
    print("[PASS] WEE Time-Travel Preview: Evaluated simulated timestamp 2026-10-01T12:00:00Z successfully.")

    # 4. Draft modification & Publish
    save_draft_res = client.put("/api/experience/page/home/draft", json={
        "meta": {"title": "Welele™ | Curated African Dramas", "theme": "dark_gold_glow"},
        "sections": manifest["sections"]
    })
    assert save_draft_res.status_code == 200, "Save draft failed"

    pub_res = client.post("/api/experience/page/home/publish", json={})
    assert pub_res.status_code == 200, "Publish failed"
    pub_data = pub_res.json()
    assert pub_data["status"] == "published"
    print(f"[PASS] WEE Publishing: Promoted draft to LIVE version '{pub_data['version']}'.")

    print("\n=======================================================")
    print("ALL WELELE EXPERIENCE ENGINE (WEE) TESTS PASSED!")
    print("=======================================================")

if __name__ == "__main__":
    test_experience_engine_lifecycle()
