import type { ResponseCookie } from 'next/dist/compiled/@edge-runtime/cookies';

/** Cookie name used for the httpOnly refresh token. */
export const REFRESH_COOKIE = 'bolt_refresh_token';

/** Shared cookie options — imported by every route handler that touches auth. */
export const COOKIE_OPTIONS: Partial<ResponseCookie> = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax',
  path: '/',
  // 7 days — should match backend REFRESH_TOKEN_EXPIRE_DAYS setting
  maxAge: 60 * 60 * 24 * 7,
};
