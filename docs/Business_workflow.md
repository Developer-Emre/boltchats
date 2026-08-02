# SparkQuark - Business Workflow & User Journey

**Version:** 1.0.0  
**Status:** Draft  
**Phase:** Product Design  
**Purpose:** Define the complete business workflow and user journey of SparkQuark.

---

# Overview

SparkQuark is an **Omnichannel Customer Communication Platform** that enables businesses to manage customer conversations from multiple communication channels through a single unified workspace.

Unlike Discord or Slack, SparkQuark is customer-centric rather than team-centric.

Customers never log into SparkQuark.

Only company employees access the platform.

Supported communication channels include:

- Instagram
- Facebook Messenger
- WhatsApp Business
- Email
- Telegram
- Live Chat
- Future channels...

---

# Actors

There are five primary actors within the system.

```
                    Owner
                      │
                Organization
                      │
          ┌───────────┴───────────┐
          │                       │
       Admin                  Manager
                                  │
                              Agents
                                  │
                         Customer Conversation
                                  │
                               Customer
```

---

# User Roles

## Organization Owner

Responsible for the entire organization.

Permissions:

- Create organization
- Manage billing
- Connect integrations
- Invite users
- Manage permissions
- Manage workspaces
- View analytics
- Delete organization

---

## Admin

Responsible for daily administration.

Can:

- Invite members
- Create teams
- Manage conversations
- Manage labels
- Configure integrations

Cannot:

- Delete organization
- Change subscription

---

## Manager

Responsible for operations.

Can:

- Assign conversations
- Monitor agents
- View reports
- Manage teams
- Review conversations

---

## Agent

Support employee.

Can:

- Reply to customers
- Receive assignments
- Create notes
- Mention teammates
- Close conversations

---

## Customer

External user.

Customer never logs into SparkQuark.

Customer communicates through:

- Instagram
- Facebook
- WhatsApp
- Email
- Live Chat

---

# Complete User Journey

---

# Phase 1 — Landing Page

Business owner visits

```
sparkquark.io
```

Available actions:

```
Login

Start Free Trial

Book Demo

Contact Sales
```

---

# Phase 2 — Organization Registration

Owner creates the organization.

Required information:

```
Company Name

Organization Name

Owner Name

Business Email

Password

Country

Timezone

Language
```

System creates automatically:

```
Organization

Default Workspace

Owner Member

Admin Role

Default Teams

System Labels
```

---

# Phase 3 — First Login

User logs in.

Dashboard is empty.

Displayed screen:

```
Welcome to SparkQuark!

No channels connected.

Connect your first communication channel.
```

---

# Phase 4 — Initial Setup Wizard

A guided onboarding wizard starts.

---

## Step 1

Connect Instagram Business

```
Connect Instagram
```

---

## Step 2

Connect Facebook Page

```
Connect Facebook
```

---

## Step 3

Connect WhatsApp Business

```
Connect WhatsApp
```

---

## Step 4

Invite Team Members

```
Invite Team
```

---

## Step 5

Setup Complete

```
Start Using SparkQuark
```

Every step can be skipped.

---

# Phase 5 — Meta Integration

Owner navigates to

```
Settings

↓

Integrations

↓

Meta

↓

Connect
```

OAuth flow begins.

```
SparkQuark

↓

Meta OAuth

↓

Permission Screen

↓

Business Selection

↓

Instagram Account

↓

Facebook Page

↓

Webhook Registration

↓

OAuth Token

↓

Integration Created
```

System stores:

- Access Token
- Refresh Token
- Business ID
- Instagram ID
- Facebook Page ID
- Webhook Configuration

---

# Phase 6 — Invite Team

Owner opens

```
Settings

↓

Members
```

Invites users.

Invitation includes:

```
Email

Role

Workspace

Team
```

User receives email.

Clicks

```
Accept Invitation
```

Account becomes active.

---

# Phase 7 — Daily Dashboard

Every morning agents enter the system.

Landing page is

```
Inbox
```

NOT

```
Rooms
```

NOT

```
Channels
```

Inbox sections:

```
Assigned

Unassigned

Open

Pending

Resolved

Closed
```

---

# Phase 8 — Incoming Customer Message

Customer sends message.

Example:

Instagram DM

```
Hello,

Is this product available?
```

Flow:

```
Instagram

↓

Meta Webhook

↓

SparkQuark Webhook

↓

Webhook Verification

↓

Normalize Payload

↓

Resolve Customer

↓

Find Conversation

↓

Create Conversation (if needed)

↓

Store Message

↓

Publish Event

↓

Redis

↓

WebSocket

↓

Agent Dashboard
```

---

# Phase 9 — Agent Notification

Assigned agent instantly receives

```
New Conversation

Instagram

Ali Yılmaz

Just now
```

Notification methods:

