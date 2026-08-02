# SparkQuark - Register & Onboarding Flow

**Version:** 1.0  
**Status:** Production Design  
**Purpose:** Describe how a new organization is created and prepared before using SparkQuark.

---

# Overview

Every SparkQuark account starts with an **Organization**.

An Organization is the tenant boundary of the entire platform.

Everything belongs to an organization:

- Members
- Teams
- Roles
- Conversations
- Customers
- Integrations
- Notifications
- Audit Logs
- Events

There is **no global data sharing** between organizations.

---

# High Level Flow

```

Landing Page
│
▼
Register
│
▼
Verify Email
│
▼
Create Organization
│
▼
Create Owner Member
│
▼
Seed Default Roles
│
▼
Create Default Workspace
│
▼
Redirect Dashboard
│
▼
Connect First Channel
│
▼
Receive First Customer Message

```

---

# Step 1 — User Registration

User enters

- Name
- Company Name
- Email
- Password

API

```

POST /auth/register

```

Backend validates

- email format
- password strength
- organization name
- duplicate email

If everything is valid

Create

```

User

```

Password is hashed using bcrypt.

Nothing else is created yet.

---

# Step 2 — Email Verification

SparkQuark sends

Verification Email

```

https://sparkquark.com/verify?token=...

```

User clicks

Backend

```

POST /auth/verify-email

```

User becomes

```

verified = true

```

Only verified users can continue.

---

# Step 3 — Organization Creation

Backend creates

```

Organization

```

Example

```

{
"id":"org_01H...",
"name":"Acme Inc.",
"slug":"acme",
"plan":"trial"
}

```

Every resource from now on references

```

organization_id

```

---

# Step 4 — Create Owner Member

The registered user now becomes

```

Owner

```

Member document

```

{
"member_id":"mem_xxx",
"organization_id":"org_xxx",
"user_id":"usr_xxx",
"roles":[Owner]
}

```

Owner has

All permissions.

---

# Step 5 — Seed Default Roles

Backend automatically creates

Admin

Manager

Agent

Viewer

Each role already contains predefined permissions.

Example

```

Admin

conversation:*
member:*
team:*
integration:*

```

No manual setup required.

---

# Step 6 — Create Default Workspace

Automatically

```

Workspace

```

is created.

Default

```

Support

```

Workspace can later be renamed or deleted.

Future examples

- Sales
- Marketing
- Technical Support

---

# Step 7 — Seed System Labels

Create default labels

```

New

Waiting

Urgent

VIP

Spam

Resolved

```

These help organize conversations immediately.

---

# Step 8 — Redirect to Dashboard

Dashboard is initially empty.

```

Conversations = 0
Customers = 0
Messages = 0
Channels = 0

```

A setup wizard starts.

---

# Step 9 — Setup Wizard

SparkQuark guides the owner.

Progress

```

□ Connect Instagram

□ Connect Facebook

□ Connect WhatsApp

□ Invite Team Members

□ Create Teams

□ Finish Setup

```

Owner may skip any step.

---

# Step 10 — Connect First Integration

Example

Instagram

```

Dashboard
↓
Settings
↓
Integrations
↓
Connect Instagram

```

OAuth Flow

```

SparkQuark
↓

Meta OAuth
↓

Permission Grant
↓

Access Token
↓

Webhook Registration
↓

Integration Connected

```

Backend stores

```

Integration

OAuth Token

Webhook Config

```

---

# Step 11 — Webhook Activation

SparkQuark subscribes to

Instagram Events

Example

```

message

message_seen

message_reaction

```

Now SparkQuark waits for events.

---

# Step 12 — First Incoming Message

Customer sends

```

Hello

```

Instagram

↓

Meta Webhook

↓

SparkQuark

↓

Webhook Service

↓

Conversation Service

↓

Database

↓

WebSocket

↓

Dashboard

Owner immediately sees

```

1 New Conversation

```

without refreshing the page.

---

# Database Objects Created

During onboarding the following documents are created.

```

User

Organization

Member

Roles

Workspace

Labels

Audit Log

Events

```

After connecting Instagram

```

Integration

OAuth Token

Webhook Config

```

---

# Events Produced

The onboarding process generates domain events.

```

UserRegistered

↓

EmailVerified

↓

OrganizationCreated

↓

MemberCreated

↓

RoleSeeded

↓

WorkspaceCreated

↓

IntegrationConnected

↓

WebhookSubscribed

```

These events are stored in

```

Domain Events

```

collection.

---

# Permissions After Registration

Owner automatically receives

```

organization:*

member:*

workspace:*

conversation:*

customer:*

message:*

integration:*

analytics:*

settings:*

```

No additional approval is required.

---

# Result

At the end of onboarding the organization is fully operational.

The owner can immediately:

- Connect communication channels
- Invite teammates
- Assign roles
- Receive customer messages
- Respond from one inbox
- View analytics
- Manage integrations

The platform is now ready for real-time omnichannel communication.
