# WELELE MEDIA™ — REST API CONTRACT SPECIFICATION
**Document ID:** `WELELE-DOCS-API-001`  
**Base URL:** `/api`  
**Protocol:** HTTPS / JSON / WebSockets (for Live Bullet Chat)  
**Standard Response Envelope:**
```json
{
  "success": true,
  "data": {},
  "message": "Operation executed successfully",
  "timestamp": "2026-09-07T16:00:00Z"
}
```

---

## 1. Authentication & Identity Domain (`/auth`)

### `POST /auth/phone/send-otp`
Initiates mobile SMS/WhatsApp OTP authentication across Pan-African carrier networks.
- **Request Body**:
  ```json
  {
    "phone_number": "0828912345",
    "region_code": "ZA"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "success": true,
    "otp_sent": true,
    "expires_in_seconds": 300,
    "carrier_detected": "vodacom_airtime"
  }
  ```

### `POST /auth/phone/verify-otp`
Validates 6-digit OTP and issues signed JWT session.
- **Request Body**:
  ```json
  {
    "phone_number": "0828912345",
    "otp_code": "492018"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "user_id": "b35c4dae-4663-5d1a-90da-4bfff4bfa570",
    "token": "eyJhbGciOiJIUzI1NiIsIn...",
    "display_name": "Sipho Dlamini",
    "coin_balance": 150
  }
  ```

---

## 2. Content & Series Domain (`/series`)

### `GET /series/feed`
Retrieves curated vertical feeds (Spotlight Original, Trending Now, New Releases).
- **Query Params**: `genre` (optional), `language` (optional), `page` (int, default=1), `limit` (int, default=20)
- **Response `200 OK`**:
  ```json
  {
    "series": [
      {
        "id": "c3e9302a-9809-51c2-b219-4e2a3079787f",
        "title": "Blood Ties",
        "tagline": "Two powerful families tied by blood, torn apart by greed.",
        "cover_image": "/banners/blood_ties_banner.jpg",
        "vertical_poster": "/posters/blood_ties.jpg",
        "genre": "Drama • Family • Betrayal",
        "rating": 4.98,
        "total_episodes": 12,
        "free_episodes_count": 3
      }
    ],
    "total": 8
  }
  ```

### `GET /series/{series_id}`
Returns full series details including episode listings and cliffhanger timestamps.

---

## 3. Streaming & Episode Domain (`/episodes`)

### `GET /episodes/{series_id}/{episode_id}`
Fetches playback stream parameters with adaptive HLS playlist links and DRM tokens.
- **Response `200 OK`**:
  ```json
  {
    "episode_id": "ep_bt_1",
    "title": "The Golden Will",
    "episode_number": 1,
    "is_unlocked": true,
    "hls_manifest_url": "https://cdn.welele.media/hls/stories/blood_ties/ep1/master.m3u8",
    "renditions": {
      "1080p": "https://cdn.welele.media/hls/stories/blood_ties/ep1/1080p.m3u8",
      "720p": "https://cdn.welele.media/hls/stories/blood_ties/ep1/720p.m3u8",
      "480p_data_saver": "https://cdn.welele.media/hls/stories/blood_ties/ep1/480p.m3u8"
    },
    "cliffhanger_time": 68,
    "cliffhanger_hook": "Who authorized her DNA test before the funeral?"
  }
  ```

### `POST /episodes/{series_id}/{episode_id}/unlock`
Unlocks episode using Coins or Airtime deduction.
- **Request Body**:
  ```json
  {
    "user_id": "b35c4dae-4663-5d1a-90da-4bfff4bfa570",
    "payment_method": "COINS",
    "coins_cost": 5
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "success": true,
    "remaining_coins": 145,
    "unlocked_episode_id": "ep_bt_4",
    "playback_token": "ptk_991823a01f..."
  }
  ```

---

## 4. Wallet & Double-Entry Monetization Domain (`/wallet` & `/monetization`)

### `GET /wallet/balance`
Returns materialized coin balance and audit summary.
- **Query Params**: `user_id` (UUID)
- **Response `200 OK`**:
  ```json
  {
    "user_id": "b35c4dae-4663-5d1a-90da-4bfff4bfa570",
    "coin_balance": 150,
    "bonus_coins": 30,
    "lifetime_coins_purchased": 50,
    "lifetime_coins_spent": 15
  }
  ```

### `POST /monetization/airtime/charge`
Executes 1-tap direct operator billing (Vodacom / MTN / Telkom / Cell C).
- **Request Body**:
  ```json
  {
    "user_id": "b35c4dae-4663-5d1a-90da-4bfff4bfa570",
    "carrier_id": "vodacom_airtime",
    "phone_number": "0828912345",
    "charge_type": "episode_unlock",
    "target_id": "ep_bt_4",
    "amount_zar": 3.00,
    "coins_equivalent": 5
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "success": true,
    "transaction_id": "tx_vodacom_991024",
    "message": "Deducted R3.00 from Vodacom Airtime. Episode unlocked!"
  }
  ```

---

## 5. Telemetry & Analytics Ingestion Domain (`/events`)

### `POST /events/track`
Ingests streaming, engagement, and funnel telemetry.
- **Request Body**:
  ```json
  {
    "event_name": "cliffhanger_reached",
    "user_id": "b35c4dae-4663-5d1a-90da-4bfff4bfa570",
    "story_id": "c3e9302a-9809-51c2-b219-4e2a3079787f",
    "episode_id": "ep_bt_1",
    "metadata": {
      "playback_position_seconds": 68.4,
      "watch_duration_seconds": 68.4,
      "connection_type": "4G",
      "carrier": "Vodacom"
    }
  }
  ```
- **Response `202 Accepted`**:
  ```json
  {
    "received": true,
    "event_id": "evt_991280381"
  }
  ```
