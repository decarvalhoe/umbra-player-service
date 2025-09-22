"""Database models for player profiles and statistics."""

from sqlalchemy import CheckConstraint

from .extensions import db


class Player(db.Model):
    """Represents a player profile within the Umbra universe."""

    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    level = db.Column(db.Integer, nullable=False, default=1)
    xp = db.Column(db.Integer, nullable=False, default=0)

    stats = db.relationship(
        "PlayerStats",
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("level >= 1", name="ck_player_level_positive"),
        CheckConstraint("xp >= 0", name="ck_player_xp_non_negative"),
    )

    def xp_to_next_level(self) -> int:
        """Return the amount of experience required to reach the next level."""

        return max(self.level, 1) * 100

    def add_experience(self, amount: int) -> int:
        """Add experience points and perform level ups when necessary.

        Args:
            amount: Experience points to add.

        Returns:
            The number of levels gained after applying the experience.

        Raises:
            ValueError: If *amount* is negative.
        """

        if amount < 0:
            raise ValueError("Experience amount must be non-negative.")

        self.xp += amount
        levels_gained = 0

        while self.xp >= self.xp_to_next_level():
            required_xp = self.xp_to_next_level()
            self.xp -= required_xp
            self.level += 1
            levels_gained += 1

        return levels_gained

    def progress_to_next_level(self) -> float:
        """Return the normalized progress towards the next level."""

        required_xp = self.xp_to_next_level()
        if required_xp == 0:
            return 0.0

        return min(self.xp / required_xp, 1.0)

    def __repr__(self) -> str:  # pragma: no cover - convenience method
        return f"<Player id={self.id!r} name={self.name!r} level={self.level!r}>"


class PlayerStats(db.Model):
    """Represents the combat statistics for a player."""

    __tablename__ = "player_stats"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(
        db.Integer, db.ForeignKey("players.id"), nullable=False, unique=True
    )
    health = db.Column(db.Integer, nullable=False, default=100)
    attack = db.Column(db.Integer, nullable=False, default=10)
    defense = db.Column(db.Integer, nullable=False, default=5)

    player = db.relationship("Player", back_populates="stats")

    __table_args__ = (
        CheckConstraint("health >= 0", name="ck_player_stats_health_non_negative"),
        CheckConstraint("attack >= 0", name="ck_player_stats_attack_non_negative"),
        CheckConstraint("defense >= 0", name="ck_player_stats_defense_non_negative"),
    )

    def __repr__(self) -> str:  # pragma: no cover - convenience method
        return (
            "<PlayerStats "
            f"player_id={self.player_id!r} "
            f"health={self.health!r} "
            f"attack={self.attack!r} "
            f"defense={self.defense!r}>"
        )
