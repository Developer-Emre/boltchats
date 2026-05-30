'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { messagesApi } from '@/lib/api';
import type { Message, WsEvent } from '@/types';
import { useWebSocket } from '@/hooks/useWebSocket';

// How long (ms) an optimistic message is eligible to be replaced by its
// server confirmation. Covers any realistic WS round-trip.
const OPTIMISTIC_TTL_MS = 30_000;

interface UseMessagesReturn {
  messages: Message[];
  isLoading: boolean;
  connected: boolean;
  sendMessage: (content: string) => void;
}

export function useMessages(
  roomId: string,
  token: string | null,
  currentUserId: string,
): UseMessagesReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const joinedRef = useRef(false);

  // Keep roomId in a ref so the WS event handler never closes over a stale value
  const roomIdRef = useRef(roomId);
  roomIdRef.current = roomId;

  const handleEvent = useCallback((event: WsEvent): void => {
    if (event.type !== 'message' || event.room_id !== roomIdRef.current) return;

    setMessages((prev) => {
      // Guard against duplicate delivery (e.g. reconnect replays)
      if (prev.some((m) => m.id === event.id)) return prev;

      // Replace the matching optimistic placeholder with the confirmed server
      // message. Match on content + sender within the TTL window so we never
      // accidentally collapse two distinct messages the user sent.
      // findIndex returns the *first* match, which is correct: server
      // confirmations arrive in send order, so each echo replaces its own
      // optimistic entry and leaves later ones untouched.
      const serverTime = new Date(event.created_at).getTime();
      const optimisticIdx = prev.findIndex(
        (m) =>
          m.id.startsWith('optimistic-') &&
          m.content === event.content &&
          m.sender_id === event.sender_id &&
          Math.abs(serverTime - new Date(m.created_at).getTime()) < OPTIMISTIC_TTL_MS,
      );

      if (optimisticIdx !== -1) {
        const updated = [...prev];
        updated[optimisticIdx] = event as Message;
        return updated;
      }

      return [...prev, event as Message];
    });
  }, []);

  const { connected, send } = useWebSocket(token, handleEvent);

  // Fetch message history whenever the room changes
  useEffect((): void => {
    setIsLoading(true);
    setMessages([]);
    messagesApi
      .list(roomId)
      .then((msgs: Message[]): void => setMessages(msgs))
      .catch((): void => setMessages([]))
      .finally((): void => setIsLoading(false));
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

  const sendMessage = useCallback(
    (content: string): void => {
      const trimmed = content.trim();
      if (!trimmed) return;

      // Show immediately — handleEvent will swap this out when the server
      // echo arrives, giving the user instant feedback with no ghost messages.
      setMessages((prev) => [
        ...prev,
        {
          id: `optimistic-${Date.now()}`,
          room_id: roomId,
          sender_id: currentUserId,
          content: trimmed,
          created_at: new Date().toISOString(),
        },
      ]);

      send({ type: 'message', room_id: roomId, content: trimmed });
    },
    [send, roomId, currentUserId],
  );

  return { messages, isLoading, connected, sendMessage };
}