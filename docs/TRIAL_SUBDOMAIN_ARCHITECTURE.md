# Multi-Tenant Subdomain + Trial Period Architecture

**Version:** 1.0 (Concept)  
**Status:** Planning Phase  
**Date:** 2026-08-03  
**Purpose:** Design free trial (3 months) → paid subdomain dashboard flow

---

## 📊 High-Level Flow

```
User Registration
    ↓
Trial Organization Created (3 months free)
    ↓
Main Dashboard (default.sparkquark.com or main.sparkquark.com)
    ↓
Month 1-3 (Free Trial)
    ├─ Full access to all features
    ├─ Email: "Your trial expires in 2 months"
    └─ CTA: "Upgrade now"
    ↓
Day 89 (Before expiry)
    ├─ Email: "Your trial ends in 1 day"
    └─ Must choose: Upgrade or let trial expire
    ↓
After Trial Expiry (4 options)
    ├─ Option A: User upgrades → Subdomain created
    │  └─ acme.sparkquark.com (permanent, paid)
    ├─ Option B: User ignores → Account frozen
    │  └─ "Please upgrade to continue"
    ├─ Option C: User cancels → Data deleted after 30 days
    │  └─ Compliance: GDPR right to be forgotten
    └─ Option D: User uses free tier (future)
       └─ Limited features (not MVP)
```

---

## 🏗️ Organization Model - Extended

### Current (MVP)
```python
class Organization(BaseModel):
    id: str
    name: str
    slug: str  # unique
    owner_id: str
    created_at: datetime
```

### New (Multi-Tenant)
```python
class Organization(BaseModel):
    id: str
    name: str
    slug: str  # unique, for Trial dashboard access
    owner_id: str
    
    # ⭐ TRIAL FIELDS
    plan: str = "trial"  # "trial", "basic", "pro", "enterprise"
    trial_started_at: datetime
    trial_expires_at: datetime  # created_at + 90 days
    trial_status: str = "active"  # "active", "expired", "upgraded"
    
    # ⭐ SUBDOMAIN FIELDS
    subdomain: str | None = None  # e.g., "acme" → acme.sparkquark.com
    custom_domain: str | None = None  # Future: yourcompany.com
    domain_verified: bool = False
    
    # ⭐ SUBSCRIPTION FIELDS
    subscription_id: str | None = None  # Stripe subscription ID
    payment_method_id: str | None = None  # Stripe payment method
    billing_email: str = ""
    billing_cycle_start: datetime | None = None
    billing_cycle_end: datetime | None = None
    auto_renew: bool = True
    
    # ⭐ FEATURE FLAGS
    features: dict = {
        "conversations_limit": None,  # None = unlimited
        "team_members_limit": 3,
        "integrations_limit": 1,
        "api_access": False,
        "custom_domain": False,
    }
    
    # ⭐ USAGE TRACKING
    conversations_used: int = 0
    team_members_used: int = 0
    integrations_used: int = 0
    
    # ACCOUNT STATUS
    status: str = "trial"  # "active", "trial", "paused", "cancelled", "deleted"
    
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None  # Soft delete
```

---

## 🔌 New Collections

### 1. Subscriptions
```python
class Subscription(BaseModel):
    id: str
    organization_id: str  # FK
    plan_type: str  # "basic", "pro", "enterprise"
    status: str  # "active", "cancelled", "expired", "incomplete"
    
    # Stripe Integration
    stripe_subscription_id: str
    stripe_customer_id: str
    
    # Billing
    billing_amount: int  # cents: 2999 = $29.99
    billing_currency: str = "USD"
    billing_cycle: str  # "monthly" | "yearly"
    
    # Dates
    current_period_start: datetime
    current_period_end: datetime
    cancel_at: datetime | None
    cancelled_at: datetime | None
    
    created_at: datetime
    updated_at: datetime
```

**Collections:**
- `db.subscriptions` — One per paid organization

---

### 2. PaymentMethods
```python
class PaymentMethod(BaseModel):
    id: str
    organization_id: str  # FK
    stripe_payment_method_id: str  # Never expose to client
    
    # Card Info (display only)
    card_last_four: str  # "4242"
    card_brand: str  # "visa", "mastercard"
    card_exp_month: int
    card_exp_year: int
    
    # Status
    is_default: bool = True
    status: str  # "active", "expired", "invalid"
    
    created_at: datetime
    updated_at: datetime
```

**Collections:**
- `db.payment_methods` — Payment methods per organization

---

### 3. TrialUsageLogs
```python
class TrialUsageLog(BaseModel):
    id: str
    organization_id: str  # FK
    date: date  # YYYY-MM-DD
    
    # Daily usage metrics
    conversations_created: int = 0
    messages_sent: int = 0
    team_members_invited: int = 0
    integrations_connected: int = 0
    api_calls: int = 0
    
    created_at: datetime
```

