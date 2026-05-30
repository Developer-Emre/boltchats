'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { WsClient } from '@/lib/ws';
import type { WsEvent, WsOutgoingEvent } from '@/types';

interface UseWebSocketReturn {
  connected: boolean;
  send: (event: WsOutgoingEvent) => void;
}

/**
 * Manages a single WsClient lifecycle.
 *
 * `onEvent` is called for every incoming WS event. Internally it is stored
 * in a ref so the caller can pass a new closure on each render without
 * causing the effect to re-run or the handler registration to be redone.
 * The handler is registered exactly once when the client is created —
 * eliminating all timing races between "client created" and "connected=true".
 */
export function useWebSocket(
  token: string | null,
  onEvent: (event: WsEvent) => void,
): UseWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const clientRef = useRef<WsClient | null>(null);

  // Always-current reference — updated on every render, never stale
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect((): (() => void) | undefined => {
    if (!token) return undefined;

    const client = new WsClient(token);
    clientRef.current = client;

    const unsubStatus = client.onStatus(setConnected);
    // Register once at creation time via the ref — no separate subscription effect needed
    const unsubMessage = client.onMessage((event) => onEventRef.current(event));
    client.connect();

    return (): void => {
      setConnected(false);
      unsubStatus();
      unsubMessage();
      client.disconnect();
      clientRef.current = null;
    };
  }, [token]);

  const send = useCallback((event: WsOutgoingEvent): void => {
    clientRef.current?.send(event);
  }, []);

  return { connected, send };
}
