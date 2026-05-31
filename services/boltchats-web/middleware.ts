import { NextRequest, NextResponse } from 'next/server';
import { REFRESH_COOKIE } from '@/lib/auth-cookies';

const PROTECTED_PREFIXES = ['/rooms'];
const PUBLIC_PATHS = new Set(['/login', '/register']);

export function middleware(req: NextRequest): NextResponse {
  const { pathname } = req.nextUrl;
  const hasSession = req.cookies.has(REFRESH_COOKIE);

  const isProtected = PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));
  const isPublic = PUBLIC_PATHS.has(pathname);

  // Unauthenticated user hitting a protected route → login
  if (isProtected && !hasSession) {
    return NextResponse.redirect(new URL('/login', req.url));
  }

  // Authenticated user hitting a public auth page → rooms (already logged in)
  if (isPublic && hasSession) {
    return NextResponse.redirect(new URL('/rooms', req.url));
  }

  return NextResponse.next();
}

export const config = {
  // Run on all routes except Next.js internals and static assets
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
