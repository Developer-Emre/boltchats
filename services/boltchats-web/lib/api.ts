import type { AccessTokenResponse, AuthTokens, Message, Room } from '@/types';
import {
  clearToken,
  getRefreshToken,
  getToken,
  setRefreshToken,
  setToken,
} from '@/store/auth';

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

// Singleton promise — prevents multiple simultaneous refresh calls when
// several requests 401 at the same time (only one refresh races to the server).
let refreshPromise: Promise<string> | null = null;

async function attemptTokenRefresh(): Promise<string> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async (): Promise<string> => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) throw new ApiError(401, 'No refresh token');

    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      clearToken();
      if (typeof window !== 'undefined') window.location.href = '/login';
      throw new ApiError(401, 'Session expired');
    }

    const data = (await res.json()) as AccessTokenResponse;
    setToken(data.access_token);
    return data.access_token;
  })().finally(() => {
    refreshPromise = null;
  });

  return refreshPromise;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  // Auto-refresh on 401 — retry the original request once with the new token
  if (res.status === 401) {
    const newToken = await attemptTokenRefresh();
    const retryRes = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: { ...headers, Authorization: `Bearer ${newToken}` },
    });

    if (!retryRes.ok) {
      const body = await retryRes
        .json()
        .catch(() => ({ detail: 'Unknown error' })) as { detail?: string };
      throw new ApiError(retryRes.status, body.detail ?? 'Request failed');
    }

    return retryRes.json() as Promise<T>;
  }

  if (!res.ok) {
    const body = await res
      .json()
      .catch(() => ({ detail: 'Unknown error' })) as { detail?: string };
    throw new ApiError(res.status, body.detail ?? 'Request failed');
  }

  return res.json() as Promise<T>;
}

const apiClient = {
  get: <T>(path: string): Promise<T> =>
    request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string): Promise<T> =>
    request<T>(path, { method: 'DELETE' }),
};

export const authApi = {
  login: (email: string, password: string): Promise<AuthTokens> =>
    apiClient.post<AuthTokens>('/auth/login', { email, password }),

  register: (
    username: string,
    email: string,
    password: string,
  ): Promise<AuthTokens> =>
    apiClient.post<AuthTokens>('/auth/register', { username, email, password }),

  refresh: (refreshToken: string): Promise<AccessTokenResponse> =>
    apiClient.post<AccessTokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    }),

  // Backend requires the refresh_token in the body to invalidate it in Redis
  logout: (): Promise<void> => {
    const refreshToken = getRefreshToken();
    return apiClient.post<void>('/auth/logout', { refresh_token: refreshToken ?? '' });
  },
};

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
