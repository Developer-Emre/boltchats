import type {
  AccessTokenResponse,
  Channel,
  DirectMessageGroup,
  Invitation,
  Message,
  OnlineUsers,
  Room,
  RoomPresence,
  SessionResponse,
  UpdateUserPayload,
  User,
  UserPresence,
  Workspace,
} from '@/types';
import { clearToken, getToken, setToken } from '@/store/auth';

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v2';

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

    // 204 No Content has no body
    if (retryRes.status === 204) {
      return null as T;
    }

    return retryRes.json() as Promise<T>;
  }

  if (!res.ok) {
    const body = (await res.json().catch(() => ({ detail: 'Unknown error' }))) as {
      detail?: string;
    };
    throw new ApiError(res.status, body.detail ?? 'Request failed');
  }

  // 204 No Content has no body
  if (res.status === 204) {
    return null as T;
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

  googleLogin: (idToken: string): Promise<SessionResponse> =>
    internalRequest<SessionResponse>('/api/auth/google', {
      method: 'POST',
      body: JSON.stringify({ id_token: idToken }),
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
  get: (roomId: string): Promise<Room> =>
    apiClient.get<Room>(`/rooms/${roomId}`),
  create: (payload: CreateRoomPayload): Promise<Room> =>
    apiClient.post<Room>('/rooms', payload),
  join: (roomId: string): Promise<Room> =>
    apiClient.post<Room>(`/rooms/${roomId}/join`, {}),
  leave: (roomId: string): Promise<void> =>
    apiClient.delete<void>(`/rooms/${roomId}/leave`),
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
  
  listWithCursor: (roomId: string, before?: string): Promise<MessageListResponse> =>
    apiClient.get<MessageListResponse>(
      `/rooms/${roomId}/messages${before ? `?before=${before}` : ''}`
    ),

  edit: (roomId: string, messageId: string, content: string): Promise<Message> =>
    apiClient.patch<Message>(`/rooms/${roomId}/messages/${messageId}`, { content }),

  delete: (roomId: string, messageId: string): Promise<void> =>
    apiClient.delete<void>(`/rooms/${roomId}/messages/${messageId}`),

  addReaction: (roomId: string, messageId: string, emoji: string): Promise<void> =>
    apiClient.post<void>(
      `/rooms/${roomId}/messages/${messageId}/reactions/${encodeURIComponent(emoji)}`,
      {},
    ),

  removeReaction: (roomId: string, messageId: string, emoji: string): Promise<void> =>
    apiClient.delete<void>(
      `/rooms/${roomId}/messages/${messageId}/reactions/${encodeURIComponent(emoji)}`,
    ),
};

export const usersApi = {
  getMe: (): Promise<User> =>
    apiClient.get<User>('/users/me'),
  updateMe: (payload: UpdateUserPayload): Promise<User> =>
    apiClient.patch<User>('/users/me', payload),
  getById: (userId: string): Promise<User> =>
    apiClient.get<User>(`/users/${userId}`),
};

export const presenceApi = {
  getRoom: (roomId: string): Promise<RoomPresence> =>
    apiClient.get<RoomPresence>(`/presence/rooms/${roomId}`),
  getUser: (userId: string): Promise<UserPresence> =>
    apiClient.get<UserPresence>(`/presence/users/${userId}`),
  getOnline: (): Promise<OnlineUsers> =>
    apiClient.get<OnlineUsers>('/presence/online'),
};

// ── V2 API (Discord-like: workspaces, channels, DMs) ───────────────────────

interface ListResponse<T> {
  items: T[];
  next_cursor: string | null;
}

export const workspacesApi = {
  list: (): Promise<Workspace[]> =>
    apiClient.get<ListResponse<Workspace>>('/workspaces').then((res) => res.items),
  
  get: (workspaceId: string): Promise<Workspace> =>
    apiClient.get<Workspace>(`/workspaces/${workspaceId}`),
  
  create: (name: string, description: string): Promise<Workspace> =>
    apiClient.post<Workspace>('/workspaces', { name, description }),
  
  update: (workspaceId: string, name: string, description: string): Promise<Workspace> =>
    apiClient.patch<Workspace>(`/workspaces/${workspaceId}`, { name, description }),
  
  addMember: (workspaceId: string, userId: string, role: string): Promise<Workspace> =>
    apiClient.post<Workspace>(`/workspaces/${workspaceId}/members`, { user_id: userId, role }),
  
  removeMember: (workspaceId: string, userId: string): Promise<void> =>
    apiClient.delete<void>(`/workspaces/${workspaceId}/members/${userId}`),
  
  updateMemberRole: (workspaceId: string, userId: string, role: string): Promise<Workspace> =>
    apiClient.patch<Workspace>(`/workspaces/${workspaceId}/members/${userId}`, { role }),
};

export const channelsApi = {
  list: (workspaceId: string): Promise<Channel[]> =>
    apiClient
      .get<ListResponse<Channel>>(`/workspaces/${workspaceId}/channels`)
      .then((res) => res.items),
  
  get: (workspaceId: string, channelId: string): Promise<Channel> =>
    apiClient.get<Channel>(`/workspaces/${workspaceId}/channels/${channelId}`),
  
  create: (
    workspaceId: string,
    name: string,
    description: string,
    type: 'public' | 'private' = 'public',
  ): Promise<Channel> =>
    apiClient.post<Channel>(`/workspaces/${workspaceId}/channels`, {
      name,
      description,
      type,
    }),
  
  update: (
    workspaceId: string,
    channelId: string,
    name: string,
    description: string,
  ): Promise<Channel> =>
    apiClient.patch<Channel>(`/workspaces/${workspaceId}/channels/${channelId}`, {
      name,
      description,
    }),
  
  archive: (workspaceId: string, channelId: string): Promise<Channel> =>
    apiClient.post<Channel>(
      `/workspaces/${workspaceId}/channels/${channelId}/archive`,
      {},
    ),
  
  unarchive: (workspaceId: string, channelId: string): Promise<Channel> =>
    apiClient.post<Channel>(
      `/workspaces/${workspaceId}/channels/${channelId}/unarchive`,
      {},
    ),
  
  addMember: (
    workspaceId: string,
    channelId: string,
    userId: string,
  ): Promise<Channel> =>
    apiClient.post<Channel>(
      `/workspaces/${workspaceId}/channels/${channelId}/members`,
      { user_id: userId },
    ),
  
  removeMember: (
    workspaceId: string,
    channelId: string,
    userId: string,
  ): Promise<void> =>
    apiClient.delete<void>(
      `/workspaces/${workspaceId}/channels/${channelId}/members/${userId}`,
    ),
};

export const directMessagesApi = {
  list: (workspaceId: string): Promise<DirectMessageGroup[]> =>
    apiClient
      .get<ListResponse<DirectMessageGroup>>(`/workspaces/${workspaceId}/dms`)
      .then((res) => res.items),
  
  get: (workspaceId: string, dmId: string): Promise<DirectMessageGroup> =>
    apiClient.get<DirectMessageGroup>(`/workspaces/${workspaceId}/dms/${dmId}`),
  
  create: (workspaceId: string, participantIds: string[]): Promise<DirectMessageGroup> =>
    apiClient.post<DirectMessageGroup>(`/workspaces/${workspaceId}/dms`, {
      participant_ids: participantIds,
    }),
};

export const invitationsApi = {
  create: (
    workspaceId: string,
    invitedEmail: string,
    role: string,
  ): Promise<Invitation> =>
    apiClient.post<Invitation>(`/workspaces/${workspaceId}/invitations`, {
      invited_email: invitedEmail,
      role,
    }),
  
  list: (workspaceId: string): Promise<Invitation[]> =>
    apiClient
      .get<ListResponse<Invitation>>(`/workspaces/${workspaceId}/invitations`)
      .then((res) => res.items),
  
  accept: (workspaceId: string, invitationCode: string): Promise<Workspace> =>
    apiClient.post<Workspace>(
      `/workspaces/${workspaceId}/invitations/${invitationCode}/accept`,
      {},
    ),
  
  decline: (workspaceId: string, invitationCode: string): Promise<void> =>
    apiClient.post<void>(
      `/workspaces/${workspaceId}/invitations/${invitationCode}/decline`,
      {},
    ),
  
  revoke: (workspaceId: string, invitationId: string): Promise<void> =>
    apiClient.delete<void>(
      `/workspaces/${workspaceId}/invitations/${invitationId}`,
    ),
};

// V2 Message API (per channel/DM)
export const channelMessagesApi = {
  list: (workspaceId: string, channelId: string): Promise<Message[]> =>
    apiClient
      .get<ListResponse<Message>>(
        `/workspaces/${workspaceId}/channels/${channelId}/messages`,
      )
      .then((res) => res.items),
  
  listWithCursor: (
    workspaceId: string,
    channelId: string,
    before?: string,
  ): Promise<ListResponse<Message>> =>
    apiClient.get<ListResponse<Message>>(
      `/workspaces/${workspaceId}/channels/${channelId}/messages${before ? `?before=${before}` : ''}`,
    ),
  
  create: (workspaceId: string, channelId: string, content: string): Promise<Message> =>
    apiClient.post<Message>(
      `/workspaces/${workspaceId}/channels/${channelId}/messages`,
      { content },
    ),
  
  edit: (
    workspaceId: string,
    channelId: string,
    messageId: string,
    content: string,
  ): Promise<Message> =>
    apiClient.patch<Message>(
      `/workspaces/${workspaceId}/channels/${channelId}/messages/${messageId}`,
      { content },
    ),
  
  delete: (workspaceId: string, channelId: string, messageId: string): Promise<void> =>
    apiClient.delete<void>(
      `/workspaces/${workspaceId}/channels/${channelId}/messages/${messageId}`,
    ),
};

export const dmMessagesApi = {
  list: (workspaceId: string, dmId: string): Promise<Message[]> =>
    apiClient
      .get<ListResponse<Message>>(`/workspaces/${workspaceId}/dms/${dmId}/messages`)
      .then((res) => res.items),
  
  listWithCursor: (
    workspaceId: string,
    dmId: string,
    before?: string,
  ): Promise<ListResponse<Message>> =>
    apiClient.get<ListResponse<Message>>(
      `/workspaces/${workspaceId}/dms/${dmId}/messages${before ? `?before=${before}` : ''}`,
    ),
  
  create: (workspaceId: string, dmId: string, content: string): Promise<Message> =>
    apiClient.post<Message>(
      `/workspaces/${workspaceId}/dms/${dmId}/messages`,
      { content },
    ),
  
  edit: (
    workspaceId: string,
    dmId: string,
    messageId: string,
    content: string,
  ): Promise<Message> =>
    apiClient.patch<Message>(
      `/workspaces/${workspaceId}/dms/${dmId}/messages/${messageId}`,
      { content },
    ),
  
  delete: (workspaceId: string, dmId: string, messageId: string): Promise<void> =>
    apiClient.delete<void>(
      `/workspaces/${workspaceId}/dms/${dmId}/messages/${messageId}`,
    ),
};

export default apiClient;
