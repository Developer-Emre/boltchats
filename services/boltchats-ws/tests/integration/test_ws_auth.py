import pytest
from starlette.websockets import WebSocketDisconnect

from tests.conftest import make_token


@pytest.mark.integration
def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "boltchats-ws"}


@pytest.mark.integration
def test_valid_token_connects(client, valid_token):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "ping"})
        data = ws.receive_json()
    assert data["type"] == "pong"


@pytest.mark.integration
def test_invalid_token_closes_with_4001(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws?token=bad.token.here") as ws:
            ws.receive_json()
    assert exc.value.code == 4001


@pytest.mark.integration
def test_missing_token_closes_with_4001(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()
    assert exc.value.code == 4001


@pytest.mark.integration
def test_token_without_sub_claim_closes_with_4001(client):
    from jose import jwt
    from app.core.config import get_settings

    settings = get_settings()
    bad_token = jwt.encode({"no_sub": "here"}, settings.secret_key, algorithm=settings.algorithm)

    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws?token={bad_token}") as ws:
            ws.receive_json()
    assert exc.value.code == 4001


@pytest.mark.integration
def test_expired_token_closes_with_4001(client):
    from datetime import datetime, timezone
    from jose import jwt
    from app.core.config import get_settings

    settings = get_settings()
    expired_token = jwt.encode(
        {"sub": "user_001", "exp": datetime(2000, 1, 1, tzinfo=timezone.utc)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws?token={expired_token}") as ws:
            ws.receive_json()
    assert exc.value.code == 4001
