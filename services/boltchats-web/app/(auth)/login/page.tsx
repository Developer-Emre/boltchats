'use client';

import Link from 'next/link';
import { type FormEvent, useState } from 'react';
import { GoogleLogin, type CredentialResponse } from '@react-oauth/google';
import { Logo } from '@/components/ui/Logo';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';

export default function LoginPage(): React.JSX.Element {
  const { login, googleLogin, isLoading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    await login(email, password);
  };

  const handleGoogleSuccess = async (response: CredentialResponse): Promise<void> => {
    if (response.credential) {
      await googleLogin(response.credential);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-[#0c0c0e] px-4">
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        <div className="absolute -top-40 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-indigo-600/8 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-64 w-64 rounded-full bg-indigo-900/10 blur-3xl" />
      </div>

      {/* Grid overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            'linear-gradient(to right, #818cf8 1px, transparent 1px), linear-gradient(to bottom, #818cf8 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
        aria-hidden
      />

      <div className="relative z-10 w-full max-w-sm">
        {/* Card */}
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/80 p-8 shadow-2xl backdrop-blur-sm">
          <div className="mb-8 flex flex-col items-center gap-2">
            <Logo size="lg" />
            <p className="text-[11px] font-mono tracking-widest text-zinc-600 uppercase">
              fast · simple · yours
            </p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />

            {error && (
              <p className="rounded border border-red-800/50 bg-red-950/30 px-3 py-2 text-xs text-red-400">
                {error}
              </p>
            )}

            <Button
              type="submit"
              isLoading={isLoading}
              className="mt-2 w-full"
            >
              Sign in
            </Button>
          </form>

          {/* Divider */}
          <div className="my-5 flex items-center gap-3">
            <div className="h-px flex-1 bg-zinc-800" />
            <span className="text-[11px] font-mono text-zinc-600 uppercase">or</span>
            <div className="h-px flex-1 bg-zinc-800" />
          </div>

          {/* Google button */}
          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => undefined}
              theme="filled_black"
              shape="rectangular"
              size="large"
              width="100%"
            />
          </div>

          <p className="mt-6 text-center text-xs text-zinc-700">
            No account?{' '}
            <Link
              href="/register"
              className="text-indigo-400 transition-colors hover:text-indigo-300"
            >
              Create one
            </Link>
          </p>
        </div>

        {/* Decorative corner accent */}
        <div className="absolute -bottom-px left-8 right-8 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />
      </div>
    </div>
  );
}
