'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { WsClient } from '@/lib/ws';
import type { WsEvent, WsOutgoingEvent } from '@/types';

interface UseWebSocketReturn {
  connected: boolean;
  send: (event: WsOutgoingEvent) => void;
  onMessage: (handler: (event: WsEvent) => void) => () => void;
}

export function useWebSocket(token: string | null): UseWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const clientRef = useRef<WsClient | null>(null);

  useEffect((): (() => void) | undefined => {
    if (!token) return undefined;

    const client = new WsClient(token);
    clientRef.current = client;

    const unsubStatus = client.onStatus(setConnected);
    client.connect();

    return (): void => {
      unsubStatus();
      client.disconnect();
      clientRef.current = null;
    };
  }, [token]);

  // Stable references — use clientRef internally so deps array stays empty
  const send = useCallback((event: WsOutgoingEvent): void => {
    clientRef.current?.send(event);
  }, []);

  const onMessage = useCallback(
    (handler: (event: WsEvent) => void): (() => void) => {
      if (!clientRef.current) return (): void => undefined;
      return clientRef.current.onMessage(handler);
    },
    [],
  );

  return { connected, send, onMessage };
}
