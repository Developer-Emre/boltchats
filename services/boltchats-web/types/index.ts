export interface AccessTokenResponse {
  access_token: string;
}

/** Returned by Next.js /api/auth/* route handlers to the browser.
 *  The refresh_token is never sent to the client — it lives in an httpOnly cookie. */
export interface SessionResponse {
  access_token: string;
  user: User;
}

// ── Domain models ────────────────────────────────────────────────────────────

export interface User {
  id: string;
  username: string;
  email: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface Room {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface Message {
  id: string;
  room_id: string;
  sender_id: string;
  content: string;
  created_at: string;
}

// ── API error ─────────────────────────────────────────────────────────────────

export interface ApiErrorShape {
  detail: string;
  code?: string;
}

// ── WebSocket — incoming events ───────────────────────────────────────────────

export interface WsIncomingMessage {
  type: 'message';
  id: string;
  room_id: string;
  sender_id: string;
  content: string;
  created_at: string;
}

export interface WsMessageConfirmedEvent {
  type: 'message_confirmed';
  /** UUID the client generated — matches the optimistic placeholder's id. */
  client_message_id: string;
  /** Authoritative id assigned by the server. */
  server_id: string;
}

export interface WsUserJoinedEvent {
  type: 'user_joined';
  room_id: string;
  user_id: string;
}

export interface WsUserLeftEvent {
  type: 'user_left';
  room_id: string;
  user_id: string;
}

export interface WsErrorEvent {
  type: 'error';
  message: string;
}

export interface WsPongEvent {
  type: 'pong';
}

export type WsEvent =
  | WsIncomingMessage
  | WsMessageConfirmedEvent
  | WsUserJoinedEvent
  | WsUserLeftEvent
  | WsErrorEvent
  | WsPongEvent;

// ── WebSocket — outgoing events ───────────────────────────────────────────────

export interface WsSendMessage {
  type: 'message';
  room_id: string;
  content: string;
  client_message_id: string;
}

export interface WsJoinRoom {
  type: 'join_room';
  room_id: string;
}

export interface WsLeaveRoom {
  type: 'leave_room';
  room_id: string;
}

export interface WsPing {
  type: 'ping';
}

export type WsOutgoingEvent = WsSendMessage | WsJoinRoom | WsLeaveRoom | WsPing;
