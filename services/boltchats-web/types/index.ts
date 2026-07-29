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
  is_active: boolean;
  workspaces?: string[];
}

// ── Workspace & Channel (v2 API) ──────────────────────────────────────────

export interface WorkspaceMember {
  user_id: string;
  role: 'owner' | 'admin' | 'member' | 'guest';
  joined_at: string;
  is_active: boolean;
}

export interface WorkspaceSettings {
  require_email_verification: boolean;
  allow_external_sharing: boolean;
  sso_enabled: boolean;
  message_retention_days: number;
  file_retention_days: number;
  max_upload_size_mb: number;
  default_channel_visibility: 'public' | 'private';
  guest_can_post: boolean;
  guest_can_download_files: boolean;
}

export interface WorkspaceBilling {
  plan: 'free' | 'pro' | 'enterprise';
  billing_email?: string;
  billing_cycle_start?: string;
  billing_cycle_end?: string;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon_url?: string;
  owner_id: string;
  members: WorkspaceMember[];
  settings?: WorkspaceSettings;
  billing?: WorkspaceBilling;
  created_at: string;
  updated_at: string;
}

export interface ChannelSettings {
  can_post: string[];
  can_invite: string[];
  thread_replies_allowed: boolean;
  auto_join_new_members: boolean;
  posting_restrictions: 'none' | 'mods' | 'owner';
}

export interface Channel {
  id: string;
  workspace_id: string;
  name: string;
  display_name: string;
  description: string;
  type: 'public' | 'private' | 'direct_message' | 'shared_channel';
  topic: string;
  purpose: string;
  owner_id: string;
  members: string[];
  settings: ChannelSettings;
  is_archived: boolean;
  archived_at?: string;
  archived_by?: string;
  is_default: boolean;
  message_count: number;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface DirectMessageGroup {
  id: string;
  workspace_id: string;
  type: 'direct_message';
  participants: string[];
  created_by: string;
  read_status: Record<string, { read_at: string; read_message_id: string }>;
  last_message_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Invitation {
  id: string;
  workspace_id: string;
  invited_by: string;
  invited_email?: string;
  invited_user_id?: string;
  role: 'member' | 'admin' | 'guest';
  code: string;
  code_expires_at: string;
  status: 'pending' | 'accepted' | 'declined' | 'revoked';
  accepted_at?: string;
  accepted_by?: string;
  declined_at?: string;
  revoked_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface Room {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  member_ids: string[];
  is_private: boolean;
  created_at: string;
}

export interface UpdateUserPayload {
  username?: string;
}

export interface RoomPresence {
  room_id: string;
  online_user_ids: string[];
  count: number;
}

export interface UserPresence {
  user_id: string;
  is_online: boolean;
}

export interface OnlineUsers {
  online_user_ids: string[];
  count: number;
}

export interface Message {
  id: string;
  room_id: string;
  sender_id: string;
  content: string;
  created_at: string;
  edited_at?: string;
  deleted_at?: string;
  is_deleted?: boolean;
  /** Flag: false = optimistic (still being persisted), true = confirmed by server */
  confirmed?: boolean;
  reactions?: Reaction[];
}

export interface Reaction {
  emoji: string;
  users: string[];
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

export interface WsMessageEditedEvent {
  type: 'message_edited';
  room_id: string;
  message_id: string;
  content: string;
  edited_at: string;
}

export interface WsMessageDeletedEvent {
  type: 'message_deleted';
  room_id: string;
  message_id: string;
  deleted_at: string;
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

export interface WsReactionAddedEvent {
  type: 'reaction_added';
  room_id: string;
  message_id: string;
  emoji: string;
  user_id: string;
}

export interface WsReactionRemovedEvent {
  type: 'reaction_removed';
  room_id: string;
  message_id: string;
  emoji: string;
  user_id: string;
}

export type WsEvent =
  | WsIncomingMessage
  | WsMessageConfirmedEvent
  | WsMessageEditedEvent
  | WsMessageDeletedEvent
  | WsUserJoinedEvent
  | WsUserLeftEvent
  | WsReactionAddedEvent
  | WsReactionRemovedEvent
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

export interface WsSendMessageEdited {
  type: 'message_edited';
  room_id: string;
  message_id: string;
  content: string;
  edited_at: string;
}

export interface WsSendMessageDeleted {
  type: 'message_deleted';
  room_id: string;
  message_id: string;
  deleted_at: string;
}

export interface WsPing {
  type: 'ping';
}

export interface WsSendReactionAdded {
  type: 'reaction_added';
  room_id: string;
  message_id: string;
  emoji: string;
  user_id: string;
}

export interface WsSendReactionRemoved {
  type: 'reaction_removed';
  room_id: string;
  message_id: string;
  emoji: string;
  user_id: string;
}

export type WsOutgoingEvent = 
  | WsSendMessage 
  | WsJoinRoom 
  | WsLeaveRoom 
  | WsSendMessageEdited 
  | WsSendMessageDeleted 
  | WsSendReactionAdded 
  | WsSendReactionRemoved 
  | WsPing;
