import { NextRequest, NextResponse } from 'next/server';
import type { AccessTokenResponse } from '@/types';
import { REFRESH_COOKIE, COOKIE_OPTIONS } from '@/lib/auth-cookies';

const BACKEND_URL =
  process.env.BACKEND_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  'http://localhost:8000/api/v1';

export async function POST(req: NextRequest): Promise<NextResponse> {
  const refreshToken = req.cookies.get(REFRESH_COOKIE)?.value;

  if (!refreshToken) {
    return NextResponse.json({ detail: 'No session' }, { status: 401 });
  }

  const res = await fetch(`${BACKEND_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    // Refresh token expired or revoked — clear the cookie so middleware
    // redirects the user to /login on the next navigation.
    const response = NextResponse.json({ detail: 'Session expired' }, { status: 401 });
    response.cookies.delete(REFRESH_COOKIE);
    return response;
  }

  const data = (await res.json()) as AccessTokenResponse;

  // Rotate cookie TTL on every successful refresh
  const response = NextResponse.json({ access_token: data.access_token });
  response.cookies.set(REFRESH_COOKIE, refreshToken, COOKIE_OPTIONS);
  return response;
}
