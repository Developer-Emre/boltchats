# SparkQuark Architecture Guide

Version: 1.0
Status: MVP
Architecture: Modular Monolith (AI Ready)
Target: B2B SaaS
Language: Python (FastAPI) + Next.js
Database: MongoDB
Realtime: WebSocket
Cache: Redis

---

# 1. Product Vision

SparkQuark is an Omnichannel Customer Communication Platform designed for modern businesses.

Companies should be able to manage every customer conversation from one place.

Instead of switching between:

- Instagram
- Facebook
- WhatsApp
- Live Chat
- Email
- X (Twitter)

everything should appear inside one collaborative inbox.

SparkQuark is NOT a messaging application.

SparkQuark is a Customer Communication Operating System.

Realtime messaging is only one part of the product.

---

# 2. Goals

SparkQuark should solve these problems.

• Multiple communication channels

• Slow customer support

• No internal collaboration

• Scattered conversations

• No centralized customer profile

• No realtime collaboration

• Difficult social media management

---

# 3. Core Principles

## Multi Tenant

Everything belongs to an Organization.

Organizations are completely isolated.

Each organization owns:

- Users
- Teams
- Roles
- Customers
- Integrations
- OAuth Tokens
- Conversations
- Analytics

No organization can access another organization's data.

---

## Domain Driven Design

Every feature belongs to a domain.

Domains communicate through events.

Domains never depend on each other directly.

---

## API First

Business logic lives inside APIs.

Realtime only delivers events.

Never implement business rules inside websocket handlers.

---

## Event Driven

Every important action should create a domain event.

Examples

ConversationCreated

ConversationAssigned

MessageReceived

MessageSent

IntegrationConnected

CustomerCreated

MentionCreated

Later these events will be used by:

Automation

Analytics

Notifications

AI

---

## AI Ready

AI is NOT part of MVP.

Architecture should allow future AI modules without changing existing code.

Future AI

Conversation Summary

Suggested Replies

Sentiment Analysis

Knowledge Search

Auto Categorization

---

# 4. Product Modules

SparkQuark consists of six business domains.

Identity

Conversation

Integration

Realtime

Notification

Analytics

Every module has a single responsibility.

---

# 5. Identity Domain

Responsible for

Authentication

Organizations

Members

Invitations

Teams

Roles

Permissions

JWT

RBAC

OAuth Login (future)

Never store customer data here.

---

Entities

Organization

Workspace

Member

Role

Permission

Team

Invitation

---

# 6. Conversation Domain

This is the heart of SparkQuark.

Everything customer related belongs here.

Entities

Conversation

Message

Attachment

Mention

Internal Note

Assignment

Label

Draft

There are NO chat rooms.

Everything is conversation based.

---

Conversation lifecycle

Open

Pending

Resolved

Closed

Archived

---

Conversation source

Instagram

Facebook

WhatsApp

Live Chat

Email

Twitter

LinkedIn

Telegram

---

# 7. Customer Domain

A customer should have one unified profile.

Example

Customer

Name

Email

Phone

Instagram

Facebook

WhatsApp

Every communication channel belongs to one customer.

Future CRM features will extend this model.

---

# 8. Integration Domain

Responsible for external providers.

Each provider must be isolated.

Example

Meta

Instagram

Facebook

Messenger

WhatsApp

Each provider must implement the same interface.

Required capabilities

Connect

Disconnect

OAuth

Webhook

Receive Message

Send Message

Download Attachment

Every provider translates external payloads into internal domain models.

Conversation Domain should never know Meta payload formats.

---

Adapters

MetaAdapter

TwitterAdapter

LinkedInAdapter

EmailAdapter

WebChatAdapter

TelegramAdapter

---

# 9. Realtime Domain

Responsible only for websocket communication.

Features

Connection

Presence

Typing Indicator

Read Receipts

Online Status

Realtime Notifications

Broadcast

No database logic.

No business logic.

No validation.

Everything comes from Conversation Domain.

---

# 10. Notification Domain

Responsible for delivering notifications.

Delivery Channels

Email

Push

WebSocket

Webhook

SMS (future)

Notifications should be asynchronous.

---

# 11. Analytics Domain

Responsible for reporting.

Metrics

Response Time

First Response

Average Resolution Time

Open Conversations

Closed Conversations

Agent Performance

Customer Satisfaction (future)

Analytics should never affect production performance.

---

# 12. Workspace Structure

Organization

↓

Workspace

↓

Team

↓

Member

Example

Acme

Support

Support Team

John

---

# 13. Conversation Flow

Customer sends Instagram message

↓

Meta Webhook

↓

Integration Module

↓

Normalize Payload

↓

Conversation Domain

↓

Save Message

↓

Publish Event

↓

Realtime

↓

Dashboard

---

# 14. Internal Collaboration

Every conversation supports

Mentions

Assignments

Labels

Internal Notes

Drafts

Internal Notes are never visible to customers.

---

# 15. RBAC

Roles

Owner

Admin

Manager

Agent

Viewer

Every API endpoint must validate permissions.

Never trust frontend permissions.

---

# 16. Database Collections

organizations

members

roles

permissions

teams

customers

conversations

messages

attachments

internal_notes

mentions

labels

assignments

integrations

oauth_tokens

notifications

events

audit_logs

---

# 17. Folder Structure

sparkquark/

apps/

dashboard/

widget/

admin/

services/

api/

realtime/

packages/

auth/

events/

logger/

config/

types/

utils/

infrastructure/

kubernetes/

terraform/

monitoring/

docs/

scripts/

---

# 18. Coding Standards

Use Clean Architecture.

Business logic belongs to Services.

Controllers must be thin.

Repositories only access database.

Never call MongoDB directly from Controllers.

Never call websocket from Controllers.

Everything should pass through Services.

---

# 19. Design Patterns

Repository Pattern

Service Layer

Adapter Pattern

Dependency Injection

Factory Pattern (Integrations)

Strategy Pattern (Providers)

Observer Pattern (Events)

---

# 20. Security

JWT Authentication

Refresh Tokens

Rate Limiting

Audit Logs

Role Based Authorization

Webhook Signature Validation

Encrypted OAuth Tokens

HTTPS Only

CORS

Secure Cookies (future)

---

# 21. MVP Features

Authentication

Organization Management

Workspace

Members

RBAC

Meta Integration

Instagram Messaging

Facebook Messaging

WhatsApp Business

Live Chat Widget

Conversation Inbox

Realtime Messaging

Mentions

Assignments

Internal Notes

Labels

Attachments

Notifications

Analytics

Audit Logs

---

# 22. Future Roadmap

Twitter

LinkedIn

Telegram

Email

CRM

Automation Engine

AI Module

Marketplace

Public API

Mobile Apps

Voice

Video

Knowledge Base

Chatbots

---

# 23. Non Goals

SparkQuark is NOT

A Discord clone

A Slack clone

A CRM

A Ticket System

SparkQuark is a Customer Communication Platform that can integrate with CRMs and Ticket Systems.

---

# 24. Engineering Rules

One responsibility per module.

Never couple business logic with integrations.

Never expose provider-specific payloads.

Always normalize data.

Every integration is replaceable.

Every module should be independently testable.

Every feature must support multi tenancy.

Every important action creates an event.

Business logic never lives inside websocket handlers.

Controllers stay thin.

Services contain business logic.

Repositories only communicate with MongoDB.

All external APIs must be wrapped by adapters.

Never leak provider implementation details into the domain model.

Architecture must always remain AI-ready even if AI is disabled.