'use client';

import { useEffect, useState } from 'react';
import { presenceApi } from '@/lib/api';
import type { OnlineUsers, RoomPresence, UserPresence } from '@/types';

interface UseRoomPresenceReturn {
  presence: RoomPresence | null;
  isLoading: boolean;
}

/** Fetches room presence on mount. Re-fetches whenever roomId changes. */
export function useRoomPresence(roomId: string): UseRoomPresenceReturn {
  const [presence, setPresence] = useState<RoomPresence | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect((): void => {
    setIsLoading(true);
    presenceApi
      .getRoom(roomId)
      .then(setPresence)
      .catch(() => setPresence(null))
      .finally(() => setIsLoading(false));
  }, [roomId]);

  return { presence, isLoading };
}

interface UseUserPresenceReturn {
  presence: UserPresence | null;
  isLoading: boolean;
}

/** Returns online/offline status for a single user. */
export function useUserPresence(userId: string): UseUserPresenceReturn {
  const [presence, setPresence] = useState<UserPresence | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect((): void => {
    setIsLoading(true);
    presenceApi
      .getUser(userId)
      .then(setPresence)
      .catch(() => setPresence(null))
      .finally(() => setIsLoading(false));
  }, [userId]);

  return { presence, isLoading };
}

interface UseOnlineUsersReturn {
  online: OnlineUsers | null;
  isLoading: boolean;
}

/** Returns the global online user list. */
export function useOnlineUsers(): UseOnlineUsersReturn {
  const [online, setOnline] = useState<OnlineUsers | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect((): void => {
    presenceApi
      .getOnline()
      .then(setOnline)
      .catch(() => setOnline(null))
      .finally(() => setIsLoading(false));
  }, []);

  return { online, isLoading };
}
