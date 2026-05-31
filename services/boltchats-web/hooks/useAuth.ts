'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api';
import { broadcastLogout, subscribeAuthChannel } from '@/lib/auth-channel';
import {
  clearToken,
  getStoredUser,
  getToken,
  setStoredUser,
  setToken,
  type StoredUser,
} from '@/store/auth';

interface UseAuthReturn {
  user: StoredUser | null;
  isLoading: boolean;
  /** True once the session has been initialised (token in memory or refresh attempted). */
  isReady: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<StoredUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  // Cross-tab logout sync: when another tab logs out, mirror the action here.
  useEffect((): (() => void) => {
    return subscribeAuthChannel((): void => {
      clearToken();
      setUser(null);
      router.replace('/login');
    });
  }, [router]);

  // Session init: if the in-memory token was lost (page refresh), restore it
  // by calling /api/auth/refresh — the httpOnly cookie is sent automatically.
  useEffect((): void => {
    if (getToken()) {
      setUser(getStoredUser());
      setIsReady(true);
      return;
    }

    authApi
      .refresh()
      .then((data) => {
        setToken(data.access_token);
        const stored = getStoredUser();
        setUser(stored);
      })
      .catch(() => {
        // No valid session — middleware will redirect on the next navigation.
        // We don't force a redirect here to avoid fighting middleware on public pages.
        clearToken();
      })
      .finally(() => {
        setIsReady(true);
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await authApi.login(email, password);
        setToken(data.access_token);
        setStoredUser(data.user);
        setUser(data.user);
        router.push('/rooms');
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Login failed');
      } finally {
        setIsLoading(false);
      }
    },
    [router],
  );

  const register = useCallback(
    async (username: string, email: string, password: string): Promise<void> => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await authApi.register(username, email, password);
        setToken(data.access_token);
        setStoredUser(data.user);
        setUser(data.user);
        router.push('/rooms');
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Registration failed');
      } finally {
        setIsLoading(false);
      }
    },
    [router],
  );

  const logout = useCallback(async (): Promise<void> => {
    await authApi.logout().catch(() => undefined);
    broadcastLogout(); // notify other open tabs before clearing local state
    clearToken();
    setUser(null);
    router.push('/login');
  }, [router]);

  return { user, isLoading, isReady, error, login, register, logout };
}
