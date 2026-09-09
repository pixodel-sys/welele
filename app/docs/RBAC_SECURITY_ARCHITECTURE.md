# Welele Media™ — Role-Based Access Control (RBAC) & Security Architecture

This document defines the Role-Based Access Control (RBAC), Identity and Access Management (IAM), and data isolation architecture across Welele Media's three core surfaces: **Viewer (Consumer Streaming)**, **Creator Studio (Showrunner Workstation)**, and **Admin Studio (Platform Management)**.

---

## 1. System Overview & User Hierarchy

```
                         WELELE IDENTITY & ACCESS MANAGEMENT
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
     VIEWER                            CREATOR                           ADMIN
 (Consumer Streaming)           (Showrunner Workstation)         (Platform Ops & Trust)
        │                                 │                                 │
 • Phone Number + SMS OTP          • Email/Pass + 2FA / Phone + PIN  • Enterprise SSO + 2FA / WebAuthn
 • Guest Token / Device ID         • Verified African Creator KYC    • IP Allowlisting & Audit Trail
 • Scope: Watch, Unlock, Tip       • Scope: Own Series & MoMo        • Scope: Global Platform Mgmt
```

---

## 2. Role Definitions & Security Matrix

### A. Viewer (`ROLE_VIEWER`)
* **Target User:** End consumer watching vertical microdramas in South Africa and pan-African markets.
* **Risk Profile:** Minimal attack surface.
* **Authentication Method:**
  * **Carrier / Mobile OTP:** Phone number + 4-digit SMS OTP (Vodacom, MTN, Airtel, Safaricom).
  * **Anonymous Guest Session:** Instant zero-barrier trial token bound to device fingerprint.
* **Permissions & Capabilities:**
  * `stream:episode:free` — Stream promotional acquisition episodes.
  * `wallet:recharge` — Top-up coin balance via Direct Carrier Billing (Airtime) or Mobile Money.
  * `stream:episode:unlock` — Deduct coins to unlock cliffhanger episodes.
  * `social:gift:send` — Tip creators with African cultural virtual gifts (Charly, Dashiki, Cowries, Braai Pack).
  * `social:chat:participate` — Post live comments and send reactions during playback.
* **Restrictions:**
  * **Strictly barred** from accessing `/creator/*` or `/admin/*` routes and API endpoints.

---

### B. Creator / Showrunner (`ROLE_CREATOR`)
* **Target User:** Independent film directors, writers, and African production studios creating 9:16 vertical microdramas.
* **Risk Profile:** Medium–High (Intellectual property, unreleased scripts, video assets, banking/MoMo payout details).
* **Authentication Method:**
  * Registered showrunner account (Email + Password + 2FA, or verified Phone + Studio PIN).
  * **Mandatory Creator KYC:** Identity verification (National ID / Passport / Studio Registration) before MoMo settlements are disbursed.
* **Permissions & Capabilities:**
  * `series:create` & `series:update:own` — Create and manage owned microdrama catalogue.
  * `episode:upload` — Ingest 9:16 vertical episodes via pre-signed Cloudflare R2 / AWS S3 URLs.
  * `ai:storyforge:execute` — Generate cliffhanger scripts, character bibles, and story arcs with Welele AI™.
  * `analytics:read:own` — View retention curves, cliffhanger completion rates, and coin breakdown for owned titles.
  * `settlement:payout:request` — Request automated M-Pesa, MTN MoMo, or EFT payout settlements.
* **Restrictions & Data Isolation:**
  * **Tenant Isolation:** A creator can **only see and modify series/episodes where `creator_id == current_user.id`**.
  * **Strictly barred** from viewing other creators' private analytics, unreleased video drafts, or platform admin tools.

---

### C. Platform Administrator (`ROLE_ADMIN`)
* **Target User:** Welele Media executive leadership, content curators, safety moderators, and finance operations.
* **Risk Profile:** Critical infrastructure risk.
* **Authentication Method:**
  * Enterprise Email + Hardware Token / Authenticator 2FA + IP Allowlisting.
* **Permissions & Capabilities:**
  * `experience:layout:publish` — Reorder, edit, and publish dynamic home showcase experiences in Welele Admin Studio (WEE).
  * `moderation:queue:review` — Review AI safety flagged episodes, DRM infringement alerts, and age-rating compliance.
  * `creator:kyc:approve` — Review and verify African showrunner identity and payout credentials.
  * `ledger:audit:read` — Platform-wide financial double-entry ledger oversight and settlement clearing.

---

## 3. JWT Claims Specification

Every authenticated session issues a cryptographically signed JWT with the following payload structure:

