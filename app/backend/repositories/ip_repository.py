"""
Welele Media™ — Digital IP Repository (GAP-001 & GAP-005)
Manages canonical IP assets, story worlds, character bibles, multi-party rights, and versioned story packages.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .base_repository import BaseRepository
from schemas.ip_schemas import CreateIPRequest, StoryForgePackageCreateRequest

class IPRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self._seed_default_ips()

    def _seed_default_ips(self):
        existing = self.local_get("digital_ips")
        if not existing:
            # Seed canonical Digital IPs
            ip_1 = {
                "id": "ip_blood_ties",
                "title": "Blood Ties: Jozi Dynasty",
                "franchise_code": "IP-BLOOD-TIES",
                "logline": "Two warring families collide over Johannesburg's gold transit routes in high-stakes 90-second showdowns.",
                "synopsis": "Set across Sandton high-rises and Alexandra taxi ranks, Blood Ties chronicles the inheritance war triggered by an unsealed midnight codicil.",
                "genre": "Dynasty & Revenge Thriller",
                "primary_language": "isiZulu",
                "master_owner_id": "creator_zola",
                "global_valuation_usd": 1250000.00,
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("digital_ips", ip_1)

            # Story World
            self.local_insert("story_worlds", {
                "id": "sw_blood_ties_01",
                "ip_id": "ip_blood_ties",
                "world_name": "The Gauteng Gold Corridor",
                "geographical_setting": "Alexandra Workshop & Sandton Financial District",
                "time_period": "Contemporary 2026",
                "mythology_and_rules": "All power flows through the unwritten rank ledger; ancestral blood debts cannot be forgiven with money.",
                "cultural_context": "High-octane urban Mzansi dialogue blending deep isiZulu with modern Jozi vernacular.",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            # Character Bibles
            self.local_insert("character_bibles", {
                "id": "char_bt_01",
                "ip_id": "ip_blood_ties",
                "name": "Sipho Dlamini",
                "role": "protagonist",
                "archetype": "The Rightful Outcast",
                "secret_motivation": "Rebuild his father’s legacy without spilling blood in the township.",
                "fatal_flaw": "Hesitates to arm his allies until cornered.",
                "signature_quote": "The grease on my hands washes off; betrayal stays forever.",
                "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            self.local_insert("character_bibles", {
                "id": "char_bt_02",
                "ip_id": "ip_blood_ties",
                "name": "Lerato Khumalo",
                "role": "antagonist",
                "archetype": "The Ruthless Heiress",
                "secret_motivation": "Prove to the board that she alone has the iron will to rule.",
                "fatal_flaw": "Underestimates community loyalty in Alexandra.",
                "signature_quote": "In Sandton, contracts are signed in blood and gold.",
                "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            # Rights Splits
            self.local_insert("rights_ledger", {
                "id": "rights_bt_01",
                "ip_id": "ip_blood_ties",
                "beneficiary_user_id": "creator_zola",
                "stakeholder_role": "Showrunner & Creator",
                "royalty_split_pct": 70.0,
                "territory": "GLOBAL",
                "medium": "ALL_MEDIA",
                "contract_ref": "WELELE-CTR-2026-001",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            self.local_insert("rights_ledger", {
                "id": "rights_bt_02",
                "ip_id": "ip_blood_ties",
                "beneficiary_user_id": "creator_lerato",
                "stakeholder_role": "Lead Writer",
                "royalty_split_pct": 30.0,
                "territory": "GLOBAL",
                "medium": "ALL_MEDIA",
                "contract_ref": "WELELE-CTR-2026-002",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            # 2. Queen of Jozi
            self.local_insert("digital_ips", {
                "id": "ip_queen_of_jozi",
                "title": "Queen of Jozi: Mining Syndicate",
                "franchise_code": "IP-QUEEN-JOZI",
                "logline": "One woman's ruthless rise to the top of Johannesburg's underworld.",
                "synopsis": "Nina Khumalo steps from the shadows to reclaim the throne in Sandton when rival syndicates attempt a hostile takeover.",
                "genre": "Crime • Empire • Dynasty",
                "primary_language": "isiZulu",
                "master_owner_id": "creator_zola",
                "global_valuation_usd": 1500000.00,
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            self.local_insert("story_worlds", {
                "id": "sw_queen_of_jozi_01",
                "ip_id": "ip_queen_of_jozi",
                "world_name": "Sandton Syndicate Towers",
                "geographical_setting": "Rosebank Penthouses & Reef Gold Refineries",
                "time_period": "Contemporary 2026",
                "mythology_and_rules": "He who controls the gold refinery permits sets the law across Gauteng.",
                "cultural_context": "Elite cosmopolitan Jozi corporate warfare meets street security enforcement.",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            # 3. The CEO's Secret Wife
            self.local_insert("digital_ips", {
                "id": "ip_ceo_wife",
                "title": "The CEO's Secret Wife: Dynasty Contract",
                "franchise_code": "IP-CEO-WIFE",
                "logline": "A fake marriage with a ruthless billionaire CEO turns into a battle for an empire.",
                "synopsis": "A 1-year contract marriage to save a heritage estate turns into forbidden passion amidst Sandton boardroom sabotage.",
                "genre": "Romance • Contract Marriage",
                "primary_language": "English",
                "master_owner_id": "creator_amaka",
                "global_valuation_usd": 2100000.00,
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            self.local_insert("story_worlds", {
                "id": "sw_ceo_wife_01",
                "ip_id": "ip_ceo_wife",
                "world_name": "Ndlovu Holdings & Clifton Waterfront",
                "geographical_setting": "Sandton Headquarters & Cape Town Penthouses",
                "time_period": "Contemporary 2026",
                "mythology_and_rules": "Boardroom voting shares determine family sovereignty.",
                "cultural_context": "High-fashion Pan-African luxury romance with high-society drama.",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            # 4. Umembeso: Royal Secrets
            self.local_insert("digital_ips", {
                "id": "ip_umembeso",
                "title": "Umembeso: Royal Bloodline",
                "franchise_code": "IP-UMEMBESO",
                "logline": "A traditional royal wedding where every gift carries a deadly secret.",
                "synopsis": "Ancient family talismans and 30-year secrets clash during an opulent royal dowry ceremony.",
                "genre": "Romance • Royal • Mystery",
                "primary_language": "isiZulu",
                "master_owner_id": "creator_zola",
                "global_valuation_usd": 980000.00,
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            # 5. The Hustlers of Alex
            self.local_insert("digital_ips", {
                "id": "ip_the_hustlers",
                "title": "The Hustlers of Alex: Solar Syndicate",
                "franchise_code": "IP-HUSTLERS-ALEX",
                "logline": "Three township innovators invent an off-grid solar micro-grid and fight off cartels.",
                "synopsis": "Township resilience turns into an all-out turf battle against energy monopolists.",
                "genre": "Township Crime • Heist • Hustle",
                "primary_language": "isiZulu",
                "master_owner_id": "creator_kabelo",
                "global_valuation_usd": 850000.00,
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            # 6. Durban Nights
            self.local_insert("digital_ips", {
                "id": "ip_durban_nights",
                "title": "Durban Nights: Gqom Underworld",
                "franchise_code": "IP-DURBAN-NIGHTS",
                "logline": "Where coastal glamour meets the darkest beats of the underground.",
                "synopsis": "A music producer unearths dangerous shipping secrets buried in Durban Harbor.",
                "genre": "Coastal Noir • Music • Betrayal",
                "primary_language": "isiZulu",
                "master_owner_id": "creator_nomvula",
                "global_valuation_usd": 920000.00,
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

    def list_ips(self) -> List[Dict[str, Any]]:
        ips = self.local_get("digital_ips")
        series_list = self.local_get("series")
        result = []
        for ip in ips:
            ip_copy = dict(ip)
            ip_copy["series_count"] = len([s for s in series_list if s.get("ip_id") == ip["id"]])
            result.append(ip_copy)
        return result

    def get_ip_detail(self, ip_id: str) -> Optional[Dict[str, Any]]:
        ips = self.local_get("digital_ips")
        ip = next((i for i in ips if i["id"] == ip_id or i["franchise_code"] == ip_id), None)
        if not ip:
            return None

        actual_id = ip["id"]
        story_worlds = [w for w in self.local_get("story_worlds") if w.get("ip_id") == actual_id]
        characters = [c for c in self.local_get("character_bibles") if c.get("ip_id") == actual_id]
        rights = [r for r in self.local_get("rights_ledger") if r.get("ip_id") == actual_id]
        series = [s for s in self.local_get("series") if s.get("ip_id") == actual_id]
        packages = [p for p in self.local_get("story_forge_packages") if p.get("ip_id") == actual_id]

        return {
            "ip": ip,
            "story_world": story_worlds[0] if story_worlds else None,
            "characters": characters,
            "rights_ledger": rights,
            "series": series,
            "story_packages": packages
        }

    def create_ip(self, req: CreateIPRequest) -> Dict[str, Any]:
        # Validate rights split sum <= 100%
        if req.rights_splits:
            total_pct = sum(s.royalty_split_pct for s in req.rights_splits)
            if total_pct > 100.0:
                raise ValueError(f"Total royalty splits ({total_pct}%) exceed 100.0%")

        new_ip_id = f"ip_{uuid.uuid4().hex[:8]}"
        now_ts = datetime.now(timezone.utc).isoformat()

        ip_record = {
            "id": new_ip_id,
            "title": req.title,
            "franchise_code": req.franchise_code.upper(),
            "logline": req.logline,
            "synopsis": req.synopsis,
            "genre": req.genre,
            "primary_language": req.primary_language,
            "master_owner_id": req.master_owner_id,
            "global_valuation_usd": 0.0,
            "status": "active",
            "created_at": now_ts,
            "updated_at": now_ts
        }
        self.local_insert("digital_ips", ip_record)

        # Story World
        if req.story_world:
            sw_record = {
                "id": f"sw_{uuid.uuid4().hex[:8]}",
                "ip_id": new_ip_id,
                **req.story_world.model_dump(),
                "created_at": now_ts
            }
            self.local_insert("story_worlds", sw_record)

        # Characters
        if req.characters:
            for char in req.characters:
                char_record = {
                    "id": char.id or f"char_{uuid.uuid4().hex[:8]}",
                    "ip_id": new_ip_id,
                    **char.model_dump(exclude={"id"}),
                    "created_at": now_ts
                }
                self.local_insert("character_bibles", char_record)

        # Rights splits
        if req.rights_splits:
            for split in req.rights_splits:
                r_record = {
                    "id": f"rights_{uuid.uuid4().hex[:8]}",
                    "ip_id": new_ip_id,
                    **split.model_dump(),
                    "is_active": True,
                    "created_at": now_ts
                }
                self.local_insert("rights_ledger", r_record)

        return self.get_ip_detail(new_ip_id)

    def save_story_forge_package(self, req: StoryForgePackageCreateRequest) -> Dict[str, Any]:
        import hashlib
        import json

        pkg_id = f"sfp_{uuid.uuid4().hex[:8]}"
        now_ts = datetime.now(timezone.utc).isoformat()

        # Build canonical payload for deterministic cryptographic hashing (Amendment 2)
        canonical_dict = {
            "ip_id": req.ip_id,
            "creator_id": req.creator_id,
            "package_title": req.package_title,
            "story_world_id": req.story_world_id,
            "character_ids": sorted(req.character_ids or []),
            "episode_target": req.episode_target or 1,
            "version": req.version,
            "target_duration_seconds": req.target_duration_seconds,
            "beats": req.beats,
            "dialogues": req.dialogues,
            "cliffhanger_prompt": req.cliffhanger_prompt
        }
        canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(',', ':'))
        computed_hash = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

        pkg_record = {
            "id": pkg_id,
            "ip_id": req.ip_id,
            "creator_id": req.creator_id,
            "package_title": req.package_title,
            "story_world_id": req.story_world_id,
            "character_ids": req.character_ids or [],
            "episode_target": req.episode_target or 1,
            "version": req.version,
            "target_duration_seconds": req.target_duration_seconds,
            "beats_json": req.beats,
            "dialogues_json": req.dialogues,
            "cliffhanger_prompt": req.cliffhanger_prompt,
            "ai_model_used": req.ai_model_used,
            "human_approved": req.human_approved,
            "lineage_hash": computed_hash,
            "created_at": now_ts
        }
        self.local_insert("story_forge_packages", pkg_record)
        return pkg_record

ip_repository = IPRepository()