**Collections:**
- `db.trial_usage_logs` — Daily usage tracking (analytics)

---

### 4. BillingEvents
```python
class BillingEvent(BaseModel):
    id: str
    organization_id: str  # FK
    
    event_type: str  # "trial_started", "trial_expiring", "trial_expired",
                     # "upgrade_initiated", "upgrade_completed",
                     # "payment_failed", "subscription_cancelled",
                     # "payment_refunded", etc
    
    metadata: dict = {}  # {
                         #   "old_plan": "trial",
                         #   "new_plan": "basic",
                         #   "subdomain": "acme",
                         #   "amount": 2999,
                         #   "currency": "USD",
                         #   "reason": "user_request",
                         #   ...
                         # }
    
    created_at: datetime
```

**Collections:**
- `db.billing_events` — Audit trail (for compliance + analytics)

---

## 🌐 Subdomain Routing

### DNS Configuration
```
Main API:
api.sparkquark.com → 1.2.3.4

Tenant Subdomains (Wildcard):
*.sparkquark.com → 1.2.3.4  # acme.sparkquark.com, sales-1.sparkquark.com, etc

Custom Domains (Future):
yourcompany.com → CNAME: acme.sparkquark.com
```

### Request Flow
```
Request: GET https://acme.sparkquark.com/api/conversations
    ↓
TenantResolverMiddleware
    ├─ Extract "acme" from Host header
    ├─ Lookup: Organization.find_by_subdomain("acme")
    ├─ If not found → 404
    └─ Set: request.state.tenant_id = org_id
    ↓
TrialGuardMiddleware
    ├─ Check: org.status == "active" OR org.trial_status == "active"
    └─ If expired → 403 "Please upgrade to continue"
    ↓
Router
    ├─ @router.get("/api/conversations")
    └─ Dependency: tenant_id from request.state
    ↓
Service Layer
    └─ Filter: conversations.find({"organization_id": tenant_id})
    ↓
Response: Tenant-scoped data only
```

### Middleware: TenantResolver
```python
# app/middlewares/tenant_resolver.py

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class TenantResolverMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "localhost")
        
        # Extract subdomain: "acme.sparkquark.com" → "acme"
        subdomain = host.split(".")[0]
        
        # Reserved subdomains (no tenant)
        if subdomain in {"www", "api", "app", "admin", "blog", "docs", "main"}:
            request.state.tenant_id = None
            request.state.is_tenant_request = False
        else:
            # Customer tenant subdomain
            org = await OrganizationRepository.find_by_subdomain(subdomain)
            
            if not org:
                return JSONResponse(
                    status_code=404,
                    content={"detail": f"Organization '{subdomain}' not found"}
                )
            
            request.state.tenant_id = org.id
            request.state.is_tenant_request = True
            request.state.org = org
        
        response = await call_next(request)
        return response
```

### Middleware: TrialGuard
```python
# app/middlewares/trial_guard.py

class TrialGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.state.is_tenant_request:
            # Main API, no guard needed
            return await call_next(request)
        
        org = request.state.org
        
        # Allow access if paid
        if org.status == "active":
            return await call_next(request)
        
        # Allow access if trial still active
        if org.trial_status == "active":
            return await call_next(request)
        
        # Trial expired or paused
        return JSONResponse(
            status_code=403,
            content={
                "detail": "Trial expired. Please upgrade to continue using SparkQuark.",
                "upgrade_url": f"https://app.sparkquark.com/billing/upgrade?org_id={org.id}",
                "trial_status": org.trial_status,
            }
        )
```

---

## 💳 Subscription Plans

| | Trial | Basic | Pro | Enterprise |
|---|---|---|---|---|
| **Price** | Free | $29/mo | $99/mo | Custom |
| **Duration** | 3 months | 1 mo + | 1 mo + | Custom |
| **Conversations** | Unlimited | 1,000/mo | 10,000/mo | Unlimited |
| **Team Members** | 3 | 5 | 20 | Unlimited |
| **Integrations** | 1 | 3 | 10 | Unlimited |
| **API Access** | ❌ | ❌ | ✅ | ✅ |
| **Custom Domain** | ❌ | ❌ | ✅ | ✅ |
| **Subdomain** | ❌ | ✅ | ✅ | ✅ |
| **Support** | Community | Email | Priority | Dedicated |
| **SLA** | None | 99% | 99.9% | 99.99% |

---

## 🎯 Trial Flow - Detailed

