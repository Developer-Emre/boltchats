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

  // Initialize client once on mount, keep alive across token changes
  useEffect(() => {
    console.log('[useWebSocket] component mounted');
    return () => {
      console.log('[useWebSocket] component unmounting, cleanup');
      if (clientRef.current) {
        clientRef.current.disconnect();
        clientRef.current = null;
      }
      setConnected(false);
    };
  }, []);

  // Reconnect when token changes (avoids disconnect loop on intermediate null)
  useEffect(() => {
    if (!token) {
      console.log('[useWebSocket] no token yet');
      return;
    }

    // If client already exists with same token, do nothing
    if (clientRef.current) {
      const existingToken = clientRef.current.getToken();
      if (existingToken === token) {
        console.log('[useWebSocket] token unchanged, client ready');
        return;
      }
      console.log('[useWebSocket] token changed, reconnecting...');
      clientRef.current.disconnect();
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
      unsubStatus();
      unsubMessage();
    };
  }, [token]);

  // Empty deps: clientRef.current is accessed at call time, never stale
  const send = useCallback((event: WsOutgoingEvent): void => {
    clientRef.current?.send(event);
  }, []);

  return { connected, send };
}