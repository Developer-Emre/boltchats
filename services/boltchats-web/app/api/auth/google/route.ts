import { NextRequest, NextResponse } from 'next/server';
import type { AuthTokens } from '@/types';
import { REFRESH_COOKIE, COOKIE_OPTIONS } from '@/lib/auth-cookies';

const BACKEND_URL =
  process.env.BACKEND_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  'http://localhost:8000/api/v1';

export async function POST(req: NextRequest): Promise<NextResponse> {
  const body = (await req.json()) as { id_token: string };

  const res = await fetch(`${BACKEND_URL}/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = (await res.json().catch(() => ({ detail: 'Google login failed' }))) as {
      detail?: string;
    };
    return NextResponse.json(
      { detail: err.detail ?? 'Google login failed' },
      { status: res.status },
    );
  }

  const data = (await res.json()) as AuthTokens;

  const response = NextResponse.json({
    access_token: data.access_token,
    user: data.user,
  });

  response.cookies.set(REFRESH_COOKIE, data.refresh_token, COOKIE_OPTIONS);
  return response;
}
