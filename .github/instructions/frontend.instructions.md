---
applyTo: "services/boltchats-web/**"
---
# Frontend Standards — boltchats-web

## Directory Layout
```
src/
├── app/
│   ├── (auth)/         # login, register pages
│   └── (chat)/         # rooms/[roomId] page
├── components/
│   ├── ui/             # Generic reusable UI
│   ├── chat/           # Chat-specific components
│   └── layout/         # Layout components
├── hooks/              # Custom React hooks
├── lib/
│   ├── api.ts          # REST API client — ALL fetch calls go here
│   └── ws.ts           # WebSocket client — ALL WS connections go here
├── store/              # State management
└── types/
    └── index.ts        # All TypeScript type definitions
```

## Hard Rules
- `any` type → **forbidden** — always use explicit types
- `fetch` → **never** called outside `lib/api.ts`
- WebSocket → **never** instantiated outside `lib/ws.ts`
- All shared types defined in `types/index.ts`

## TypeScript Patterns
```typescript
// GOOD — explicit return type
async function getMessages(roomId: string): Promise<Message[]> { ... }

// BAD
async function getMessages(roomId: string) { ... }

// GOOD — type guard
function isApiError(err: unknown): err is ApiError {
  return typeof err === 'object' && err !== null && 'code' in err;
}
```

## API Client Pattern (`lib/api.ts`)
```typescript
// All requests go through this client
const apiClient = {
  get: <T>(path: string): Promise<T> => ...,
  post: <T>(path: string, body: unknown): Promise<T> => ...,
}
export default apiClient;
```

## Stack
- Next.js 16.2.6 App Router
- TypeScript (strict mode)
- Tailwind CSS
- No CSS-in-JS libraries
