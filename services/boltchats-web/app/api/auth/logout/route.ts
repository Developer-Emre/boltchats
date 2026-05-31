import { NextRequest, NextResponse } from 'next/server';
import { REFRESH_COOKIE } from '@/lib/auth-cookies';

const BACKEND_URL =
  process.env.BACKEND_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  'http://localhost:8000/api/v1';

export async function POST(req: NextRequest): Promise<NextResponse> {
  const refreshToken = req.cookies.get(REFRESH_COOKIE)?.value;

  // Best-effort: tell the backend to invalidate the refresh token in Redis.
  // We proceed with logout even if the backend call fails.
  if (refreshToken) {
    await fetch(`${BACKEND_URL}/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    }).catch(() => undefined);
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.delete(REFRESH_COOKIE);
  return response;
}
