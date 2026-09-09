# WELELE MEDIA™ — VIDEO TRANSCODING & CDN STREAMING PIPELINE
**Document ID:** `WELELE-DOCS-VID-001`  
**Governing Standard:** Adaptive Bitrate HLS (RFC 8216) + Cloudflare R2 ($0 Egress)

---

## 1. End-to-End Ingestion & Playback Lifecycle

```
 ┌──────────────┐      Direct Upload        ┌──────────────────┐
 │ CREATOR APP  │──────────────────────────►│  CLOUDFLARE R2    │
 │ (Workstation)│  (Pre-signed S3 Multipart)│  (Master Bucket) │
 └──────────────┘                           └────────┬─────────┘
                                                     │ S3 Webhook
                                                     ▼
                                            ┌──────────────────┐
                                            │ ASYNC TRANSCODER │
                                            │ (FFmpeg Engine)  │
                                            └────────┬─────────┘
                                                     │
                                                     ▼
                                            ┌──────────────────┐
                                            │ HLS LADDER GEN   │
                                            │ (1080/720/480p)  │
                                            └────────┬─────────┘
                                                     │
                                                     ▼
 ┌──────────────┐        Edge Streaming     ┌──────────────────┐
 │ 9:16 VIEWER  │◄──────────────────────────│  CLOUDFLARE CDN  │
 │ (Mobile PWA) │   (Zero-Egress Bandwidth) │ (African POPs)   │
 └──────────────┘                           └──────────────────┘
```

---

## 2. Canonical 9:16 Adaptive Bitrate (ABR) Ladder

Every master vertical video uploaded to Welele Media is encoded into 4 distinct rendition profiles optimized for varying mobile connection quality (from high-speed fiber in Sandton to congested 3G in rural KwaZulu-Natal):

| Rendition | Resolution (9:16) | Video Bitrate | Audio Bitrate | Target Frame Rate | Segment Length | Target Use Case |
|---|---|---|---|---|---|---|
| **1080p Ultra** | $1080 \times 1920$ | $4,500\text{ kbps}$ | $192\text{ kbps}$ | $30\text{ fps}$ | $2.0\text{s}$ | 5G & Fast Wi-Fi |
| **720p HD** | $720 \times 1280$ | $2,200\text{ kbps}$ | $128\text{ kbps}$ | $30\text{ fps}$ | $2.0\text{s}$ | 4G LTE Standard |
| **480p Data Saver** | $480 \times 854$ | $900\text{ kbps}$ | $96\text{ kbps}$ | $30\text{ fps}$ | $2.0\text{s}$ | **Default Pan-African 3G** |
| **360p Low** | $360 \times 640$ | $450\text{ kbps}$ | $64\text{ kbps}$ | $24\text{ fps}$ | $2.0\text{s}$ | Rural / Spotty 2G/3G |

---

## 3. Storage Hierarchy on Cloudflare R2

```
r2://welele-media-production/
├── masters/
│   └── stories/{story_id}/episodes/{ep_num}/master.mp4
│
├── hls/
│   └── stories/{story_id}/episodes/{ep_num}/
│       ├── master.m3u8          (Root Adaptive Bitrate Playlist)
│       ├── 1080p/
│       │   ├── playlist.m3u8
│       │   ├── segment_000.ts
│       │   └── segment_001.ts
│       ├── 720p/...
│       ├── 480p/...
│       └── 360p/...
│
└── posters/
    ├── stories/{story_id}/hero_banner.jpg
    └── stories/{story_id}/vertical_poster.jpg
```

---

## 4. Chunked Buffer Preloading (Zero-Latency Next Episode)

To achieve instantaneous swipe-to-next playback:
1. While Episode $N$ is playing, the frontend player silently requests the first 2 segments (`segment_000.ts`, `segment_001.ts`) of Episode $N+1$.
2. When the user swipes or triggers auto-advance, playback starts with **$<150\text{ms}$ time-to-first-frame (TTFF)**.
