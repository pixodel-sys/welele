# WEE — Welele Experience Engine™

## 1. Architectural Philosophy

> **The Golden Rule of Welele Architecture**:  
> *The Content Catalog stores what exists. The Experience Engine controls how, where, when, and to whom it is merchandised.*  
> The Frontend is a **Surface Renderer**; the CMS is the **Control Plane**.

An administrator or content manager can rearrange hero bill-boards, modify copy headlines, schedule promotional banners, feature new African creators, and alter row order without requesting engineering changes or deploying code.

---

## 2. The 5 Layers of WEE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. WELELE ADMIN STUDIO  (Control Workspace)                                │
│   • Visual Slot Merchandiser • Drag-and-Drop Order • Time-Travel Simulator  │
│   • Multi-device Bezel Preview (9:16 Mobile PWA / 16:9 Desktop Web)         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Publishes / Edits Layouts
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. EXPERIENCE ENGINE  (Backend Logic & Hydration)                           │
│   • Editorial Rule Evaluator • Hybrid Slot Ingestion (Manual + Algo)        │
│   • Time-Window Gatekeeper [start_at / end_at] • Badge & Copy Resolvers     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Resolves & Caches
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. EXPERIENCE API  (High-Performance Edge Delivery Layer)                  │
│   • GET /api/v1/experience/page/{page_id}                                   │
│   • GET /api/v1/experience/preview/{page_id}?simulated_time={iso_date}      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Streams Immutable JSON Payload
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. EXPERIENCE MANIFEST  (Strict Typings & System Contract)                 │
│   • Defines: Page ➔ Sections ➔ Slots ➔ Content ➔ Presentation Overrides    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Parsed & Rendered Declaratively
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. SURFACE RENDERER  (Universal Client View Layer)                          │
│   • Mobile PWA (9:16 portrait first) • Desktop Web • Smart TV • Native App  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Registry

| Component Type | Purpose | Key Attributes & Overrides |
| :--- | :--- | :--- |
| **`HERO_CAROUSEL`** | High-impact top billboard with Ken Burns rotation | Auto-play interval, headline override, subheadline override, badge, trailer video URL, desktop vs mobile 9:16 artwork. |
| **`HORIZONTAL_ROW`** | Standard Netflix/TikTok style swiper row | Rank numbers (Top 10 style), card size, slot list, hybrid algo fallback. |
| **`EDITORIAL_BANNER`** | Merchandising & payment prompts | Airtime/MTN/Vodacom top-up CTA, flash drops, festival discounts. |
| **`EDITORIAL_SPOTLIGHT`** | 16:9 cinematic feature card | Rich synopsis, creator avatar, verified director tag, primary CTA. |
| **`POSTER_GRID`** | Multi-column responsive catalog grid | 2 to 6 columns, category filter pills, infinite scroll. |
| **`COMING_SOON_RADAR`** | Pre-release hype radar | Countdown timer, release day indicator, interactive "Remind Me" bell. |

---

## 4. Slot Ingestion Modes

Each section supports three ingestion modes:
1. **`manual`**: Exact list of curated content slots with explicit sequence.
2. **`algorithmic`**: System dynamically sorts and populates items based on metrics (`velocity_24h`, `completion_rate`, `trending`, `new_releases`).
3. **`hybrid`**: Pinned items occupy positions #1..#N, while subsequent positions are filled algorithmically.

---

## 5. Publishing & Time-Travel Workflow

```
[ DRAFT ] ──(Edit & Rearrange)──► [ DEVICE PREVIEW ] ──(Approve)──► [ PUBLISHED / SCHEDULED ]
```

- **Draft State**: Safe sandbox where Content Managers stage layout and copy changes.
- **Simulated Preview**: The Admin Studio allows selecting any past or future timestamp (e.g. `2026-09-18T18:00:00Z`) to test time-gated promotional campaigns.
- **Publish to LIVE**: Atomically generates an immutable version tag (e.g., `2026.09.08.v171`) and deploys to all surface renderers instantly.

---

## 6. Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/experience/pages` | Lists all managed experience pages (`home`, `discover`). |
| `GET` | `/api/experience/page/{page_id}` | Public layout delivery for client surface renderers. |
| `GET` | `/api/experience/preview/{page_id}` | Admin preview with draft state and simulated time-travel. |
| `PUT` | `/api/experience/page/{page_id}/draft` | Saves working layout draft in Admin Studio. |
| `POST` | `/api/experience/page/{page_id}/publish` | Promotes draft layout to LIVE production status. |
| `POST` | `/api/experience/page/{page_id}/reset-default`| Resets page back to canonical platform preset. |
