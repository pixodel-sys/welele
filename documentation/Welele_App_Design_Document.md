# Welele™ Application Design & Product Architecture

**Parent Company:** Welele Media™  
**Company philosophy:** *It's about connection.*  
**Consumer platform:** Welele™  
**Consumer promise:** *Stories That Move You.*  
**Design reference:** 8:16 vertical mobile format, with responsive desktop creator/admin experiences  
**Implementation target:** React + TypeScript, PWA-first, native-ready

---

## 1. Product Vision

Welele™ is a mobile-first African storytelling and entertainment platform focused initially on microdrama and short-form episodic video.

The platform is built around **connection**:

- creator ↔ audience
- story ↔ viewer
- viewer ↔ viewer
- Africa ↔ the world
- creator ↔ opportunity
- story ↔ community

The strategic moat is not simply software. It is the combination of **content, creators, audience, community, data, production tools and monetisation**.

### Brand architecture

**Welele Media™**  
*It's about connection.*

Owns the media, technology, creator, advertising and production ecosystem.

**Welele™**  
*Stories That Move You.*

The consumer entertainment platform.

Future products can include:

- Welele Creator Hub™
- Welele Chat™
- Welele Originals™
- Welele Studios™
- Welele AI™
- Welele Ads™
- Welele Audio™
- Welele Live™

---

# 2. Brand Identity

## Approved logo usage

Use only the approved Welele logo supplied for the project.

Two official application variants:

1. **Standalone W/play symbol** — app icon, compact navigation, splash screens and constrained spaces.
2. **Full logo with white Welele wording** — brand headers, website, onboarding and large-format surfaces.

Do not recreate or substitute the logo with generated typography or alternate colours.

## Visual character

- cinematic
- premium
- warm
- modern
- energetic
- human
- African
- globally accessible

Avoid stereotypical African imagery such as generic safari, wildlife, tribal-mask or "tribal pattern" design. African identity should emerge through people, language, culture and authentic stories.

## Suggested design tokens

```css
--welele-black: #050507;
--welele-surface: #0D0D12;
--welele-surface-2: #15151B;
--welele-white: #F7F4EE;
--welele-muted: #A8A5A1;
--welele-orange: #FF9D00;
--welele-gold: #FFC400;
--welele-red: #FF3B30;
--welele-pink: #F50072;
--welele-magenta: #E800A8;
--welele-success: #39D353;
```

Primary UI font: **Plus Jakarta Sans**.

---

# 3. Mobile Design System

The viewer application is designed around an **8:16 vertical experience**, using 1080 × 2160 as a visual reference rather than a fixed pixel size.

It must respond gracefully to common mobile sizes such as:

- 360 × 720
- 390 × 844
- 393 × 852
- 412 × 915
- 430 × 932

Use CSS aspect-ratio, responsive units and safe-area insets rather than hard-coded screen dimensions.

### Mobile principle

The viewer should be:

- thumb-friendly
- one-handed
- video-first
- visually immersive
- fast on mobile networks
- low-friction

---

# 4. Viewer Navigation

Bottom navigation:

```text
┌──────────────────────────────────┐
│                                  │
│            APP CONTENT           │
│                                  │
├──────────────────────────────────┤
│ Home │ Discover │ + │ Chat │ Me │
└──────────────────────────────────┘
```

### Home
Personalised story feed.

### Discover
Search, genres, languages, collections and trending.

### Create
Viewer sees creator opportunity; creator sees upload/create tools.

### Chat
Story-centric community.

### Me
Profile, My List, history, subscription and settings.

---

# 5. Viewer Information Architecture

```text
Welele™
│
├── Home
│   ├── Featured Story
│   ├── Continue Watching
│   ├── Trending Now
│   ├── New Releases
│   ├── Welele Originals
│   ├── Because You Watched
│   └── Popular in Your Community
│
├── Discover
│   ├── Search
│   ├── Genres
│   ├── Languages
│   ├── Countries
│   ├── Collections
│   └── Trending
│
├── Watch
│   ├── Video Player
│   ├── Episode Info
│   ├── Next Episode
│   ├── Reactions
│   ├── Comments
│   ├── Chat
│   └── Share
│
├── My List
│   ├── Saved
│   ├── Downloads
│   ├── Continue Watching
│   └── History
│
├── Welele Chat
│   ├── Story Rooms
│   ├── Episode Rooms
│   ├── Fan Theories
│   └── Creator Q&A
│
└── Profile
    ├── Account
    ├── Subscription
    ├── Preferences
    ├── Language
    ├── Notifications
    └── Privacy
```

