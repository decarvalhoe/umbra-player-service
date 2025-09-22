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
        expected_token = app.config.get("API_AUTH_TOKEN")

        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

        if not expected_token or token != expected_token:
            return _build_error_response(
                message="Authentification requise.",
                error_code="auth_invalid",
                status=401,
                error_message="Jeton Bearer invalide ou manquant.",
            )

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

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)