- WebSocket
- Browser Notification
- Email (optional)

---

# Phase 10 — Conversation Screen

Agent opens conversation.

Layout:

## Left Sidebar

```
Inbox

Assigned

Labels

Filters
```

---

## Center Panel

Conversation timeline

```
Customer

↓

Messages

↓

Attachments

↓

Replies
```

---

## Right Sidebar

Customer Profile

```
Customer Information

Connected Channels

Previous Conversations

Tags

Internal Notes

Conversation Statistics
```

---

# Phase 11 — Reply to Customer

Agent writes message.

```
Hello,

Yes, the product is available.
```

Flow

```
Agent

↓

Message Service

↓

Provider Adapter

↓

Meta Graph API

↓

Instagram

↓

Customer
```

Conversation updates in real-time.

---

# Phase 12 — Internal Collaboration

Agent needs help.

Creates internal note.

```
@Mehmet

Can you verify this order?
```

Customer NEVER sees:

- Mentions
- Internal Notes
- Assignments

Internal collaboration remains invisible externally.

---

# Phase 13 — Assignment

Manager reassigns conversation.

```
Assign

↓

Ahmet
```

System:

```
Conversation Assigned

↓

Notification

↓

Dashboard Updated
```

---

# Phase 14 — Labels

Conversation may receive labels.

Examples

```
VIP

Refund

Complaint

Urgent

Sales

Technical

Spam
```

Multiple labels supported.

---

# Phase 15 — Drafts

Agent starts typing.

Draft is automatically saved.

If browser closes:

```
Draft Restored
```

---

# Phase 16 — Customer History

Returning customer sends another message.

System resolves identity.

Instead of creating a duplicate profile:

```
Instagram

↓

Customer Resolver

↓

Existing Customer

↓

Conversation History
```

Agent sees:

```
Conversation #21

Conversation #33

Conversation #57
```

---

# Phase 17 — Merge Customer Profiles

Customer later contacts by Email.

```
Instagram

↓

Ali

Email

↓

Ali@example.com
```

Manager selects

```
Merge Customer
```

Result:

```
Customer

Instagram

Facebook

Email

WhatsApp

Telegram
```

One unified customer profile.

---

# Phase 18 — Resolve Conversation

Problem solved.

Agent selects

```
Resolve
```

Conversation status

```
Resolved
```

Later

```
Closed

↓

Archived
```

according to retention policy.

---

# Phase 19 — Dashboard Analytics

Managers and Owners monitor:

```
Open Conversations

Resolved Today

Average Response Time

First Response Time

Average Resolution Time

Messages Today

Agent Performance

Online Members

Channel Distribution

Customer Satisfaction (Future)
```

---

# Phase 20 — Settings

Organization settings include:

```
General

Members

Teams

Roles

Permissions

Integrations

API Keys

Webhooks

Billing

Audit Logs

Security

Organization Preferences
```

---

# Future Automation Workflow

Future versions introduce workflow automation.

Example:

```
IF

Channel = Instagram

AND

Message contains "refund"

↓

Assign Refund Team

↓

Set Priority = High

↓

Add Label = Refund

↓

Notify Manager
```

---

# Future AI Workflow

AI capabilities can be added without changing architecture.

```
Incoming Message

↓

AI Summary

↓

Intent Detection

↓

Sentiment Analysis

↓

Suggested Reply

↓

Translation

↓

Agent Review

↓

Send
```

---

# Complete Business Flow

```
Owner Registers
        │
        ▼
Organization Created
        │
        ▼
Workspace Created
        │
        ▼
Connect Communication Channels
        │
        ▼
Invite Team Members
        │
        ▼
Webhook Registration
        │
        ▼
Customer Sends Message
        │
        ▼
Webhook Received
        │
        ▼
Verify Request
        │
        ▼
Normalize Payload
        │
        ▼
Resolve Customer Identity
        │
        ▼
Find Existing Conversation
        │
        ▼
Create Conversation (if needed)
        │
        ▼
Store Message
        │
        ▼
Publish Domain Event
        │
        ▼
Redis Queue
        │
        ▼
WebSocket Notification
        │
        ▼
Agent Opens Conversation
        │
        ▼
Reply Sent
        │
        ▼
Provider Adapter
        │
        ▼
Instagram / WhatsApp / Email
        │
        ▼
Customer Receives Reply
        │
        ▼
Conversation Resolved
        │
        ▼
Analytics Updated
        │
        ▼
Audit Log Recorded
```

---

# Design Principles

SparkQuark follows these core principles:

- Customer-centric architecture
- Omnichannel communication
- Organization-first multi-tenancy
- Event-driven architecture
- Real-time collaboration
- Role-based access control (RBAC)
- Extensible provider integrations
- Unified customer identity
- Scalable workflow automation
- AI-ready platform architecture

---

# End of Document