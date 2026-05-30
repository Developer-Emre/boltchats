'use client';

import { use, useEffect, useState } from 'react';
import { getToken, getStoredUser, type StoredUser } from '@/store/auth';
import { useMessages } from '@/hooks/useMessages';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';

interface PageProps {
  params: Promise<{ roomId: string }>;
}

// Connection status indicator
function StatusDot({ connected }: { connected: boolean }): React.JSX.Element {
  return (
    <span className="flex items-center gap-1.5 text-xs font-mono">
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          connected ? 'bg-green-400' : 'bg-zinc-600 animate-pulse'
        }`}
      />
      <span className={connected ? 'text-zinc-500' : 'text-zinc-700'}>
        {connected ? 'live' : 'connecting…'}
      </span>
    </span>
  );
}

export default function RoomPage({ params }: PageProps): React.JSX.Element {
  const { roomId } = use(params);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<StoredUser | null>(null);

  useEffect((): void => {
    setToken(getToken());
    setUser(getStoredUser());
  }, []);

  const { messages, isLoading, connected, sendMessage } = useMessages(
    roomId,
    token,
  );

  return (
    <div className="flex h-full flex-col">
      {/* Room header */}
      <header className="flex h-14 flex-shrink-0 items-center justify-between border-b border-zinc-800 px-4">
        <div className="flex items-center gap-2">
          <span className="text-zinc-600">#</span>
          <h1 className="text-sm font-semibold text-zinc-200">{roomId}</h1>
        </div>
        <StatusDot connected={connected} />
      </header>

      {/* Messages */}
      <MessageList
        messages={messages}
        currentUserId={user?.id ?? ''}
        isLoading={isLoading}
      />

      {/* Input */}
      <MessageInput
        onSend={sendMessage}
        disabled={!connected}
        roomName={roomId}
      />
    </div>
  );
}