---

# 6. Home Screen

## Hero

Large cinematic featured story with:

- artwork
- title
- genre
- age rating
- season/episode information
- synopsis
- Play
- My List

Example:

**The CEO's Secret Wife**  
Romance · 1 Season

*A fake marriage. A hidden identity. A love that could ruin everything.*

Buttons:

**▶ Play**  
**+ My List**

## Continue Watching

Horizontal cards with:

- artwork
- title
- episode
- progress bar
- remaining time

## Trending Now

Numbered ranking:

1. Blood Ties
2. Broken Vows
3. The Hustlers
4. Campus Royals

---

# 7. Discover

Search across:

- titles
- creators
- actors
- genres
- languages
- keywords

Example search prompts:

> revenge  
> CEO  
> South African drama  
> short romance

Genres:

- Drama
- Romance
- Comedy
- Crime
- Thriller
- Family
- Mystery
- Action
- Inspirational
- Horror
- Youth
- African Stories

Architecture must allow new categories without code changes.

---

# 8. Story Detail

```text
[Hero Poster]

TITLE
Genre · Rating · Seasons

[ PLAY ] [ + MY LIST ]

Synopsis

Episodes
Season 1
E01
E02
E03
...

Cast & Creator

About This Story

💬 Join the Conversation

More Like This
```

---

# 9. Video Player

The player is the core product experience.

Controls:

- play/pause
- scrub
- volume
- fullscreen
- captions
- audio language
- playback speed
- skip intro
- next episode
- share
- report

Microdrama optimisation:

- vertical viewing
- rapid next-episode transition
- cliffhanger-friendly design
- autoplay where permitted
- adaptive streaming
- mobile data awareness

Use HLS or an equivalent adaptive streaming architecture.

---

# 10. Welele Chat™

Welele Chat is **not intended to be a generic messenger**.

It is a story-centric community layer.

Each series can have:

- series room
- episode room
- reactions
- fan theories
- creator Q&A
- behind-the-scenes discussion

Example:

> **THE CEO'S SECRET WIFE — Episode 28**  
> 🔥 3,421 people talking

> “NO WAYS! I knew she wasn't the real daughter!”

> “That slap deserved an award.”

> “Who's watching from Soweto?”

Core principle:

> **Watch together, even when you're apart.**

---

# 11. Reactions

Lightweight emotional reactions:

- ❤️ Love
- 😂 Funny
- 😱 Shocked
- 😭 Emotional
- 🔥 Fire
- 👀 Suspense

Reaction data becomes useful to creators and recommendation systems.

---

# 12. Creator Ecosystem

Creator lifecycle:

```text
Idea
 ↓
Development
 ↓
Production
 ↓
Upload
 ↓
Review
 ↓
Publish
 ↓
Audience
 ↓
Engagement
 ↓
Monetisation
 ↓
Analytics
 ↓
Growth
```

Welele should eventually provide creators with production tools, education, audience analytics, monetisation and collaboration.

---

# 13. Creator Hub

Desktop and tablet-friendly professional workspace.

Main navigation:

```text
Creator Hub
Dashboard
My Series
Episodes
Analytics
Audience
Engagement
Ads & Monetisation
Earn & Payouts
Comments
Messages
Resources
Settings
```

Dashboard KPIs:

- Total Views
- Watch Time
- Subscribers
- Revenue
- Engagement Rate
- Series Performance

Example:

```text
Total Views       1.24M
Watch Time        245.6K
Subscribers       18.6K
Revenue           R24.5K
Engagement        12.6%
```

---

# 14. Creator Levels

Optional progression:

- New Creator
- Rising Creator
- Bronze
- Silver
- Gold
- Platinum
- Featured Creator

XP can come from:

- publishing
- audience growth
- watch time
- engagement
- education
- community participation

Reward quality, not spam.

---

# 15. Series Management

```text
My Series
│
├── Series Information
├── Artwork
├── Trailer
├── Seasons
├── Episodes
├── Cast
├── Languages
├── Ratings
├── Publishing
├── Analytics
└── Monetisation
```

