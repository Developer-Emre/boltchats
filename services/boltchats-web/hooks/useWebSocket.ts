'use client';

import { useCallback, useEffect, useRef } from 'react';
import type { WsEvent, WsOutgoingEvent } from '@/types';
import { WsClient } from '@/lib/ws';

interface UseWebSocketReturn {
  connected: boolean;
  send: (event: WsOutgoingEvent) => void;
}

// Module-level singleton — shared across all useWebSocket instances
let globalWsClient: WsClient | null = null;
let globalRefCount = 0;

/**
 * Hook to use the global singleton WebSocket client.
 * Multiple components can call this — they all share the same WsClient instance.
 *
 * Reference counting ensures the client stays alive as long as at least
 * one component is mounted that uses it.
 *
 * `onEvent` is stored in a ref so the caller can pass a new closure on each
 * render without causing re-subscriptions.
 */
export function useWebSocket(
  token: string | null,
  onEvent: (event: WsEvent) => void,
): UseWebSocketReturn {
  const connectedRef = useRef(false);
  const onEventRef = useRef(onEvent);
  const unsubscribersRef = useRef<Array<() => void>>([]);

  onEventRef.current = onEvent;

  useEffect(() => {
    if (!token) {
      console.log('[useWebSocket] no token, skipping');
      return;
    }

    console.log('[useWebSocket] subscribing', {
      hasGlobalClient: !!globalWsClient,
      tokenMatch: globalWsClient?.getToken() === token,
    });

    // Create global client if it doesn't exist or token changed
    if (!globalWsClient || globalWsClient.getToken() !== token) {
      console.log('[useWebSocket] creating new global client (token mismatch or missing)');
      if (globalWsClient) {
        globalWsClient.disconnect();
      }
      globalWsClient = new WsClient(token);
      globalWsClient.connect();
    }

    // Increment ref count
    globalRefCount += 1;
    console.log('[useWebSocket] ref count:', globalRefCount);

    // Subscribe to events
    const unsubStatus = globalWsClient.onStatus((status) => {
      console.log('[useWebSocket] status:', status);
      connectedRef.current = status;
    });

    const unsubMessage = globalWsClient.onMessage((event) => {
      console.log('[useWebSocket] received event:', event.type);
      onEventRef.current(event);
    });

    unsubscribersRef.current = [unsubStatus, unsubMessage];

    // Cleanup on unmount or token change
    return (): void => {
      console.log('[useWebSocket] unsubscribing');

      // Unsubscribe from events
      unsubscribersRef.current.forEach((unsub) => unsub());
      unsubscribersRef.current = [];

      // Decrement ref count
      globalRefCount -= 1;
      console.log('[useWebSocket] ref count:', globalRefCount);

      // Disconnect global client if no more subscribers
      if (globalRefCount === 0 && globalWsClient) {
        console.log('[useWebSocket] no more subscribers, disconnecting global client');
        globalWsClient.disconnect();
        globalWsClient = null;
      }
    };
  }, [token]);

  // Empty deps: read connectedRef.current at call time (never stale)
  const send = useCallback((event: WsOutgoingEvent): void => {
    globalWsClient?.send(event);
  }, []);

  return { connected: connectedRef.current, send };
}
