"""Tests pour l'endpoint GET /players/{id}."""

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