Episode object:

```text
episode_id
series_id
season
episode_number
title
description
video_asset
thumbnail
duration
language
captions
status
publication_date
age_rating
monetisation_status
ad_eligibility
```

Statuses:

- Draft
- Processing
- Review
- Approved
- Scheduled
- Published
- Unpublished
- Rejected

---

# 16. Content Moderation

```text
Upload
 ↓
Automated checks
 ↓
AI safety/content analysis
 ↓
Human review where necessary
 ↓
Approve / Reject / Request Changes
 ↓
Publish
```

Checks can include:

- copyright signals
- explicit content
- violence
- hate/abuse
- age suitability
- metadata
- thumbnail quality

AI should assist moderation; high-impact decisions should retain appropriate human oversight.

---

# 17. Ads & Monetisation

Creator-facing dashboard:

```text
Estimated Earnings     R24,580
Ad Impressions          2.45M
Ad Views                1.86M
eCPM                    R42.65
Fill Rate               94.7%
Monetised Playbacks     1.32M
```

Inventory:

- pre-roll
- mid-roll
- post-roll
- banner
- overlay
- sponsored story
- branded integration
- creator sponsorship

Microdrama should use short, carefully placed advertising.

---

# 18. Ad Tracking

Event chain:

```text
Ad Request
 ↓
Ad Served
 ↓
Impression
 ↓
View
 ↓
25%
 ↓
50%
 ↓
75%
 ↓
100%
 ↓
Click
 ↓
Conversion (where available)
```

Store relationships to:

- campaign
- advertiser
- creative
- placement
- episode
- series
- creator
- geography
- device
- timestamp
- session

---

# 19. Creator Payment Portal

```text
Available Balance
R12,130.00

[ REQUEST PAYOUT ]

Next Payout
24 May 2026

Estimated Payout
R12,130.00
```

Sections:

- earnings
- transactions
- payouts
- payment methods
- tax information
- statements
- payment history

Never expose full financial account numbers.

Do not store raw card data. Use tokenised payment-provider infrastructure.

---

# 20. Revenue Model

Potential viewer revenue:

- free ad-supported viewing
- premium subscription
- premium episodes
- early access
- offline downloads

Creator revenue:

- advertising share
- subscription share
- sponsored content
- fan support/tips
- premium releases

Welele revenue:

- platform revenue share
- originals
- production
- licensing
- advertising
- partnerships

Revenue-share percentages must be configurable in the backend, not hard-coded.

---

# 21. AI-Generated Video & Welele AI™

AI makes sense as a production accelerator rather than a replacement for storytellers.

Potential uses:

- story ideation
- script development
- storyboards
- visual development
- trailers
- promotional clips
- pilot production
- voice
- music
- captions
- localisation

Core philosophy:

> **AI lowers the production barrier. Humans provide the story.**

Pipeline:

```text
Story Idea
 ↓
AI Story Development
 ↓
Characters
 ↓
Episode Structure
 ↓
Script
 ↓
Storyboard
 ↓
Visual Development
 ↓
Video Generation / Production
 ↓
Voice
 ↓
Music
 ↓
Captions
 ↓
Human Review
 ↓
Publish
```

---

# 22. Multilingual Architecture

Initial/future language support should include:

- English
- isiZulu
- isiXhosa
- Sesotho
- Setswana
- Sepedi
- Xitsonga
- siSwati
- Tshivenda
- Afrikaans

Support:

- original language
- subtitles
- dubbed audio
- creator-approved translations
- AI-assisted localisation

Never overwrite the creator's original language.

---

# 23. Admin Platform

Admin is desktop-first.

Navigation:

```text
Dashboard
Content
Series
Episodes
Creators
Users
Engagement
Revenue
Payouts
Subscriptions
Welele Chat
Reports
Settings
System
```

Admin dashboard:

- Total Views
- Watch Time
- Subscribers
- Revenue
- Creators
- Active Users
- Content Published
- Engagement

Panels:

- views over time
- revenue
- top-performing series
- audience demographics
- geographic distribution
- recent activity
- content performance

---

# 24. Admin Content Control

Admins can:

- review uploads
- approve/reject content
- edit metadata
- manage artwork
- schedule releases
- feature stories
- manage age ratings
- manage rights
- handle takedowns

