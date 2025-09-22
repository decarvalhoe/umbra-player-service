"""Tests for the player and player stats models."""
import pytest

from src.extensions import db
from src.models import Player, PlayerStats


def test_player_stats_relationship(app):
    """A player should expose a one-to-one relationship with stats."""

    with app.app_context():
        player = Player(
            user_id="user-001",
            name="Umbra",
            stats=PlayerStats(health=120, attack=15, defense=9),
        )
        db.session.add(player)
        db.session.commit()

        retrieved = Player.query.filter_by(user_id="user-001").one()

        assert retrieved.stats is not None
        assert retrieved.stats.health == 120
        assert retrieved.stats.player is retrieved


def test_player_add_experience_levels_up(app):
    """Experience should accumulate and trigger level ups when thresholds are met."""

    with app.app_context():
        player = Player(user_id="user-002", name="Adept")
        db.session.add(player)
        db.session.commit()

        levels_gained = player.add_experience(350)

        assert levels_gained == 2
        assert player.level == 3
        assert player.xp == 50  # 350 - (100 + 200)


def test_player_add_experience_rejects_negative_amount(app):
    """Negative experience amounts are not allowed."""

    with app.app_context():
        player = Player(user_id="user-003", name="Rogue")

        with pytest.raises(ValueError):
            player.add_experience(-5)
