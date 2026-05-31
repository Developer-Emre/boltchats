'use client';

import { useCallback, useEffect, useState } from 'react';
import { roomsApi } from '@/lib/api';
import type { Room } from '@/types';

interface UseRoomReturn {
  room: Room | null;
  isLoading: boolean;
  error: string | null;
  join: () => Promise<void>;
  leave: () => Promise<void>;
}

export function useRoom(roomId: string): UseRoomReturn {
  const [room, setRoom] = useState<Room | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect((): void => {
    setIsLoading(true);
    setError(null);
    roomsApi
      .get(roomId)
      .then(setRoom)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load room');
      })
      .finally(() => setIsLoading(false));
  }, [roomId]);

  const join = useCallback(async (): Promise<void> => {
    const updated = await roomsApi.join(roomId);
    setRoom(updated);
  }, [roomId]);

  const leave = useCallback(async (): Promise<void> => {
    await roomsApi.leave(roomId);
    setRoom((prev) =>
      prev ? { ...prev, member_ids: prev.member_ids.filter((id) => id !== prev.owner_id) } : prev,
    );
  }, [roomId]);

  return { room, isLoading, error, join, leave };
}