Creator administration:

- verification
- onboarding
- content history
- earnings
- violations
- payout status
- suspension
- support

User administration:

- account
- subscription
- reports
- moderation
- device sessions
- preferences
- support history

---

# 25. Analytics

Unified event model:

```text
app_open
session_start
story_impression
story_open
play
pause
resume
25_percent
50_percent
75_percent
complete
next_episode
add_to_list
share
reaction
comment
chat_join
subscribe
ad_impression
ad_click
creator_upload
creator_publish
payout_request
```

Analytics should power:

- recommendations
- creator analytics
- advertising
- monetisation
- product decisions

---

# 26. Recommendation Engine

MVP:

- popularity
- recency
- genre
- completion
- watch history
- similar titles

Later:

- collaborative filtering
- embeddings
- semantic similarity
- session-based recommendations
- language/cultural preferences
- emerging creator discovery

Do not optimise solely for clicks.

Optimise for:

- completion
- satisfaction
- return visits
- meaningful discovery
- creator diversity

---

# 27. Database Architecture

Recommended initial database:

**PostgreSQL**, compatible with Supabase/Postgres.

Core entities:

```text
users
profiles
creators
creator_profiles
series
seasons
episodes
episode_assets
genres
languages
countries
cast
series_cast
watch_history
watch_progress
watchlists
subscriptions
plans
payments
transactions
payouts
payment_methods
ad_campaigns
ad_creatives
ad_impressions
ad_events
creator_earnings
comments
reactions
chat_rooms
chat_messages
notifications
reports
moderation_cases
content_rights
analytics_events
```

Large media files must not be stored directly in PostgreSQL.

---

# 28. Media Architecture

```text
Creator
 ↓
Object Storage
 ↓
Transcoding
 ↓
Multiple Resolutions
 ↓
CDN
 ↓
Adaptive Streaming
 ↓
Viewer
```

Store:

- videos
- posters
- thumbnails
- trailers
- captions
- audio
- promotional assets

Use signed URLs and appropriate access controls.

---

# 29. React Architecture

Recommended stack:

```text
React
TypeScript
Vite or Next.js
Tailwind CSS
DaisyUI or custom design system
Lucide Icons
TanStack Query
Zod
React Hook Form
PostgreSQL / Supabase
Object Storage
CDN
```

A PWA is sufficient for the first release.

Keep the architecture compatible with future Capacitor/native packaging.

---

# 30. Frontend Structure

```text
src/
│
├── app/
│   ├── router/
│   ├── providers/
│   └── config/
│
├── components/
│   ├── ui/
│   ├── navigation/
│   ├── video/
│   ├── story/
│   ├── creator/
│   ├── chat/
│   ├── monetisation/
│   └── analytics/
│
├── features/
│   ├── auth/
│   ├── home/
│   ├── discover/
│   ├── watch/
│   ├── library/
│   ├── chat/
│   ├── profile/
│   ├── creator-hub/
│   ├── monetisation/
│   └── admin/
│
├── hooks/
├── services/
│   ├── api/
│   ├── analytics/
│   ├── payments/
│   ├── video/
│   └── notifications/
│
├── stores/
├── types/
├── utils/
├── styles/
└── assets/
```

---

# 31. Reusable Component System

Core components:

```text
Button
IconButton
Avatar
Badge
Card
StoryCard
EpisodeCard
CreatorCard
Poster
Hero
BottomNav
TopBar
Modal
Drawer
Tabs
ProgressBar
VideoPlayer
ReactionBar
ChatBubble
StatCard
ChartCard
DataTable
EmptyState
Skeleton
Toast
```

Use domain-specific components instead of building screens from one-off markup.

---

# 32. Viewer / Creator / Admin Modes

### Viewer
Mobile-first, vertical, touch-first.

### Creator
Responsive desktop/mobile workspace.

### Admin
Desktop information-dense control centre.

All three share:

- design tokens
- typography
- brand assets
- components
- authentication
- permissions

---

# 33. Authentication & Roles

Account roles:

```text
Viewer
Creator
Moderator
Advertiser
Partner
Admin
Super Admin
```

A user should be able to become a creator without creating a second account.

```text
User Account
   ├── Viewer Profile
   └── Creator Profile
```

