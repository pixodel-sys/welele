"""
Welele Media™ — Versioned Intelligence Evidence & Recommendation Engine (P2)
Persists immutable diagnostic evidence and narrative recommendations for Story Forge with confidence gating.
"""

import os
import sys
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.base_repository import BaseRepository
from services.analytics_service import analytics_service

class IntelligenceService(BaseRepository):
    MIN_SAMPLE_SIZE_THRESHOLD = 5
    MIN_CONFIDENCE_THRESHOLD = 0.70

    def generate_episode_diagnostic_evidence(
        self,
        ip_id: str,
        series_id: str,
        episode_id: str
    ) -> Dict[str, Any]:
        """
        Creates an immutable, versioned evidence artifact from analyzed retention signals.
        """
        analytics = analytics_service.analyze_episode_performance(series_id, episode_id)
        now_ts = datetime.now(timezone.utc).isoformat()
        evidence_id = f"evid_{uuid.uuid4().hex[:10]}"

        drops = analytics.get("detected_drops", [])
        narrative_drops = [d for d in drops if d["classification"] == "CONFIRMED_NARRATIVE_DROP"]

        evidence_artifact = {
            "id": evidence_id,
            "ip_id": ip_id,
            "series_id": series_id,
            "episode_id": episode_id,
            "analysis_version": "v2.1-evidence",
            "sample_size": analytics["total_views"],
            "cliffhanger_conversion_pct": analytics["cliffhanger_conversion_pct"],
            "technical_health": analytics["technical_health"],
            "narrative_drops_detected": len(narrative_drops),
            "diagnostics": drops,
            "created_at": now_ts
        }
        self.local_insert("intelligence_evidence", evidence_artifact)

        # Generate recommendation if confidence threshold met (Amendment 4)
        rec = None
        if analytics["total_views"] >= self.MIN_SAMPLE_SIZE_THRESHOLD and narrative_drops:
            primary_drop = narrative_drops[0]
            confidence = primary_drop["confidence_score"]

            if confidence >= self.MIN_CONFIDENCE_THRESHOLD:
                rec_id = f"rec_{uuid.uuid4().hex[:10]}"
                rec = {
                    "id": rec_id,
                    "evidence_id": evidence_id,
                    "ip_id": ip_id,
                    "series_id": series_id,
                    "episode_id": episode_id,
                    "metric": "RETENTION_DROP_PACING",
                    "time_range": primary_drop["time_range"],
                    "cohort": "ALL_VIEWERS_ZA",
                    "sample_size": analytics["total_views"],
                    "confidence": confidence,
                    "analysis_version": "v2.1-evidence",
                    "model_version": "gemini-1.5-flash-intelligence",
                    "prescription_text": (
                        f"Evidence confirms a {primary_drop['drop_percentage']}% audience drop at {primary_drop['time_range']}. "
                        f"For upcoming episodes, introduce a high-stakes dialogue revelation or secret conflict before second {primary_drop['start_second']}."
                    ),
                    "is_actionable": True,
                    "created_at": now_ts
                }
                self.local_insert("intelligence_recommendations", rec)

        return {
            "evidence": evidence_artifact,
            "recommendation": rec
        }

    def get_recommendations_for_series(self, series_id: str) -> List[Dict[str, Any]]:
        all_recs = self.local_get("intelligence_recommendations")
        return [r for r in all_recs if r.get("series_id") == series_id and r.get("confidence", 0) >= self.MIN_CONFIDENCE_THRESHOLD]

    def get_story_forge_context(self, series_id: str) -> Dict[str, Any]:
        """
        Returns latest active recommendations formatted as contextual advice for Story Forge prompts.
        """
        recs = self.get_recommendations_for_series(series_id)
        if not recs:
            return {
                "has_recommendations": False,
                "prompt_directive": "Maintain high-tension 60-90 second pacing with cliffhanger hook."
            }

        latest = recs[-1]
        return {
            "has_recommendations": True,
            "recommendation_id": latest["id"],
            "evidence_id": latest["evidence_id"],
            "confidence": latest["confidence"],
            "sample_size": latest["sample_size"],
            "prompt_directive": latest["prescription_text"]
        }

intelligence_service = IntelligenceService()