### Step 1: Registration (Updated)
```python
# app/services/auth/authentication_service.py

async def register(email, password, full_name, organization_name):
    # ... existing validation ...
    
    # Create User (unchanged)
    hashed_password = password_service.hash_password(password)
    user = User(
        email=email,
        password_hash=hashed_password,
        full_name=full_name,
        email_verified=False,
    )
    user_id = await users.create(user)
    
    # ⭐ NEW: Create Organization WITH TRIAL FIELDS
    org = Organization(
        name=organization_name,
        slug=generate_slug(organization_name),
        owner_id=user_id,
        
        # Trial fields
        plan="trial",
        trial_started_at=datetime.now(timezone.utc),
        trial_expires_at=datetime.now(timezone.utc) + timedelta(days=90),
        trial_status="active",
        
        # No subdomain yet (created on upgrade)
        subdomain=None,
        subscription_id=None,
        
        # Feature limits for trial
        features={
            "conversations_limit": None,  # Unlimited
            "team_members_limit": 3,
            "integrations_limit": 1,
            "api_access": False,
            "custom_domain": False,
        },
        
        status="trial",
    )
    org_id = await organizations.create(org)
    
    # ... create workspace, roles, member, etc (unchanged) ...
    
    # ⭐ NEW: Log billing event
    await log_billing_event("trial_started", org_id, {
        "trial_expires_at": org.trial_expires_at.isoformat(),
    })
    
    return {
        "user_id": user_id,
        "org_id": org_id,
        ...
    }
```

---

### Step 2: Trial Monitoring (Daily Job)
```python
# app/services/billing/trial_monitor_service.py

async def monitor_trial_expirations():
    """Run daily (APScheduler or Celery)"""
    
    now = datetime.now(timezone.utc)
    
    # Organizations expiring in 1 day
    orgs_expiring_soon = await organizations.find({
        "trial_status": "active",
        "trial_expires_at": {
            "$gte": now,
            "$lt": now + timedelta(days=1)
        }
    })
    
    for org in orgs_expiring_soon:
        # Send "1 day left" email
        await email_service.send(
            to=org.owner.email,
            template="trial_expiring_soon",
            data={
                "org_name": org.name,
                "days_left": 1,
                "upgrade_url": f"https://app.sparkquark.com/billing?org_id={org.id}",
            }
        )
        
        await log_billing_event("trial_expiring_soon", org.id, {
            "days_remaining": 1,
        })
    
    # Organizations JUST expired (last 1 hour)
    orgs_just_expired = await organizations.find({
        "trial_status": "active",
        "trial_expires_at": {
            "$lt": now,
            "$gte": now - timedelta(hours=1)
        }
    })
    
    for org in orgs_just_expired:
        # Mark as expired
        await organizations.update(org.id, {
            "trial_status": "expired",
            "status": "paused",  # Block access
        })
        
        # Send "upgrade now" email
        await email_service.send(
            to=org.owner.email,
            template="trial_expired",
            data={
                "org_name": org.name,
                "upgrade_url": f"https://app.sparkquark.com/billing?org_id={org.id}",
            }
        )
        
        await log_billing_event("trial_expired", org.id)
```

---

### Step 3: Upgrade Flow

#### 3a. Initiate Upgrade
```python
# POST /billing/upgrade-checkout
# Request: { "organization_id": "org_123", "plan": "basic" }

async def create_upgrade_checkout(org_id: str, plan: str):
    org = await organizations.read(org_id)
    
    if org.plan != "trial":
        raise ValueError("Only trial orgs can upgrade")
    
    # Create Stripe checkout session
    session = await stripe.checkout.Session.create(
        customer_email=org.owner.email,
        payment_method_types=["card"],
        line_items=[{
            "price": STRIPE_PRICE_IDS[plan],  # price_basic_monthly
            "quantity": 1,
        }],
        mode="subscription",
        success_url=f"{FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/billing/cancel",
    )
    
    # Cache session (link to org/plan)
    await cache.setex(
        f"stripe_session:{session.id}",
        3600,  # 1 hour
        json.dumps({
            "org_id": org_id,
            "plan": plan,
            "created_at": datetime.now().isoformat(),
        })
    )
    
    return {"checkout_url": session.url}
```

