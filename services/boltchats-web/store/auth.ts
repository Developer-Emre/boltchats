// Access token lives in memory only — never persisted to storage.
// On page refresh the chat layout calls /api/auth/refresh (httpOnly cookie)
// to restore it without ever exposing the refresh token to JavaScript.
let _accessToken: string | null = null;

const USER_KEY = 'bolt_user';

export interface StoredUser {
  id: string;
  username: string;
  email: string;
}

export function getToken(): string | null {
  return _accessToken;
}

export function setToken(token: string): void {
  _accessToken = token;
}

export function getRefreshToken(): string | null {
  return null; // refresh token is now in an httpOnly cookie — not accessible from JS
}

export function setRefreshToken(_token: string): void {
  // no-op: refresh token is managed exclusively by Next.js route handlers
}

export function clearToken(): void {
  _accessToken = null;
  if (typeof window !== 'undefined') {
    localStorage.removeItem(USER_KEY);
  }
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredUser;
  } catch {
    return null;
  }
}

export function setStoredUser(user: StoredUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
