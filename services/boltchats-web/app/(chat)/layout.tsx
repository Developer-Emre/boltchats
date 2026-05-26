'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { roomsApi } from '@/lib/api';
import { getToken, getStoredUser } from '@/store/auth';
import type { Room } from '@/types';
import { RoomSidebar } from '@/components/chat/RoomSidebar';
import { useAuth } from '@/hooks/useAuth';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}): React.JSX.Element {
  const [rooms, setRooms] = useState<Room[]>([]);
  const router = useRouter();
  const { logout } = useAuth();

  // Guard — redirect if not authenticated
  useEffect((): void => {
    if (!getToken()) {
      router.replace('/login');
    }
  }, [router]);

  useEffect((): void => {
    roomsApi
      .list()
      .then(setRooms)
      .catch((): void => setRooms([]));
  }, []);

  const user = getStoredUser();
  const username = user?.username ?? user?.email ?? 'anonymous';

  return (
    <div className="flex h-screen overflow-hidden bg-[#111113]">
      <RoomSidebar rooms={rooms} onLogout={logout} username={username} />
      <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
    </div>
  );
}
