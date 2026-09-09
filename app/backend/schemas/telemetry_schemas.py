"""
Welele Media™ — Audience Telemetry & Event Spine Schemas (Pydantic v2)
Standardized event envelope capturing viewing beacons, cliffhanger conversions, and device context.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class TelemetryEventPayload(BaseModel):
    event_name: str = Field(..., description="episode_started | heartbeat | cliffhanger_reached | unlock_attempted | unlock_completed | episode_completed")
    session_id: str
    user_id: Optional[str] = None
    ip_id: Optional[str] = None
    series_id: Optional[str] = None
    episode_id: Optional[str] = None
    playback_second: int = 0
    region_code: str = "ZA"
    device_type: str = "mobile_pwa"
    metadata: Dict[str, Any] = {}

class RetentionDataPoint(BaseModel):
    second: int
    retention_pct: float
    viewer_count: int
    is_cliffhanger: bool = False

class EpisodeRetentionResponse(BaseModel):
    series_id: str
    episode_id: str
    total_starts: int
    completion_rate_pct: float
    cliffhanger_conversion_pct: float
    avg_watch_time_seconds: float
    retention_curve: List[RetentionDataPoint]
    geo_distribution: List[Dict[str, Any]]
