import type { AuthTokens, Message, Room } from '@/types';
import { getToken } from '@/store/auth';

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

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

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

  logout: (): Promise<void> => apiClient.post<void>('/auth/logout', {}),
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
