'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { messagesApi } from '@/lib/api';
import type { Message, WsEvent } from '@/types';
import { useWebSocket } from '@/hooks/useWebSocket';

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
    // Delivery receipt for our own optimistic message — swap placeholder id
    // with the authoritative server id. Never goes to other room members.
    if (event.type === 'message_confirmed') {
      setMessages((prev) =>
        prev.map((m) => (m.id === event.client_message_id ? { ...m, id: event.server_id } : m)),
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

      // Use the clientMessageId as the optimistic entry's id so handleEvent
      // can find and replace it with a single O(n) findIndex — no content
      // comparison, no time-window heuristics.
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

  return { messages, isLoading, connected, sendMessage };
}