#### 3b. Stripe Webhook (Payment Success)
```python
# POST /webhooks/stripe

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Retrieve org/plan from cache
        session_data = await cache.get(f"stripe_session:{session.id}")
        if not session_data:
            return JSONResponse(status_code=400, content={"error": "Session not found"})
        
        data = json.loads(session_data)
        org_id = data["org_id"]
        plan = data["plan"]
        
        # Create Subscription record
        subscription = Subscription(
            organization_id=org_id,
            plan_type=plan,
            status="active",
            stripe_subscription_id=session.subscription,
            stripe_customer_id=session.customer,
            billing_amount=PLAN_PRICES[plan],
            billing_cycle="monthly",
            current_period_start=datetime.fromtimestamp(
                session.subscription.current_period_start
            ),
            current_period_end=datetime.fromtimestamp(
                session.subscription.current_period_end
            ),
        )
        await subscriptions.create(subscription)
        
        # Allocate subdomain
        subdomain = await allocate_subdomain(org_id)
        
        # Update Organization
        await organizations.update(org_id, {
            "plan": plan,
            "trial_status": "upgraded",
            "status": "active",
            "subdomain": subdomain,
            "subscription_id": subscription.id,
        })
        
        # Log billing event
        await log_billing_event("upgrade_completed", org_id, {
            "plan": plan,
            "subdomain": subdomain,
            "stripe_subscription_id": session.subscription,
        })
        
        # Send success email
        await email_service.send(
            to=session.customer_email,
            template="upgrade_successful",
            data={
                "subdomain": subdomain,
                "dashboard_url": f"https://{subdomain}.sparkquark.com",
                "plan": plan,
            }
        )
    
    return JSONResponse(status_code=200, content={"received": True})
```

#### 3c. Subdomain Allocation
```python
# app/services/billing/subdomain_service.py

async def allocate_subdomain(org_id: str) -> str:
    """Allocate unique subdomain for upgraded org"""
    
    org = await organizations.read(org_id)
    
    # Start with org slug
    base = org.slug
    subdomain = base
    counter = 1
    
    # Check uniqueness
    while await organizations.find_by_subdomain(subdomain):
        subdomain = f"{base}-{counter}"
        counter += 1
    
    # Verify no reserved words
    if subdomain in RESERVED_SUBDOMAINS:
        subdomain = f"{base}-1"
    
    # Store subdomain
    await organizations.update(org_id, {"subdomain": subdomain})
    
    # Log
    await log_billing_event("subdomain_allocated", org_id, {
        "subdomain": subdomain,
    })
    
    return subdomain

RESERVED_SUBDOMAINS = {
    "www", "mail", "api", "app", "admin", "blog", "docs",
    "support", "help", "status", "billing", "main", "home",
    "webhook", "payment", "auth", "login", "signup", "reset"
}
```

---

## 📋 Implementation Roadmap

### Phase 1: Trial Foundation (Week 1-2)
- [ ] Extend Organization model (trial fields, status)
- [ ] Create Subscription, PaymentMethod, BillingEvent models
- [ ] Create trial_monitor_service (scheduled job)
- [ ] Add TrialGuardMiddleware
- [ ] Email templates: trial_expiring_soon, trial_expired

### Phase 2: Stripe Integration (Week 2-3)
- [ ] Setup Stripe account + test keys
- [ ] Implement Stripe checkout endpoint
- [ ] Webhook handler for payment success
- [ ] Create billing dashboard endpoint

### Phase 3: Subdomain Routing (Week 3-4)
- [ ] Implement TenantResolverMiddleware
- [ ] Add subdomain allocation logic
- [ ] Test wildcard DNS (*.sparkquark.com)
- [ ] Update frontend to use tenant subdomain

### Phase 4: Feature Limits (Week 4)
- [ ] Implement quota checks (team members, integrations)
- [ ] Usage tracking (TrialUsageLog)
- [ ] Upgrade CTA when limits reached

### Phase 5: Analytics (Week 5)
- [ ] Trial-to-paid conversion rate
- [ ] Churn analysis
- [ ] Revenue dashboard
- [ ] Payment failure tracking

---

## 🔐 Security Checklist

- [ ] Tenant isolation: All queries filter by `request.state.tenant_id`
- [ ] Subdomain reservation: Reserved words prevent squatting
- [ ] Payment security: Never store full card numbers (Stripe handles)
- [ ] Quota enforcement: Check limits before resource creation
- [ ] Trial status check: Middleware blocks expired trials
- [ ] Soft deletes: Organizations marked `deleted_at` (not hard deleted)

---

## 📌 Key Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **3-month trial** | Standard SaaS conversion window, enough to evaluate |
| **Subdomain allocation on upgrade** | Trial uses main slug, upgrade gets unique subdomain |
| **Feature limits in dict** | Easy to extend per-plan limits, no DB migration |
| **Stripe subscription mode** | Automatic billing, reduced churn vs one-time charges |
| **Soft deletes** | GDPR compliance: 30-day grace period before purge |
| **Scheduled job for monitoring** | Daily emails reduce churn before trial expires |

---

**Next Step:** Start Phase 1 (Trial Foundation)? Or finalize current auth first?

