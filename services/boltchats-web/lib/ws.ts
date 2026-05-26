import type { WsEvent, WsOutgoingEvent } from '@/types';

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8001/ws';

type WsEventHandler = (event: WsEvent) => void;
type WsStatusHandler = (connected: boolean) => void;

export class WsClient {
  private socket: WebSocket | null = null;
  private readonly eventHandlers = new Set<WsEventHandler>();
  private readonly statusHandlers = new Set<WsStatusHandler>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;

  constructor(private readonly token: string) {}

  connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) return;

    this.socket = new WebSocket(`${WS_URL}?token=${this.token}`);

    this.socket.onopen = (): void => {
      this.emitStatus(true);
      if (this.reconnectTimer !== null) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.socket.onmessage = (e: MessageEvent<string>): void => {
      try {
        const event = JSON.parse(e.data) as WsEvent;
        this.eventHandlers.forEach((h) => h(event));
      } catch {
        // Malformed message — ignore
      }
    };

    this.socket.onclose = (): void => {
      this.emitStatus(false);
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      }
    };

    this.socket.onerror = (): void => {
      this.socket?.close();
    };
  }

  send(event: WsOutgoingEvent): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(event));
    }
  }

  onMessage(handler: WsEventHandler): () => void {
    this.eventHandlers.add(handler);
    return (): void => {
      this.eventHandlers.delete(handler);
    };
  }

  onStatus(handler: WsStatusHandler): () => void {
    this.statusHandlers.add(handler);
    return (): void => {
      this.statusHandlers.delete(handler);
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.socket = null;
  }

  private emitStatus(connected: boolean): void {
    this.statusHandlers.forEach((h) => h(connected));
  }
}