```json
{
  "sub": "usr_94b8e21a",
  "phone": "+27828912345",
  "market": "ZA",
  "role": "creator",
  "creator_id": "cr_zola_dlamini_01",
  "permissions": [
    "series:create",
    "series:update:own",
    "episode:upload",
    "ai:storyforge:execute",
    "settlement:payout:request"
  ],
  "kyc_status": "VERIFIED",
  "exp": 1757364000,
  "iss": "welele.media/auth"
}
```

---

## 4. API Layer Route Guards (FastAPI Implementation)

FastAPI endpoints enforce role scopes through dependency injection:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def require_role(allowed_roles: list[str]):
    def role_checker(credentials: HTTPAuthorizationCredentials = Depends(security)):
        token = credentials.credentials
        payload = verify_jwt(token)
        user_role = payload.get("role")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role in {allowed_roles}, but found '{user_role}'."
            )
        return payload
    return role_checker

# Example Protected Endpoints
@router.post("/creator/episodes/upload", dependencies=[Depends(require_role(["creator", "admin"]))])
def upload_episode(payload: EpisodeUploadRequest, auth_user = Depends(get_current_user)):
    # Automatically scoped to auth_user["creator_id"]
    return episode_service.create_episode(creator_id=auth_user["creator_id"], data=payload)

@router.post("/admin/experience/publish", dependencies=[Depends(require_role(["admin"]))])
def publish_homepage_experience(layout: ExperiencePayload):
    return experience_engine.publish_live_layout(layout)
```

---

## 5. Database Row-Level Security (Postgres / Supabase RLS)

Data isolation is enforced at the database storage engine layer:

```sql
-- Enable Row-Level Security on Core Tables
ALTER TABLE series ENABLE ROW LEVEL SECURITY;
ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledger_transactions ENABLE ROW LEVEL SECURITY;

-- 1. Series Visibility Policy: Public can view published series; Creators can view own drafts; Admin sees all
CREATE POLICY "series_access_policy" ON series
FOR ALL USING (
    status = 'PUBLISHED'
    OR creator_id = auth.uid()
    OR auth.jwt() ->> 'role' = 'admin'
);

-- 2. Episode Visibility Policy: Viewers only see published; Creators see their owned series episodes
CREATE POLICY "episodes_access_policy" ON episodes
FOR ALL USING (
    status = 'PUBLISHED'
    OR series_id IN (SELECT id FROM series WHERE creator_id = auth.uid())
    OR auth.jwt() ->> 'role' = 'admin'
);

-- 3. Wallet Ledger Policy: Users and Creators can only read their own financial balances
CREATE POLICY "wallet_owner_isolation" ON wallets
FOR ALL USING (
    user_id = auth.uid()
    OR auth.jwt() ->> 'role' = 'admin'
);
```

---

## 6. Frontend Navigation & Interface Gating

1. **Viewer Session:** Top mode switcher is hidden; user interacts exclusively with the mobile-optimized vertical streaming interface.
2. **Creator Session:** Redirected directly to `/creator` workstation upon login. Displays series management, Story Forge AI, and MoMo payout settings. Wrapped with `<RequireRole allowedRoles={['creator', 'admin']}>`.
3. **Admin Session:** Displays Admin Studio with device simulators, experience tree re-ordering, AI moderation queues, and KYC approvals. Wrapped with `<RequireRole allowedRoles={['admin']}>`.

---

## 7. Institutional Trust Infrastructure: Append-Only Hash-Chained Audit Ledger

Welele Media implements an institutional-grade, cryptographic append-only audit ledger across **6 core trust domains**:

### Trust Domains & Sensitive State Transitions
1. **AUTH**: `auth.login`, `auth.failed_login`, `auth.token_refresh`, `auth.role_change`
2. **IP**: `ip.created`, `ip.rights_changed`, `ip.contributor_changed`, `ip.story_package_created`
3. **CONTENT**: `content.series_created`, `content.episode_created`, `content.episode_submitted`, `content.moderation_decision`, `content.publication`, `content.unpublication`
4. **COMMERCE**: `commerce.payment_received`, `commerce.wallet_mutation`, `commerce.royalty_calculation`, `commerce.payout`, `commerce.refund`
5. **EXPERIENCE**: `experience.layout_changed`, `experience.draft_published`, `experience.schedule_changed`
6. **SECURITY**: `security.permission_denied`, `security.ownership_violation`, `security.signature_failure`, `security.suspicious_access`

### Cryptographic Integrity & Immutability Guarantees
- **Payload Hash**: Each event's canonical JSON payload is hashed with `SHA-256`.
- **Chain Hash**: Each entry links to the previous entry via `SHA-256(entry_index + previous_entry_hash + payload_hash + timestamp)`.
- **Append-Only Database Rule**: Strict database-level `REVOKE UPDATE, DELETE, TRUNCATE ON security_audit_ledger FROM PUBLIC, authenticated, anon;`
- **Tamper-Evident Verification**: The platform verifies chain continuity and cryptographic non-repudiation via `/api/admin/audit-logs/verify-chain`.
