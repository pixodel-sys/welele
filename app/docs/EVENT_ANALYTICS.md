# WELELE MEDIA™ — EVENT INGESTION & ANALYTICS TAXONOMY
**Document ID:** `WELELE-DOCS-EVT-001`  
**Core Purpose:** Track viewing drop-offs, cliffhanger conversion, coin velocity, and creator intelligence.

---

## 1. Platform Event Taxonomy

All platform events share the standard envelope:
```typescript
interface WeleleTelemetryEvent {
  event_name: string;
  user_id: string | null;
  session_id: string;
  story_id: string | null;
  episode_id: string | null;
  timestamp: string; // ISO-8601 UTC
  ip_region: 'ZA' | 'NG' | 'KE' | 'GHS' | 'OTHER';
  device: {
    form_factor: 'mobile' | 'desktop' | 'tablet';
    os: string;
    browser: string;
    connection_type: '5G' | '4G' | '3G' | 'WiFi';
  };
  metadata: Record<string, any>;
}
```

---

## 2. Canonical Event Catalog

### 2.1 Video Streaming & Retention Curve
- `episode_started`: Fires when first video frame decodes.
- `episode_25_percent`: Fires when playback reaches 25% of duration.
- `episode_50_percent`: Fires when playback reaches 50% of duration.
- `episode_completed`: Fires when playback reaches end of stream.
- `cliffhanger_reached`: Critical metric! Fires at the designated cliffhanger timestamp (e.g. second 68 of 80).

### 2.2 Monetization & Paywall Conversion
- `unlock_prompt_shown`: Fires when paywall/cliffhanger dialog appears.
- `unlock_attempted`: Fires when user taps Coin or Airtime unlock button.
- `unlock_completed`: Fires upon successful double-entry ledger debit and stream authorization.
- `coin_pack_viewed`: Fires when Coin Top-Up Modal is opened.
- `coin_purchase_success`: Fires when fiat payment is confirmed.
- `airtime_payment_success`: Fires when Vodacom/MTN carrier billing succeeds.

### 2.3 Community & Viral Engagement
- `comment_posted`: Viewer posted bullet or drawer comment.
- `reaction_sent`: Viewer triggered floating emoji reaction (🔥, ❤️, 👏, 😱).
- `series_followed`: User bookmarked or saved series to "My List".
- `episode_shared`: User generated WhatsApp / TikTok / Twitter share link.

### 2.4 Creator Lifecycle
- `creator_upload`: Master video uploaded to R2.
- `ai_subtitle_generated`: Timeline subtitles generated across local languages.
- `episode_published`: Creator launched episode live to the catalog.

---

## 3. Analytics Engine Consumers

```
                              EVENT BUS (/events/track)
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
RETENTION INTELLIGENCE          MONETIZATION FUNNELS            CREATOR SCORECARD
 - Episode drop-off heatmap       - Cliffhanger ➔ Unlock %       - Views & engagement
 - Churn prediction at paywall    - Airtime vs. Card share       - Coin earnings breakdown
 - Language preference share      - Revenue per active user      - Payout balance velocity
```
