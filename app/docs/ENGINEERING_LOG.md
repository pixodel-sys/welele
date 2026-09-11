# Welele Media™ Technical Reference & Engineering Log

This reference document consolidates all architecture decisions, bug investigations, root causes, and implementation fixes across the Welele platform.

---

## 1. Global Platform Brand Ident Architecture

### Architecture Model
The Welele Brand Ident is decoupled from individual episode masters. It is configured globally by the Welele Experience Engine (WEE) and executed seamlessly by the Welele Vertical Player before episode content:

```
                  WELELE PLATFORM (WEE)
                            │
               Brand Ident Configuration
              /videos/welele_ident.mp4
                            │
                            ▼
                  Viewer selects Episode
                            │
                            ▼
             ┌─────────────────────────────┐
             │    Welele Vertical Player   │
             └──────────────┬──────────────┘
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
      [STAGE 1: 0:00-0:05]          [PARALLEL PRELOAD]
    Play Welele Brand Ident       Preload & buffer episode
    (Unmuted Audio Context)       (Pre-buffered in background)
             │                             │
             └──────────────┬──────────────┘
                            ▼
                  [STAGE 2: 0:05.1+]
             Story Begins with Zero Latency
                  Episode Video Plays
```

### Key Components
- **Brand Ident Asset**: Stored at `/videos/welele_ident.mp4` and `/brand/welele-ident-v1.mp4`.
- **Service Worker Caching**: Service Worker (`sw.js`) aggressively caches the ident in `CacheStorage`.
- **Preload & Zero-Latency Switch**: While the 5-second brand ident is playing, the main episode video buffers invisibly in the background. When the ident completes, playback transitions immediately with no loading spinner.
- **Binge Intelligence**: Frequency capping prevents redundant ident replay during continuous episode watching sessions.

---

## 2. IndexedDB Persistent Local Media Store (`mediaStore.ts`)

### Purpose
Allows Creators and Admins to upload local video files (`.mp4`, etc.) and preview/play them across Creator Studio, Admin Moderation, and Viewer surfaces with persistence across browser reloads, without requiring cloud object storage credentials in local/dev environments.

### Core Mechanisms & Fixes

#### A. DOM File Serialization via `ArrayBuffer`
- **Issue**: Standard DOM `File` objects fail when directly stored in IndexedDB across certain browser contexts (`DataCloneError`).
- **Fix**: In `mediaStore.ts`, `File` objects are converted to pure binary `Blob` with `await file.arrayBuffer()` and stored with an explicit MIME type (`video/mp4`).

#### B. Ephemeral `blob:` URL Handling
- **Issue**: Session `blob:https://...` URLs expire upon browser reload. When backend payloads returned stale session URLs, HTML5 video failed with Error Code 4 (`MEDIA_ERR_SRC_NOT_SUPPORTED` / `Failed to open channel`).
- **Fix**: In `VerticalPlayer.tsx`, raw URLs starting with `blob:` are skipped and resolved from the persistent binary `Blob` in IndexedDB.

---

## 3. Episode Key Isolation & Cross-Contamination Resolution

### Problem 1: Uploaded Video Not Playing (Falling Back to Ident)
- **Cause**: IndexedDB cloning failed silently, leaving the database empty. The player fell back to the placeholder file (which was a copy of `welele_ident.mp4`).
- **Fix**: Binary serialization ensured files are safely written into IndexedDB and returned via dynamic `URL.createObjectURL(blob)`.

### Problem 2: Single Video Playing Across All Episodes and Titles
- **Cause**:
  1. `EpisodePipelineModal` initial state had `videoUrl = '/videos/welele_placeholder.mp4'`.
  2. When saving an uploaded file, the candidate key generator was saving the binary under the key `'/videos/welele_placeholder.mp4'`.
  3. Every default episode in the catalog had its `video_url` set to `'/videos/welele_placeholder.mp4'`.
  4. Opening *any* episode queried IndexedDB with `'/videos/welele_placeholder.mp4'`, retrieving the uploaded file (`Energy_pusle.mp4`) for all titles.
- **Fix**:
  1. **Automated Purge**: Added `purgeStaleKeys` on IndexedDB initialization to remove generic keys (`placeholder`, `ident`, `/videos/welele_placeholder.mp4`, un-scoped `energy_pusle`, etc.).
  2. **Strict Key Scoping**: Keys are strictly generated with series ID and episode numbers:
     - `video_story_${seriesId}_${episodeNumber}`
     - `video_${seriesId}_${episodeNumber}`
     - `video_${episodeId}`
  3. **Distinct Catalog Media**: Updated `mockData.ts` and `series_repository.py` to assign unique, distinct video files (`ocean_waves.mp4`, `sample_drama.mp4`, `flower_bloom.mp4`, `jellyfish.mp4`, `sintel.mp4`, `big_buck.mp4`) across all default episodes.

---

## 4. UI / Drawer Z-Index & Header Overlap Fix

- **Issue**: The episode selector sidebar close button (`X`) was inaccessible beneath the sticky header.
- **Fix**: Elevated episode drawer `z-index` to `z-50` and added top padding matching the header height (`pt-16`) to ensure close triggers and headers remain fully accessible on desktop and mobile.

