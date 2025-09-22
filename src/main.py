"""umbra-player-service - Service de gestion des profils et données des joueurs."""

import os

from flask import Flask, jsonify
from flask_cors import CORS

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

    # TODO: Ajouter les routes spécifiques au service

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)