Permissions must be enforced server-side.

---

# 34. Notifications

Story:

- new episode
- new season
- recommendation

Community:

- reply
- reaction
- mention
- chat activity

Creator:

- upload approved
- new subscriber
- milestone
- earnings
- payout

Platform:

- announcements
- security alerts

Users control notification preferences.

---

# 35. PWA Strategy

MVP should be **PWA-first**.

Advantages:

- one React codebase
- installable
- no immediate app-store dependency
- rapid iteration
- web sharing/deep links
- lower initial development cost

Support:

- install prompt
- offline shell
- push notifications
- caching
- responsive UI
- deep links

Native iOS/Android and Smart TV clients can follow once product-market fit is established.

---

# 36. Welele Sonic Identity

The Welele Original ident should become a recurring brand ritual.

Target duration: **3–4 seconds**.

Sequence:

```text
BLACK
 ↓
HEARTBEAT
 ↓
EMBER
 ↓
PARTICLES
 ↓
CONNECTIONS FORM
 ↓
W SYMBOL
 ↓
WELELE™
 ↓
FEMALE VOICE
 ↓
STORY
```

The visual metaphor:

**spark → people → connection → story**

The intended voice is a mature, warm African female voice saying:

> **“Weleleeeee...”**

It should sound intimate and welcoming, not like an advert.

The long-term recording should be professionally performed by a human voice artist; AI can be used for exploration.

---

# 37. About / Corporate Story

Website/app About page should centre on:

## We believe stories connect us.

Key narrative:

> Every laugh, every tear and every cliffhanger begins with a connection.

Then:

> Technology should strengthen human connection, not replace it.

And:

> Welele™ exists to empower African storytellers and bring unforgettable stories to audiences everywhere.

### Why Africa?

> Africa isn't short of stories.  
> It has been short of platforms built for them.  
> Welele™ exists to change that.

---

# 38. Website

Suggested structure:

```text
/
├── Home
├── About
├── Features
├── Creators
├── Business
├── Blog
├── Support
├── Login
└── Get the App
```

Hero:

# Stories That Move You

> Africa's next-generation storytelling platform.

CTAs:

**Get the App**  
**Watch Trailer**

Creator CTA:

> **Create. Share. Earn.**

---

# 39. Empty & Error States

Keep the brand human.

Empty:

> **Your next story is waiting.**

No messages:

> **It's quiet here... for now.**

Video failure:

> **Oops. The story got interrupted.**

Button:

**Try Again**

Microcopy examples:

> **What's moving you today?**

> **Continue your story**

> **Join the conversation**

> **Something new just dropped**

---

# 40. Performance & Accessibility

Performance targets:

- fast initial load
- lazy-loaded imagery
- adaptive video
- CDN delivery
- skeleton loading
- small JS bundles
- mobile-network optimisation

Accessibility:

- captions
- scalable text
- high contrast
- screen reader support
- keyboard navigation on desktop
- reduced-motion preference
- accessible video controls

---

# 41. Security

Required:

- HTTPS
- secure authentication
- RBAC
- server-side authorisation
- signed media URLs
- rate limiting
- audit logs
- encrypted sensitive data
- secure secrets
- tokenised payments
- content reporting
- abuse prevention

Never trust frontend permissions.

---

# 42. Content Rights

Every content object should support:

```text
Owner
Creator
Production Company
Territory
Start Date
End Date
Platform Rights
Language Rights
Advertising Rights
Exclusive / Non-exclusive
```

This is critical when Welele begins commissioning and licensing content.

---

# 43. Audit & Observability

Audit important administrative actions:

```text
Who
What
When
Before
After
Reason
```

Monitor:

- API latency
- errors
- video startup
- buffering
- failed uploads
- payment failures
- notification failures
- database health
- CDN health

---

# 44. Event-Driven Scaling

As the platform grows:

```text
Video / User Event
       ↓
   Event Bus
       ├── Analytics
       ├── Recommendations
       ├── Creator Earnings
       ├── Notifications
       └── Advertising
```

This prevents analytics and monetisation processing from slowing the viewing experience.

---

# 45. MVP Scope

Do not attempt the entire ecosystem on day one.

## Viewer MVP

- authentication
- Home
- Discover
- Search
- Story details
- video playback
- Continue Watching
- My List
- Profile
- basic notifications

