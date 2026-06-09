import asyncio
import json
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.constants.ws_codes import EventType, SERVICE_NAME
from app.core.config import get_settings
from app.core.redis import close_redis, connect_redis, get_redis
from app.handlers.message_handler import handle_message
from app.handlers.message_edit_delete_handler import handle_message_edited, handle_message_deleted
from app.handlers.ping_handler import handle_ping
from app.handlers.room_handler import handle_join_room, handle_leave_room
from app.managers.broadcast_manager import BroadcastManager
from app.managers.connection_manager import ConnectionManager
from app.managers.message_confirmation_manager import MessageConfirmationManager
from app.managers.presence_manager import PresenceManager
from app.managers.room_manager import RoomManager
from app.middlewares.auth_websocket import authenticate_ws
from app.middlewares.rate_limit_ws import check_message_rate_limit
from app.models.ws_event import JoinRoomEvent, LeaveRoomEvent, MessageEvent, MessageEditedEvent, MessageDeletedEvent
from app.models.ws_message import MessageConfirmed
from app.utils.message_queue import MessageQueue

logger = structlog.get_logger()

# Module-level singletons — in-memory state per process
connection_manager = ConnectionManager()
room_manager = RoomManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await connect_redis(settings.redis_url)
    redis = get_redis()

    broadcast_manager = BroadcastManager(redis)
    presence_manager = PresenceManager(redis)
    message_queue = MessageQueue(redis)
    confirmation_manager = MessageConfirmationManager(redis)

    async def on_broadcast(room_id: str, data: str) -> None:
        """Deliver a broadcast message to all local connections in the room."""
        members = room_manager.get_members(room_id)
        await asyncio.gather(
            *[connection_manager.send_to_user(uid, data) for uid in members],
            return_exceptions=True,
        )

    async def on_message_confirmed(data: str) -> None:
        """Receive message confirmation from storage service.
        
        Data format: { "client_message_id": uuid, "server_id": ObjectId, "room_id": room_id }
        Send it to the original sender so they can update their optimistic message.
        """
        try:
            confirmation = json.loads(data)
            client_message_id = confirmation.get("client_message_id")
            room_id = confirmation.get("room_id")
            server_id = confirmation.get("server_id")
            
            logger.debug(
                "message_confirmation_manager.received",
                client_message_id=client_message_id,
                server_id=server_id,
                room_id=room_id,
            )
            
            # Send confirmation to all users in the room
            # Frontend will match by client_message_id
            msg = MessageConfirmed(
                client_message_id=client_message_id,
                server_id=server_id,
            )
            members = room_manager.get_members(room_id)
            
            logger.debug(
                "message_confirmation_manager.sending",
                room_id=room_id,
                num_members=len(members),
                member_ids=members,
            )
            
            await asyncio.gather(
                *[connection_manager.send_to_user(uid, msg.model_dump_json()) for uid in members],
                return_exceptions=True,
            )
            
            logger.debug(
                "message_confirmed.forwarded",
                room_id=room_id,
                client_message_id=client_message_id,
            )
        except Exception as exc:
            logger.exception("message_confirmed.forward_failed", error=str(exc))

    await broadcast_manager.start(on_broadcast)
    await confirmation_manager.start(on_message_confirmed)

    app.state.redis = redis
    app.state.broadcast_manager = broadcast_manager
    app.state.presence_manager = presence_manager
    app.state.message_queue = message_queue
    app.state.confirmation_manager = confirmation_manager

    logger.info("boltchats_ws.started")
    yield

    await confirmation_manager.stop()
    await broadcast_manager.stop()
    await close_redis()
    logger.info("boltchats_ws.stopped")


app = FastAPI(title=SERVICE_NAME, lifespan=lifespan)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    token: str = Query(default=None),
) -> None:
    settings = get_settings()
    broadcast_manager: BroadcastManager = app.state.broadcast_manager
    presence_manager: PresenceManager = app.state.presence_manager
    message_queue: MessageQueue = app.state.message_queue
    redis = app.state.redis

    try:
        user_id = await authenticate_ws(ws, token)
    except WebSocketDisconnect:
        return

    await connection_manager.connect(ws, user_id)
    logger.info("ws.connected", user_id=user_id)

    try:
        while True:
            raw = await ws.receive_text()

            try:
                data: dict = json.loads(raw)
                event_type: str = data.get("type", "")
            except (json.JSONDecodeError, AttributeError):
                await ws.send_text(
                    json.dumps({"type": EventType.ERROR, "detail": "Invalid JSON"})
                )
                continue

            if not await check_message_rate_limit(
                redis, user_id, settings.rate_limit_messages_per_second
            ):
                await ws.send_text(
                    json.dumps({"type": EventType.ERROR, "detail": "Rate limit exceeded"})
                )
                continue

            try:
                if event_type == EventType.MESSAGE:
                    await handle_message(
                        MessageEvent(**data),
                        user_id,
                        room_manager,
                        broadcast_manager,
                        message_queue,
                        connection_manager,
                    )
                elif event_type == EventType.MESSAGE_EDITED:
                    await handle_message_edited(
                        MessageEditedEvent(**data),
                        user_id,
                        room_manager,
                        broadcast_manager,
                    )
                elif event_type == EventType.MESSAGE_DELETED:
                    await handle_message_deleted(
                        MessageDeletedEvent(**data),
                        user_id,
                        room_manager,
                        broadcast_manager,
                    )
                elif event_type == EventType.JOIN_ROOM:
                    await handle_join_room(
                        JoinRoomEvent(**data),
                        user_id,
                        room_manager,
                        presence_manager,
                        broadcast_manager,
                    )
                elif event_type == EventType.LEAVE_ROOM:
                    await handle_leave_room(
                        LeaveRoomEvent(**data),
                        user_id,
                        room_manager,
                        presence_manager,
                        broadcast_manager,
                    )
                elif event_type == EventType.PING:
                    await handle_ping(ws)
                else:
                    await ws.send_text(
                        json.dumps(
                            {
                                "type": EventType.ERROR,
                                "detail": f"Unknown event type: {event_type!r}",
                            }
                        )
                    )
            except (ValidationError, ValueError) as exc:
                await ws.send_text(
                    json.dumps({"type": EventType.ERROR, "detail": str(exc)})
                )

    except WebSocketDisconnect:
        logger.info("ws.disconnected", user_id=user_id)
    finally:
        rooms = room_manager.leave_all(user_id)
        connection_manager.disconnect(user_id, ws)
        await presence_manager.user_offline(user_id, rooms)
        logger.info("ws.cleaned_up", user_id=user_id, rooms=rooms)
