'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { roomsApi } from '@/lib/api';
import type { Room } from '@/types';
import { RoomSidebar } from '@/components/chat/RoomSidebar';
import { CreateRoomModal } from '@/components/chat/CreateRoomModal';
import { Toaster } from '@/components/ui/Toaster';
import { useAuth } from '@/hooks/useAuth';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}): React.JSX.Element {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [showModal, setShowModal] = useState(false);
  const router = useRouter();
  // isReady: session initialised (token in memory or refresh attempted)
  // user: populated once session is ready — drives the sidebar username
  const { user, isReady, logout } = useAuth();

  const fetchRooms = useCallback((): void => {
    roomsApi
      .list()
      .then(setRooms)
      .catch((): void => setRooms([]));
  }, []);

  // Wait for session init before fetching rooms — avoids a 401 on the first render
  useEffect((): void => {
    if (isReady) fetchRooms();
  }, [isReady, fetchRooms]);

  const handleRoomCreated = useCallback(
    (room: Room): void => {
      setRooms((prev) => [...prev, room]);
      setShowModal(false);
      router.push(`/rooms/${room.id}`);
    },
    [router],
  );

  // Show a minimal spinner while the session is being restored (page refresh case).
  // Middleware has already confirmed a refresh cookie exists, so this is brief.
  if (!isReady) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#111113]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-white/20 border-t-white" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#111113]">
      <RoomSidebar
        rooms={rooms}
        onLogout={logout}
        onCreateRoom={() => setShowModal(true)}
        username={user?.username ?? user?.email ?? 'anonymous'}
      />
      <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
      <Toaster />
      {showModal && (
        <CreateRoomModal
          onClose={() => setShowModal(false)}
          onCreated={handleRoomCreated}
        />
      )}
    </div>
  );
}
