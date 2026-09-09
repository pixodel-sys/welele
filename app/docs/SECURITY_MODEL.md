# WELELE MEDIA™ — SECURITY, AUTHENTICATION & DRM MODEL
**Document ID:** `WELELE-DOCS-SEC-001`  
**Core Objective:** Protect creator intellectual property, guarantee financial ledger integrity, and enforce granular role-based access.

---

## 1. Authentication & Role-Based Access Control (RBAC)

### 1.1 User Roles
1. **Viewer (`ROLE_VIEWER`)**:
   - Access: 9:16 vertical feed, free episodes, unlocked episode streams, bullet comments, wallet balance.
2. **Creator (`ROLE_CREATOR`)**:
   - Access: Viewer permissions + Creator Studio, master uploads, AI subtitle editor, creator earnings ledger.
3. **Admin (`ROLE_ADMIN`)**:
   - Access: Moderation queues, KYC audits, double-entry financial reconciliation, carrier billing telemetry.

### 1.2 JWT Token Payload
```json
{
  "sub": "b35c4dae-4663-5d1a-90da-4bfff4bfa570",
  "phone": "0828912345",
  "role": "ROLE_VIEWER",
  "region": "ZA",
  "iat": 1788796800,
  "exp": 1789401600
}
```

---

## 2. Media DRM & Anti-Screen-Capture System

To protect creators from content scraping, piracy, and screen recording:

```
                            CONTENT PROTECTION MATRIX
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
CONTEXT & SAVE DEFENSE          SCREEN CAPTURE TRAPS            FORENSIC WATERMARKING
 - Right-click disabled          - PrintScreen intercept         - Drifting User ID
 - Video controlsList="nodownload" - Clipboard sanitization        - Episode ID stamp
 - Transparent gesture shield    - Anti-Print CSS block          - Time-coded trace
```

### 2.1 Video Player Lockdown
- Native download buttons disabled via `controlsList="nodownload noplaybackrate noremoteplayback"`.
- Picture-in-Picture and remote playback disabled (`disablePictureInPicture={true}`).
- Transparent gesture shield placed above `<video>` to prevent direct DOM context inspection.

### 2.2 Screen Recording Interception
- `navigator.mediaDevices.getDisplayMedia` is trapped and rejected with a DRM security warning.
- `PrintScreen`, `F12`, `Ctrl+S`, `Cmd+Shift+3/4/5` triggers automatic clipboard clearing and security alert banners.

### 2.3 Dynamic Forensic Watermark
- A semi-transparent watermark (`🔒 WELELE DRM • [USER_ID] • [EPISODE_ID]`) drifts continuously across the viewport, deterring external physical recording and making leaks traceable.

---

## 3. Storage Key Signing & Expiring URLs

- Master raw files in Cloudflare R2 are **never public**.
- Transcoded HLS playlists and segments require short-lived HMAC-signed tokens (`?token=...&exp=...`) issued only upon valid double-entry unlock verification.
