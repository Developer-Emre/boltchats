'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api';
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
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<StoredUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect((): void => {
    const stored = getStoredUser();
    const token = getToken();
    if (stored && token) setUser(stored);
  }, []);

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

  const logout = useCallback((): void => {
    clearToken();
    setUser(null);
    router.push('/login');
  }, [router]);

  return { user, isLoading, error, login, register, logout };
}
