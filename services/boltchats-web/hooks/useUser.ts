'use client';

import { useCallback, useEffect, useState } from 'react';
import { usersApi } from '@/lib/api';
import type { UpdateUserPayload, User } from '@/types';

interface UseUserReturn {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  updateMe: (payload: UpdateUserPayload) => Promise<void>;
}

/** Fetches the current authenticated user's profile and exposes an update fn. */
export function useUser(): UseUserReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect((): void => {
    usersApi
      .getMe()
      .then(setUser)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load user');
      })
      .finally(() => setIsLoading(false));
  }, []);

  const updateMe = useCallback(async (payload: UpdateUserPayload): Promise<void> => {
    const updated = await usersApi.updateMe(payload);
    setUser(updated);
  }, []);

  return { user, isLoading, error, updateMe };
}

interface UseUserByIdReturn {
  user: User | null;
  isLoading: boolean;
  error: string | null;
}

/** Fetches any user's public profile by id. */
export function useUserById(userId: string): UseUserByIdReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect((): void => {
    setIsLoading(true);
    setError(null);
    usersApi
      .getById(userId)
      .then(setUser)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load user');
      })
      .finally(() => setIsLoading(false));
  }, [userId]);

  return { user, isLoading, error };
}
