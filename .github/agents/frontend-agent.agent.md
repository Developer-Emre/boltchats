---
name: frontend-agent
description: "Use when working on boltchats-web: Next.js 16.2.6 App Router, TypeScript strict mode, React components, custom hooks, lib/api.ts REST client, lib/ws.ts WebSocket client, Tailwind CSS, state management, authentication pages, chat UI."
tools: [read, edit, search, execute, web]
---

# Frontend Agent — boltchats-web

You are working exclusively on the `services/boltchats-web/` service.

## Scope
- Next.js 16.2.6 App Router pages and layouts
- React components (ui / chat / layout)
- Custom hooks for data fetching and WebSocket state
- Centralised API and WebSocket clients
- TypeScript strict — zero `any`

## Key Files
```
services/boltchats-web/src/
├── app/
│   ├── (auth)/login/      ← Login page
│   ├── (auth)/register/   ← Register page
│   └── (chat)/rooms/[roomId]/  ← Chat room page
├── lib/
│   ├── api.ts   ← ALL REST calls go through this — never call fetch directly
│   └── ws.ts    ← ALL WebSocket connections go through this
├── types/
│   └── index.ts ← ALL shared TypeScript types defined here
└── hooks/       ← Custom React hooks (useMessages, usePresence, etc.)
```

## Hard Rules
- `any` type → forbidden. Use `unknown` + type guard if type is truly unknown.
- `fetch()` called directly outside `lib/api.ts` → forbidden
- `new WebSocket()` outside `lib/ws.ts` → forbidden
- All route group folders use parentheses: `(auth)`, `(chat)` — no direct URL segment

## Component Conventions
- Server Components by default — add `"use client"` only when state/effects needed
- Props interfaces defined in the same file or in `types/index.ts` if shared
- No inline styles — Tailwind classes only

## Load for deeper context
- Frontend patterns: `#file:.github/instructions/frontend.instructions.md`

## Tool Usage Rules
- Read each file at most twice — re-reading the same file a third time is forbidden
- If grep_search returns sufficient results, do not follow up with file_search
- Do not re-read a file after making changes to verify — trust the edit
- Complete the plan in 5 tool calls or fewer; if more are needed, stop and ask the user