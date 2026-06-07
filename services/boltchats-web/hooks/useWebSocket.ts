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
 * `onEvent` is stored in a ref so the caller can pass a new closure on each
 * render without causing the effect to re-run or re-register the handler.
 * The handler is registered once when the client is created — eliminating
 * all timing races between "client created" and "connected=true".
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
    if (!token) {
      console.log('[useWebSocket] no token, skipping');
      return undefined;
    }

    console.log('[useWebSocket] creating and connecting...');
    const client = new WsClient(token);
    clientRef.current = client;

    const unsubStatus = client.onStatus((status) => {
      console.log('[useWebSocket] status:', status);
      setConnected(status);
    });
    const unsubMessage = client.onMessage((event) => {
      console.log('[useWebSocket] received event:', event.type);
      onEventRef.current(event);
    });
    client.connect();

    return (): void => {
      console.log('[useWebSocket] cleanup: disconnecting...');
      setConnected(false);
      unsubStatus();
      unsubMessage();
      client.disconnect();
      clientRef.current = null;
    };
  }, [token]);

  // Empty deps: clientRef.current is accessed at call time, never stale
  const send = useCallback((event: WsOutgoingEvent): void => {
    clientRef.current?.send(event);
  }, []);

  return { connected, send };
}