'use client';

import type React from 'react';
import { useCallback, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { roomsApi } from '@/lib/api';
import { toast } from '@/lib/toast';
import { useAuth } from '@/hooks/useAuth';
import type { Room } from '@/types';

function RoomCard({
  room,
  isMember,
  onJoined,
}: {
  room: Room;
  isMember: boolean;
  onJoined: (room: Room) => void;
}): React.JSX.Element {
  const router = useRouter();
  const [joining, setJoining] = useState(false);

  const handleJoin = useCallback(async (): Promise<void> => {
    setJoining(true);
    try {
      const updated = await roomsApi.join(room.id);
      toast.success(`Joined #${room.name}`);
      onJoined(updated);
      router.push(`/rooms/${room.id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to join');
    } finally {
      setJoining(false);
    }
  }, [room, onJoined, router]);

  return (
    <div className="flex flex-col justify-between rounded-lg border border-zinc-800 bg-zinc-950/60 p-5 transition-colors hover:border-zinc-700">
      <div className="mb-4">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-zinc-700">#</span>
          <h3 className="truncate text-sm font-semibold text-zinc-200">{room.name}</h3>
          {room.is_private && (
            <span className="ml-auto flex-shrink-0 rounded border border-zinc-700 px-1.5 py-0.5 text-[10px] text-zinc-600">
              private
            </span>
          )}
        </div>
        {room.description && (
          <p className="mt-1.5 line-clamp-2 text-xs text-zinc-600">{room.description}</p>
        )}
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono text-zinc-700">
          {room.member_ids.length} {room.member_ids.length === 1 ? 'member' : 'members'}
        </span>
        {isMember ? (
          <Link
            href={`/rooms/${room.id}`}
            className="rounded bg-zinc-800 px-3 py-1 text-xs font-medium text-zinc-300 transition-colors hover:bg-zinc-700"
          >
            Open
          </Link>
        ) : (
          <button
            onClick={handleJoin}
            disabled={joining}
            className="rounded bg-indigo-600 px-3 py-1 text-xs font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
          >
            {joining ? 'Joining…' : 'Join'}
          </button>
        )}
      </div>
    </div>
  );
}

export default function RoomsIndexPage(): React.JSX.Element {
  const { user, isReady } = useAuth();
  const [rooms, setRooms] = useState<Room[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  // Fetch rooms once auth is ready
  useCallback(() => {
    if (!isReady) return;
    roomsApi
      .list()
      .then(setRooms)
      .catch(() => toast.error('Failed to load rooms'))
      .finally(() => setIsLoaded(true));
  }, [isReady])();

  const handleJoined = useCallback((updated: Room): void => {
    setRooms((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
  }, []);

  if (!isLoaded) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-white/20 border-t-white" />
      </div>
    );
  }

  if (rooms.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-2 select-none text-zinc-600">
        <p className="text-sm">No rooms yet</p>
        <p className="text-xs">Create one from the sidebar</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <h2 className="mb-5 text-xs font-bold uppercase tracking-widest text-zinc-600">
        All channels
      </h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {rooms.map((room) => (
          <RoomCard
            key={room.id}
            room={room}
            isMember={user ? room.member_ids.includes(user.id) : false}
            onJoined={handleJoined}
          />
        ))}
      </div>
    </div>
  );
}

