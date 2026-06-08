'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { messagesApi } from '@/lib/api';
import type { Message, WsEvent } from '@/types';
import { useWebSocket } from '@/hooks/useWebSocket';

interface UseMessagesReturn {
  messages: Message[];
  isLoading: boolean;
  isLoadingMore: boolean;
  hasMore: boolean;
  connected: boolean;
  sendMessage: (content: string) => void;
  loadOlderMessages: () => void;
  editMessage: (messageId: string, content: string) => Promise<void>;
  deleteMessage: (messageId: string) => Promise<void>;
}

export function useMessages(
  roomId: string,
  token: string | null,
  currentUserId: string,
): UseMessagesReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const joinedRef = useRef(false);

  // Keep roomId in a ref so the WS event handler never closes over a stale value
  const roomIdRef = useRef(roomId);
  roomIdRef.current = roomId;

  const handleEvent = useCallback((event: WsEvent): void => {
    // Delivery receipt for our own optimistic message — swap placeholder id
    // with the authoritative server id. Never goes to other room members.
    if (event.type === 'message_confirmed') {
      setMessages((prev) =>
        prev.map((m) => (m.id === event.client_message_id ? { ...m, id: event.server_id } : m)),
      );
      return;
    }

    if (event.type === 'message_edited' && event.room_id === roomIdRef.current) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === event.message_id
            ? { ...m, content: event.content, edited_at: event.edited_at }
            : m,
        ),
      );
      return;
    }

    if (event.type === 'message_deleted' && event.room_id === roomIdRef.current) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === event.message_id
            ? { ...m, deleted_at: event.deleted_at, is_deleted: true }
            : m,
        ),
      );
      return;
    }

    if (event.type !== 'message' || event.room_id !== roomIdRef.current) return;

    setMessages((prev) => {
      // Guard against duplicate delivery (e.g. reconnect replays)
      if (prev.some((m) => m.id === event.id)) return prev;
      return [...prev, event as Message];
    });
  }, []);

  const { connected, send } = useWebSocket(token, handleEvent);

  // Fetch message history whenever the room changes
  useEffect((): void => {
    setIsLoading(true);
    setMessages([]);
    setNextCursor(null);
    setHasMore(false);
    
    (async (): Promise<void> => {
      try {
        const response = await (messagesApi as any).listWithCursor(roomId);
        setMessages(response.items);
        setNextCursor(response.next_cursor);
        setHasMore(response.next_cursor !== null);
      } catch {
        setMessages([]);
        setNextCursor(null);
        setHasMore(false);
      } finally {
        setIsLoading(false);
      }
    })();
  }, [roomId]);

  // Join room once WS connects; reset on disconnect so we re-join after reconnect
  useEffect((): void => {
    if (connected && !joinedRef.current) {
      send({ type: 'join_room', room_id: roomId });
      joinedRef.current = true;
    }
    if (!connected) {
      joinedRef.current = false;
    }
  }, [connected, roomId, send]);

  const loadOlderMessages = useCallback((): void => {
    if (isLoadingMore || !hasMore || !nextCursor) return;

    setIsLoadingMore(true);
    (async (): Promise<void> => {
      try {
        const response = await (messagesApi as any).listWithCursor(roomId, nextCursor);
        setMessages((prev) => [...response.items, ...prev]);
        setNextCursor(response.next_cursor);
        setHasMore(response.next_cursor !== null);
      } catch {
        // Silently fail — user can retry
      } finally {
        setIsLoadingMore(false);
      }
    })();
  }, [roomId, isLoadingMore, hasMore, nextCursor]);

  const sendMessage = useCallback(
    (content: string): void => {
      const trimmed = content.trim();
      if (!trimmed) return;

      const clientMessageId = crypto.randomUUID();

      setMessages((prev) => [
        ...prev,
        {
          id: clientMessageId,
          room_id: roomId,
          sender_id: currentUserId,
          content: trimmed,
          created_at: new Date().toISOString(),
        },
      ]);

      send({ type: 'message', room_id: roomId, content: trimmed, client_message_id: clientMessageId });
    },
    [send, roomId, currentUserId],
  );

  const editMessage = useCallback(
    async (messageId: string, content: string): Promise<void> => {
      try {
        await (messagesApi as any).edit(roomId, messageId, content);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to edit message';
        throw new Error(message);
      }
    },
    [roomId],
  );

  const deleteMessage = useCallback(
    async (messageId: string): Promise<void> => {
      try {
        await (messagesApi as any).delete(roomId, messageId);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to delete message';
        throw new Error(message);
      }
    },
    [roomId],
  );

  return { messages, isLoading, isLoadingMore, hasMore, connected, sendMessage, loadOlderMessages, editMessage, deleteMessage };
}