## Creator MVP

- creator registration
- creator profile
- series creation
- episode upload
- publishing workflow
- basic analytics
- earnings dashboard

## Admin MVP

- dashboard
- content moderation
- creator management
- user management
- series/episode management
- basic revenue reporting

## Community MVP

- comments
- reactions
- basic story chat

---

# 46. Phase 2

- subscriptions
- advertising
- creator payouts
- advanced analytics
- creator levels
- push notifications
- AI recommendations
- multilingual subtitles
- offline viewing

---

# 47. Phase 3

- Welele AI
- AI-assisted production
- creator marketplace
- watch parties
- fan clubs
- live events
- branded content
- advanced advertiser platform

---

# 48. Phase 4

- Welele Studios
- international licensing
- African-language dubbing
- global creator network
- Welele Audio
- Welele Live
- Smart TV apps
- connected TV distribution

---

# 49. Core User Loop

```text
Discover
 ↓
See Story
 ↓
Play
 ↓
Become Emotionally Invested
 ↓
Cliffhanger
 ↓
Next Episode
 ↓
React
 ↓
Join Chat
 ↓
Follow Creator
 ↓
Notification
 ↓
Return
```

The product should optimise this loop without using manipulative dark patterns.

---

# 50. Creator Loop

```text
Register
 ↓
Build Profile
 ↓
Create Series
 ↓
Upload
 ↓
Moderation
 ↓
Publish
 ↓
Audience
 ↓
Engagement
 ↓
Analytics
 ↓
Revenue
 ↓
Payout
 ↓
Grow
 ↓
Create More
```

---

# 51. Strategic Moat

The long-term platform advantage should be:

```text
CREATORS
    +
CONTENT
    +
AUDIENCE
    +
COMMUNITY
    +
DATA
    +
PRODUCTION TOOLS
    +
MONETISATION
```

AI can dramatically reduce production costs, but it does not remove the need for great stories.

Therefore the creator/content ecosystem remains the strategic moat.

---

# 52. Brand Manifesto

> **We believe stories connect us.**
>
> Every laugh.  
> Every tear.  
> Every gasp.  
> Every conversation after the credits.
>
> A story creates a connection between people who may never meet.
>
> Welele Media™ exists to strengthen those connections.
>
> We build technology for storytellers.  
> We create space for creators.  
> We bring audiences together.  
> We connect Africa to the world.
>
> **Welele™**  
> **Stories That Move You.**
>
> **It's about connection.**

---

# 53. North Star

The product should ultimately answer:

> **Did Welele make someone feel something, discover someone, or connect with someone?**

If yes, the product is doing its job.

---

# 54. Final Architecture

```text
                         WELELE MEDIA™
                    "It's about connection."
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
      AUDIENCE             CREATORS            BRANDS
          │                   │                   │
       Welele™          Creator Hub™         Welele Ads™
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                       STORY ECOSYSTEM
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
        STORIES             CHAT               AI
           │                  │                  │
      Originals          Communities        Production
           │                  │                  │
           └──────────────────┼──────────────────┘
                              │
                         CONNECTION
```

---

# 55. Recommended Build Order

### Stage 1 — Foundation
React/TypeScript, design system, authentication, database, storage, navigation, Home, Discover, Story Details, Player.

### Stage 2 — Content Platform
Creator onboarding, Series, Episodes, uploads, moderation, publishing.

### Stage 3 — Community
Comments, reactions, Welele Chat, notifications, creator profiles.

### Stage 4 — Monetisation
Subscriptions, advertising, creator earnings, payouts, financial reporting.

### Stage 5 — Intelligence
Recommendations, analytics, AI creator tools, localisation.

### Stage 6 — Scale
Native apps, Smart TV, Originals, creator marketplace and international expansion.

---

# FINAL PRODUCT DEFINITION

Welele should **not** become simply:

> “Netflix with African content.”

The larger opportunity is:

> **A technology-powered African storytelling ecosystem.**

Netflix is primarily a destination for content.

Welele can become a destination for:

**Stories + Creators + Communities + Technology + Monetisation.**

The enduring differentiator is not merely AI, short episodes or geography.

It is the philosophy underneath the entire system:

# Welele™
## Stories That Move You.

### Welele Media™
## It's about connection.
