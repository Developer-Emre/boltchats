import type { AccessTokenResponse, Message, Room, SessionResponse } from '@/types';
import { clearToken, getToken, setToken } from '@/store/auth';

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

// ── Internal request (Next.js route handlers) ─────────────────────────────────
// No Authorization header — auth routes rely on httpOnly cookies.
// No 401 retry — would cause infinite loops.

async function internalRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init.headers as Record<string, string>) },
  });

  if (!res.ok) {
    const body = (await res.json().catch(() => ({ detail: 'Unknown error' }))) as {
      detail?: string;
    };
    throw new ApiError(res.status, body.detail ?? 'Request failed');
  }

  return res.json() as Promise<T>;
}

// ── Singleton refresh guard ───────────────────────────────────────────────────
// Prevents multiple simultaneous 401s from each firing their own refresh call.

let refreshPromise: Promise<string> | null = null;

async function attemptTokenRefresh(): Promise<string> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = internalRequest<AccessTokenResponse>('/api/auth/refresh', {
    method: 'POST',
  })
    .then((data) => {
      setToken(data.access_token);
      return data.access_token;
    })
    .catch((err: unknown) => {
      clearToken();
      if (typeof window !== 'undefined') window.location.href = '/login';
      throw err;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

// ── Backend request (FastAPI) ─────────────────────────────────────────────────

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    const newToken = await attemptTokenRefresh();
    const retryRes = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: { ...headers, Authorization: `Bearer ${newToken}` },
    });

    if (!retryRes.ok) {
      const body = (await retryRes.json().catch(() => ({ detail: 'Unknown error' }))) as {
        detail?: string;
      };
      throw new ApiError(retryRes.status, body.detail ?? 'Request failed');
    }

    return retryRes.json() as Promise<T>;
  }

  if (!res.ok) {
    const body = (await res.json().catch(() => ({ detail: 'Unknown error' }))) as {
      detail?: string;
    };
    throw new ApiError(res.status, body.detail ?? 'Request failed');
  }

  return res.json() as Promise<T>;
}

const apiClient = {
  get: <T>(path: string): Promise<T> => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string): Promise<T> => request<T>(path, { method: 'DELETE' }),
};

// ── Auth API (calls Next.js route handlers, not the backend directly) ─────────

export const authApi = {
  login: (email: string, password: string): Promise<SessionResponse> =>
    internalRequest<SessionResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (username: string, email: string, password: string): Promise<SessionResponse> =>
    internalRequest<SessionResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    }),

  // Reads httpOnly cookie — no body needed
  refresh: (): Promise<AccessTokenResponse> =>
    internalRequest<AccessTokenResponse>('/api/auth/refresh', { method: 'POST' }),

  // Route handler reads the cookie and calls backend with the refresh token
  logout: (): Promise<void> =>
    internalRequest<void>('/api/auth/logout', { method: 'POST' }),
};

// ── Domain APIs ───────────────────────────────────────────────────────────────

interface RoomListResponse {
  items: Room[];
  next_cursor: string | null;
}

export interface CreateRoomPayload {
  name: string;
  description: string;
  is_private: boolean;
}

export const roomsApi = {
  list: (): Promise<Room[]> =>
    apiClient.get<RoomListResponse>('/rooms').then((res) => res.items),
  create: (payload: CreateRoomPayload): Promise<Room> =>
    apiClient.post<Room>('/rooms', payload),
};

interface MessageListResponse {
  items: Message[];
  next_cursor: string | null;
}

export const messagesApi = {
  list: (roomId: string): Promise<Message[]> =>
    apiClient
      .get<MessageListResponse>(`/rooms/${roomId}/messages`)
      .then((res) => res.items),
};

export default apiClient;
