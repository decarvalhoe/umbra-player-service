"""umbra-player-service - Service de gestion des profils et données des joueurs."""

import os
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy.orm import joinedload

from .extensions import db
from .models import Player, PlayerStats


def create_app() -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__)
    CORS(app)

    # Configuration
    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URL", "sqlite:///players.db")
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0") == "1"

    db.init_app(app)

    app.config.setdefault("API_AUTH_TOKEN", os.getenv("API_AUTH_TOKEN"))

    def _build_success_response(data: Dict[str, Any], message: str, status: int = 200):
        return (
            jsonify(
                {
                    "success": True,
                    "data": data,
                    "message": message,
                    "error": None,
                    "meta": None,
                }
            ),
            status,
        )

    def _extract_bearer_token() -> str:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header.split(" ", 1)[1].strip()
        return ""

    def _require_authentication():
        expected_token = app.config.get("API_AUTH_TOKEN")
        token = _extract_bearer_token()

        if not expected_token or token != expected_token:
            return False, _build_error_response(
                message="Authentification requise.",
                error_code="auth_invalid",
                status=401,
                error_message="Jeton Bearer invalide ou manquant.",
            )

        return True, None

    def _build_error_response(
        message: str, error_code: str, status: int, error_message: Optional[str] = None
    ):
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "message": message,
                    "error": {
                        "code": error_code,
                        "message": error_message or message,
                    },
                    "meta": None,
                }
            ),
            status,
        )

    def _serialize_stats(stats: Optional[PlayerStats]) -> Optional[Dict[str, Any]]:
        if stats is None:
            return None

        return {
            "health": stats.health,
            "attack": stats.attack,
            "defense": stats.defense,
        }

    def _serialize_player(player: Player) -> Dict[str, Any]:
        return {
            "id": player.id,
            "user_id": player.user_id,
            "name": player.name,
            "level": player.level,
            "xp": player.xp,
            "stats": _serialize_stats(player.stats),
        }

    # Health check endpoint
    @app.route("/health")
    def health():
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "status": "healthy",
                        "service": "umbra-player-service",
                    },
                    "message": "Service en bonne santé",
                }
            ),
            200,
        )

    @app.shell_context_processor
    def shell_context():  # pragma: no cover - dev convenience
        return {"db": db, "Player": Player, "PlayerStats": PlayerStats}

    @app.route("/players/<int:player_id>", methods=["GET"])
    def get_player(player_id: int):
        is_authenticated, error_response = _require_authentication()
        if not is_authenticated:
            return error_response

        player = (
            Player.query.options(joinedload(Player.stats))
            .filter_by(id=player_id)
            .first()
        )

        if player is None:
            return _build_error_response(
                message="Joueur introuvable.",
                error_code="player_not_found",
                status=404,
            )

        return _build_success_response(
            _serialize_player(player),
            message="Informations du joueur récupérées avec succès.",
        )

    @app.route("/players", methods=["POST"])
    def create_player():
        is_authenticated, error_response = _require_authentication()
        if not is_authenticated:
            return error_response

        user_id = request.headers.get("X-User-Id")
        if not user_id:
            return _build_error_response(
                message="Identifiant utilisateur requis.",
                error_code="user_id_missing",
                status=400,
                error_message="L'en-tête 'X-User-Id' est requis.",
            )

        payload = request.get_json(silent=True) or {}
        name = payload.get("name")
        if not isinstance(name, str) or not name.strip():
            return _build_error_response(
                message="Nom du joueur invalide.",
                error_code="invalid_payload",
                status=400,
                error_message="Le champ 'name' est requis.",
            )

        existing_player = Player.query.filter_by(user_id=user_id).first()
        if existing_player is not None:
            return _build_error_response(
                message="Un joueur existe déjà pour cet utilisateur.",
                error_code="player_already_exists",
                status=409,
                error_message="Un joueur est déjà associé à cet utilisateur.",
            )

        player = Player(user_id=user_id, name=name.strip())
        player.stats = PlayerStats()

        db.session.add(player)
        db.session.commit()

        return _build_success_response(
            _serialize_player(player),
            message="Joueur créé avec succès.",
            status=201,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)