---

## 5. Repository Hygiene

- **Documentation & Docs Policy**: Added `/documentation` and `/docs` to `.gitignore` and removed from git tracking to maintain a clean codebase for production deployment.
- **Live Branch**: All fixes verified and pushed to `origin/main` on GitHub (`pixodel-sys/welele`).

---

## 6. Verification Summary

| Check | Result | Details |
|---|---|---|
| **TypeScript & Build** | ✅ Passed | `npm run build` compiled 0 errors, 1944 modules transformed |
| **Backend Tests** | ✅ Passed | 20 / 20 tests passing (including `test_playback_authorisation_lineage.py`) |
| **Key Scoping** | ✅ Isolated | Blood Ties Ep 4 plays `Energy_pusle.mp4`, Ep 1-3 play catalog media, other titles remain isolated |
| **Ident Sequencing** | ✅ Verified | 5s brand ident seamlessly transitions to episode stream |

---

## 7. Canonical Playback-Authorisation Pipeline & Media Resolution Contract (FROZEN)

### Status: Canonical Architecture Locked & Frozen

### The 5 Architectural Laws of Playback
1. **Production Playback Authority**:
   - `GET /episodes/{seriesId}/{episodeId}?user_id={userId}` (`episodesApi.getStream`) is the sole authority for playback.
   - **No silent IndexedDB fallback** in production.
   - **No placeholder substitution** when the canonical stream fails.
   - Surface a structured, meaningful playback error instead.
2. **Local Development Isolation**:
   - IndexedDB is strictly reserved for explicit local/dev drafts and `blob:` media (`resolutionMode: 'LOCAL_DEV'`).
   - It must never masquerade as production media authority.
3. **Multi-Protocol Stream Delivery**:
   - HLS via `hls.js` across Chrome, Firefox, Edge, and Android.
   - Native HLS on Safari / iOS via `video.canPlayType('application/vnd.apple.mpegurl')`.
   - Direct MP4 / CDN stream where explicitly returned by the backend.
4. **Immutable Lineage Integrity**:
   - Strict preservation of the supply chain:
     `Creator Upload ➔ media_assets Record ➔ Episode Entity ➔ Entitlement Ledger ➔ Authorised Stream ➔ Exact Uploaded Master ➔ Video Element`.
5. **Operational Diagnostics**:
   - Structured console diagnostics remain active for real-time observability:
     `episodeId`, `seriesId`, `isUnlocked`, `returnedStreamUrl`, `mediaAssetId`, `storageKey`, `resolutionMode`, `streamType`, `mediaSource`, `decisionReason`.

---

## 8. Canonical Ingestion Contract & Storage Object Invariance

### Architectural Invariant
Browser `blob:` references are ephemeral in-memory pointers, not storage objects. A browser `blob:` URL must never be persisted as a canonical master or converted into a manufactured CDN URL. The authoritative ingestion supply chain is frozen as:

```
Browser File ➔ Binary Upload (POST /api/storage/upload-binary)
             ➔ R2 / Local Object Storage (Physical Bytes Persistence)
             ➔ storage_key (e.g. masters/{series_id}/ep_{number}_{hash}.mp4)
             ➔ media_assets (Attached via DAL)
             ➔ GET /episodes/{seriesId}/{episodeId} (Authoritative getStream)
             ➔ Authorised CDN / Media Stream
             ➔ <video> (Exact Physical Bytes Delivered)
```

### Ingestion Contract Enforcement
1. **Physical Binary Ingestion**: `POST /api/v1/storage/upload-binary` accepts multipart video bytes, writes them to Cloudflare R2 or persistent local storage (`backend/media_storage/`), and returns a verified `storage_key`.
2. **Strict Ingestion Validation**: `POST /api/v1/creators/episodes/add` explicitly rejects ephemeral `blob:` URLs with HTTP 400 Bad Request if no physical storage object exists.
3. **Storage Lineage Verification**: `StorageService.get_stored_binary(storage_key)` guarantees exact byte retrieval for integrity checks and media streaming.
4. **Authoritative Playback**: `VerticalPlayer` enforces `episodesApi.getStream()` as authoritative in production, strictly rejecting `blob:` hijacking and IndexedDB overrides.

---

## 9. Verification & Acceptance Gates

```
[Level 1: Type & Syntax]     ──► tsc && vite build: 0 errors (1944 modules transformed)  ✅ PASSED
[Level 2: Unit & Ledger]     ──► pytest: 20/20 backend tests passing                     ✅ PASSED
[Level 3: Lineage Contract]  ──► test_playback_authorisation_lineage.py: PASSED          ✅ PASSED
[Level 4: Byte Exactness]    ──► Uploaded Bytes == Streamed Bytes (100% Bit-for-Bit)      ✅ PASSED
```

> [!IMPORTANT]
> **Production Status:** The canonical ingestion and playback boundary is fully sealed and verified across both backend DAL and frontend player. Ephemeral blob URLs can neither enter the database nor hijack the production playback pipeline.

