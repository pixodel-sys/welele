# Welele™ Full-Stack Application Implementation Plan (React + Python FastAPI)

## Executive Overview
**Welele™** (*"Stories That Move You"*) is a mobile-first African storytelling and microdrama entertainment platform. This implementation plan integrates a full-stack architecture combining a **React + TypeScript** frontend (PWA, 8:16 vertical video player, Creator Hub™, Admin Console) with a **Python (FastAPI)** backend powering the APIs, **Welele AI™ media processing pipeline**, African language translation/subtitling, and Mobile Money payment rails.

---

## User Review Required

> [!IMPORTANT]
> **Full-Stack Architecture**:
> - **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons + PWA.
> - **Backend (Python)**: Python 3.14 + FastAPI + Uvicorn + Pydantic + SQLite/SQLAlchemy + AI/Media processing modules.
> - **AI & Media Services (Python)**: Automated vertical format validation, African language subtitle & translation engine, AI cliffhanger detection, and automated safety moderation.
> - **Monetization Engine**: Welele Coins, microdrama episode paywall, animated creator gifting, and African Mobile Money rails (M-Pesa, MTN MoMo, Airtel Money, Paystack).

---

## Full-Stack Architecture & Directory Structure

```
g:/App_Development/App_Dev/Welele Media/app/
├── backend/                               # Python FastAPI Backend
│   ├── main.py                            # FastAPI app entry point with CORS, routers & startup events
│   ├── requirements.txt                   # Python dependencies (fastapi, uvicorn, pydantic, sqlalchemy, etc.)
│   ├── config.py                          # Environment & app configurations
│   ├── database.py                        # Database connection & session setup (SQLite / SQLAlchemy)
│   ├── models/                            # Database models
│   │   ├── user.py                        # User, Creator & Admin entity models
│   │   ├── story.py                       # Series, Episode, Genre & Language models
│   │   ├── monetization.py                # Wallet, CoinTransaction, Gift, and Payout models
│   │   └── chat.py                        # StoryChat & Reaction models
│   ├── schemas/                           # Pydantic schemas for request/response validation
│   │   ├── story_schemas.py
│   │   ├── creator_schemas.py
│   │   ├── monetization_schemas.py
│   │   └── ai_schemas.py
│   ├── routers/                           # API route handlers
│   │   ├── stories.py                     # Feed, trending, search, genres & episode details
│   │   ├── creators.py                    # Creator profile, series upload, dashboard stats
│   │   ├── monetization.py                # Coin packs, episode unlocking, virtual gifting, MoMo webhooks
│   │   ├── chat.py                        # Episode chat & live timestamped reactions
│   │   ├── ai.py                          # Welele AI™: subtitles, translations, video analyzer
│   │   └── admin.py                       # Moderation queue, creator KYC & platform analytics
│   ├── services/                          # Business logic & AI processing
│   │   ├── ai_service.py                  # AI African language translation & subtitling generator
│   │   ├── media_service.py               # Video metadata, aspect ratio check & cliffhanger analysis
│   │   ├── payment_service.py             # Mobile Money integration simulator (M-Pesa, MoMo, Paystack)
│   │   └── recommendation_service.py      # Personalized feed ranking algorithm
│   └── seed_data.py                       # Seed script with rich African microdrama series & creator data
│
├── frontend/                              # React + TypeScript Frontend (PWA)
│   ├── index.html                         # PWA shell, viewport config, Plus Jakarta Sans
│   ├── package.json                       # React, Vite, Lucide, Tailwind, Axios
│   ├── vite.config.ts                     # Vite configuration with API proxy to Python backend
│   ├── tailwind.config.js                 # Welele brand color palette & tokens
│   ├── src/
│   │   ├── main.tsx                       # React application bootstrap
│   │   ├── App.tsx                        # Mode switcher & dynamic view routing
│   │   ├── index.css                      # Custom styling, dark mode tokens, animations
│   │   ├── types/                         # TypeScript interfaces synced with backend schemas
│   │   ├── services/                      # Axios API clients connecting to Python backend
│   │   │   ├── api.ts                     # Base Axios instance
│   │   │   ├── storyService.ts            # Stories & Episodes API
│   │   │   ├── monetizationService.ts     # Coins, unlocks, gifting API
│   │   │   ├── chatService.ts             # Chat & floating reactions API
│   │   │   └── aiService.ts               # Subtitles & AI suggestions API
│   │   ├── context/
│   │   │   ├── AppContext.tsx             # Global state (user, wallet, watch history, mode)
│   │   │   └── ChatContext.tsx            # Live chat room state
│   │   └── components/
│   │       ├── common/
│   │       │   ├── Header.tsx             # Brand header with coin pill & mode switcher
│   │       │   ├── BottomNav.tsx          # Mobile navigation (Home, Discover, Create, Chat, Profile)
│   │       │   ├── CoinModal.tsx          # Welele Coins top-up modal with MoMo/M-Pesa simulation
│   │       │   └── GiftModal.tsx          # Animated virtual gifts (Flames, Crown, Drum, Clap)
│   │       ├── viewer/
│   │       │   ├── VerticalPlayer.tsx     # 8:16 vertical microdrama video player
│   │       │   ├── FloatingReactions.tsx  # Live animated reaction bursts over player
│   │       │   ├── EpisodeDrawer.tsx      # Episode list with lock/unlock status & paywall triggers
│   │       │   ├── HomeScreen.tsx         # Personalized feed & trending carousel
│   │       │   ├── DiscoverScreen.tsx     # Genre & African language filters (Yoruba, Swahili, Zulu, Pidgin)
│   │       │   ├── StoryDetailModal.tsx   # Series info, cast, trailer & episode list
│   │       │   ├── WeleleChatScreen.tsx   # Episode community chat
│   │       │   └── ProfileScreen.tsx      # User wallet, history, language preference
│   │       ├── creator/
│   │       │   ├── CreatorDashboard.tsx   # Revenue, views, cliffhanger retention stats
│   │       │   ├── SeriesManager.tsx      # Series creation & episode pricing
│   │       │   ├── EpisodeUploader.tsx    # Upload with AI subtitle generation & cliffhanger tool
│   │       │   └── CreatorEarnings.tsx    # MoMo/Bank payout request dashboard
│   │       └── admin/
│   │           ├── AdminDashboard.tsx     # System analytics, revenue velocity
│   │           ├── ModerationQueue.tsx    # Video review with AI safety insights
│   │           └── CreatorVerification.tsx # Creator KYC & verification approvals
│
└── README.md                              # Setup, running instructions, and architecture guide
```

