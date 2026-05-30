'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { roomsApi } from '@/lib/api';
import { getToken, getStoredUser } from '@/store/auth';
import type { Room } from '@/types';
import { RoomSidebar } from '@/components/chat/RoomSidebar';
import { CreateRoomModal } from '@/components/chat/CreateRoomModal';
import { useAuth } from '@/hooks/useAuth';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}): React.JSX.Element {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [username, setUsername] = useState('anonymous');
  const router = useRouter();
  const { logout } = useAuth();

  // Guard — redirect if not authenticated
  useEffect((): void => {
    if (!getToken()) {
      router.replace('/login');
    }
  }, [router]);

  // Resolve username client-side only — avoids SSR/client mismatch
  useEffect((): void => {
    const user = getStoredUser();
    setUsername(user?.username ?? user?.email ?? 'anonymous');
  }, []);

  const fetchRooms = useCallback((): void => {
    roomsApi
      .list()
      .then(setRooms)
      .catch((): void => setRooms([]));
  }, []);

  useEffect((): void => {
    fetchRooms();
  }, [fetchRooms]);

  const handleRoomCreated = useCallback(
    (room: Room): void => {
      setRooms((prev) => [...prev, room]);
      setShowModal(false);
      router.push(`/rooms/${room.id}`);
    },
    [router],
  );

  return (
    <div className="flex h-screen overflow-hidden bg-[#111113]">
      <RoomSidebar
        rooms={rooms}
        onLogout={logout}
        onCreateRoom={() => setShowModal(true)}
        username={username}
      />
      <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
      {showModal && (
        <CreateRoomModal
          onClose={() => setShowModal(false)}
          onCreated={handleRoomCreated}
        />
      )}
    </div>
  );
}
