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
): UseMessagesReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { connected, send, onMessage } = useWebSocket(token);
  const joinedRef = useRef(false);

  // Fetch message history on room change
  useEffect((): void => {
    setIsLoading(true);
    setMessages([]);
    messagesApi
      .list(roomId)
      .then((msgs: Message[]): void => setMessages(msgs))
      .catch((): void => setMessages([]))
      .finally((): void => setIsLoading(false));
  }, [roomId]);

  // Join room once WS connects
  useEffect((): void => {
    if (connected && !joinedRef.current) {
      send({ type: 'join_room', room_id: roomId });
      joinedRef.current = true;
    }
    if (!connected) {
      joinedRef.current = false;
    }
  }, [connected, roomId, send]);

  // Subscribe to incoming WS messages
  useEffect((): (() => void) => {
    const unsub = onMessage((event: WsEvent): void => {
      if (event.type === 'message' && event.room_id === roomId) {
        setMessages((prev) => [...prev, event]);
      }
    });
    return unsub;
  }, [onMessage, roomId]);

  const sendMessage = useCallback(
    (content: string): void => {
      const trimmed = content.trim();
      if (!trimmed) return;
      send({ type: 'message', room_id: roomId, content: trimmed });
    },
    [send, roomId],
  );

  return { messages, isLoading, connected, sendMessage };
}
