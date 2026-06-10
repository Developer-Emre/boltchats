'use client';

import { use, useCallback, useEffect, useState } from 'react';
import { getToken, getStoredUser, type StoredUser } from '@/store/auth';
import { useMessages } from '@/hooks/useMessages';
import { useRoom } from '@/hooks/useRoom';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { RoomHeader } from '@/components/chat/RoomHeader';
import { MemberList } from '@/components/chat/MemberList';
import { ApiError } from '@/lib/api';

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

  const { room, join, leave, error: roomError } = useRoom(roomId);
  const { messages, isLoading, isLoadingMore, hasMore, connected, sendMessage, loadOlderMessages, editMessage, deleteMessage, addReaction, removeReaction } = useMessages(
    roomId,
    token,
    user?.id ?? '',
  );

  const isMember = user ? (room?.member_ids.includes(user.id) ?? false) : false;
  const isOwner = user ? room?.owner_id === user.id : false;

  const [actionError, setActionError] = useState<string | null>(null);

  const handleJoin = useCallback(async (): Promise<void> => {
    setActionError(null);
    try {
      await join();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.detail : 'Failed to join');
    }
  }, [join]);

  const handleLeave = useCallback(async (): Promise<void> => {
    setActionError(null);
    try {
      await leave();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.detail : 'Failed to leave');
    }
  }, [leave]);

  return (
    <div className="flex h-full">
      <div className="flex flex-1 flex-col overflow-hidden">
        <RoomHeader room={room} roomId={roomId} connected={connected} />

        {/* Join / Leave banner for non-members */}
        {room && !isMember && (
          <div className="flex items-center justify-between border-b border-zinc-800 bg-indigo-950/30 px-4 py-2">
            <p className="text-xs text-zinc-400">
              You are not a member of this room.
            </p>
            <button
              onClick={handleJoin}
              className="rounded bg-indigo-600 px-3 py-1 text-xs font-semibold text-white transition-colors hover:bg-indigo-500"
            >
              Join
            </button>
          </div>
        )}

        {actionError && (
          <p className="border-b border-red-800/40 bg-red-950/20 px-4 py-1.5 text-xs text-red-400">
            {actionError}
          </p>
        )}

        {roomError && (
          <div className="flex flex-1 items-center justify-center text-zinc-600 text-sm">
            {roomError}
          </div>
        )}

        {!roomError && (
          <>
            <MessageList
              messages={messages}
              currentUserId={user?.id ?? ''}
              isLoading={isLoading}
              isLoadingMore={isLoadingMore}
              hasMore={hasMore}
              onLoadOlder={loadOlderMessages}
              onEditMessage={editMessage}
              onDeleteMessage={deleteMessage}
              onAddReaction={addReaction}
              onRemoveReaction={removeReaction}
            />
            <div className="relative">
              {isMember && !isOwner && (
                <button
                  onClick={handleLeave}
                  className="absolute right-4 -top-7 text-[11px] text-zinc-700 hover:text-red-400 transition-colors"
                >
                  Leave room
                </button>
              )}
              <MessageInput
                onSend={sendMessage}
                disabled={!connected || !isMember}
                roomName={room?.name ?? roomId}
              />
            </div>
          </>
        )}
      </div>
      <MemberList roomId={roomId} memberIds={room?.member_ids ?? []} />
    </div>
  );
}
