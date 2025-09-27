"""Tests pour les endpoints joueurs."""

from src.extensions import db
from src.models import Player, PlayerStats


def _create_player():
    player = Player(user_id="user-123", name="Test Player", level=5, xp=250)
    stats = PlayerStats(health=150, attack=25, defense=18)
    player.stats = stats
    db.session.add(player)
    db.session.commit()
    return player


def test_get_player_requires_auth(client):
    response = client.get("/players/1")

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "auth_invalid"


def test_get_player_invalid_token(client):
    response = client.get(
        "/players/1",
        headers={"Authorization": "Bearer invalid"},
    )

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "auth_invalid"


def test_get_player_not_found(client):
    response = client.get(
        "/players/999",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "player_not_found"


def test_get_player_success(client, app):
    with app.app_context():
        player = _create_player()
        player_id = player.id

    response = client.get(
        f"/players/{player_id}",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["id"] == player_id
    assert payload["data"]["user_id"] == "user-123"
    assert payload["data"]["stats"]["health"] == 150
    assert payload["message"] == "Informations du joueur récupérées avec succès."


def test_create_player_requires_auth(client):
    response = client.post(
        "/players",
        json={"name": "New Player"},
    )

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "auth_invalid"


def test_create_player_missing_user_id(client):
    response = client.post(
        "/players",
        json={"name": "New Player"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "user_id_missing"


def test_create_player_missing_name(client):
    response = client.post(
        "/players",
        json={},
        headers={
            "Authorization": "Bearer test-token",
            "X-User-Id": "user-456",
        },
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "invalid_payload"


def test_create_player_conflict(client, app):
    with app.app_context():
        _create_player()

    response = client.post(
        "/players",
        json={"name": "Duplicate"},
        headers={
            "Authorization": "Bearer test-token",
            "X-User-Id": "user-123",
        },
    )

    assert response.status_code == 409
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "player_already_exists"


def test_create_player_success(client):
    response = client.post(
        "/players",
        json={"name": "Umbra Hero"},
        headers={
            "Authorization": "Bearer test-token",
            "X-User-Id": "user-789",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["user_id"] == "user-789"
    assert payload["data"]["name"] == "Umbra Hero"
    assert payload["data"]["stats"]["health"] == 100
    assert payload["message"] == "Joueur créé avec succès."


def test_update_player_requires_auth(client, app):
    with app.app_context():
        player = _create_player()
        player_id = player.id

    response = client.put(
        f"/players/{player_id}",
        json={"name": "New Name"},
    )

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "auth_invalid"


def test_update_player_missing_user_id(client, app):
    with app.app_context():
        player = _create_player()
        player_id = player.id

    response = client.put(
        f"/players/{player_id}",
        json={"name": "New Name"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "user_id_missing"


def test_update_player_not_found(client):
    response = client.put(
        "/players/9999",
        json={"name": "New Name"},
        headers={
            "Authorization": "Bearer test-token",
            "X-User-Id": "user-unknown",
        },
    )

    assert response.status_code == 404
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "player_not_found"


def test_update_player_forbidden(client, app):
    with app.app_context():
        player = _create_player()
        player_id = player.id

    response = client.put(
        f"/players/{player_id}",
        json={"name": "New Name"},
        headers={
            "Authorization": "Bearer test-token",
            "X-User-Id": "user-456",
        },
    )

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "forbidden"


def test_update_player_invalid_name(client, app):
    with app.app_context():
        player = _create_player()
        player_id = player.id

    response = client.put(
        f"/players/{player_id}",
        json={"name": "   "},
        headers={
            "Authorization": "Bearer test-token",
            "X-User-Id": "user-123",
        },
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "invalid_payload"


def test_update_player_success(client, app):
    with app.app_context():
        player = _create_player()
        player_id = player.id

    response = client.put(
        f"/players/{player_id}",
        json={"name": "Umbra Legend"},
        headers={
            "Authorization": "Bearer test-token",
            "X-User-Id": "user-123",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["id"] == player_id
    assert payload["data"]["name"] == "Umbra Legend"
    assert payload["message"] == "Joueur mis à jour avec succès."