---

## Detailed Component & Python Service Specs

### 1. Python FastAPI Backend (`backend/`)
- **FastAPI Endpoints**:
  - `GET /api/stories/feed` & `GET /api/stories/trending`: Dynamic ranking powered by `recommendation_service.py`.
  - `POST /api/stories/unlock`: Deducts user coins, unlocks episode, credits creator wallet.
  - `POST /api/monetization/topup`: Simulates Mobile Money (M-Pesa, MTN MoMo, Airtel Money, Paystack) coin purchases.
  - `POST /api/monetization/gift`: Triggers animated gift, sends notification, updates creator revenue.
  - `POST /api/ai/subtitles`: Welele AI™ service generating automated captions and multi-language translations (English, Swahili, Yoruba, Zulu, Amharic, Pidgin, French).
  - `POST /api/ai/analyze-video`: Validates 8:16 / 9:16 vertical format, detects cliffhanger timestamp, and performs safety screening.
  - `GET /api/creators/dashboard`: Live stats for creator revenue, retention, and viewer engagement.

### 2. Welele Design System & Brand Palette
- **Dark Canvas Surfaces**: `#050507` (Black), `#0D0D12` (Surface), `#15151B` (Surface 2)
- **Brand Accents & Gradients**: `#FF9D00` (Orange), `#FFC400` (Gold), `#FF3B30` (Red), `#F50072` (Pink), `#E800A8` (Magenta), `#39D353` (Success), `#F7F4EE` (White)
- **Typography**: Plus Jakarta Sans with Cinzel / Barlow Condensed cinematic accents.

### 3. Viewer Microdrama Experience (`frontend/`)
- **Vertical Player**: Gesture-driven 8:16 / 9:16 player with smooth swipe transitions between episodes.
- **Cliffhanger Unlocking**: Free episodes 1–3, with instant coin unlock for subsequent episodes.
- **Floating Community Reactions & Chat**: Real-time bursts (🔥, 👑, 😱, 👏) floating over the screen and episode-specific discussion rooms.

### 4. Creator Hub™ & Admin Console
- **Creator Studio**: Upload new episodes, run Welele AI™ subtitle generator, set cliffhanger timestamps, request MoMo payouts.
- **Admin Platform**: AI-assisted content moderation, creator approvals, revenue metrics.

---

## Verification Plan

### Automated Tests & Checks
- **Python Backend**: Run FastAPI health checks and test seed data initialization.
- **Frontend**: Run TypeScript compilation (`tsc --noEmit`) and build checks.
- **Integration**: Verify API endpoints communicate seamlessly between React and FastAPI via Vite proxy.

### Manual End-to-End Verification
1. **Viewer Flow**: Browse feed, watch vertical episodes, send live floating reactions, unlock gated cliffhanger with Welele Coins, top up coins with simulated MoMo.
2. **Creator Flow**: Upload new episode, generate AI subtitles, view real-time earnings, request payout.
3. **Admin Flow**: Review pending uploads in moderation queue, approve verified creators.
4. **Responsive Verification**: Test across mobile view (8:16 vertical emulation) and desktop dashboards.
