'use client';

import { use, useEffect, useState } from 'react';
import { getToken, getStoredUser, type StoredUser } from '@/store/auth';
import { useMessages } from '@/hooks/useMessages';
import { useRoom } from '@/hooks/useRoom';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { RoomHeader } from '@/components/chat/RoomHeader';
import { MemberList } from '@/components/chat/MemberList';

interface PageProps {
  params: Promise<{ roomId: string }>;
}

export default function RoomPage({ params }: PageProps): React.JSX.Element {
  const { roomId } = use(params);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<StoredUser | null>(null);

  useEffect((): void => {
    setToken(getToken());
    setUser(getStoredUser());
  }, []);

  const { room } = useRoom(roomId);
  const { messages, isLoading, connected, sendMessage } = useMessages(
    roomId,
    token,
    user?.id ?? '',
  );

  return (
    <div className="flex h-full">
      <div className="flex flex-1 flex-col overflow-hidden">
        <RoomHeader room={room} roomId={roomId} connected={connected} />
        <MessageList
          messages={messages}
          currentUserId={user?.id ?? ''}
          isLoading={isLoading}
        />
        <MessageInput
          onSend={sendMessage}
          disabled={!connected}
          roomName={room?.name ?? roomId}
        />
      </div>
      <MemberList roomId={roomId} memberIds={room?.member_ids ?? []} />
    </div>
  );
}
