"""SQLAlchemy models used by the smart playlist pipeline."""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

UTC = timezone.utc

class Play(Base):
    """Last-known play timestamp for a track, keyed by ISRC."""
    __tablename__ = "plays"

    track_isrc = Column(String, primary_key=True)
    last_played = Column(
        DateTime(),
        nullable=False,
    )

    def played_within_last_n_days(self, n: int) -> bool:
        """
        Return ``True`` when the track has been played within ``n`` days.
        """
        cutoff = (datetime.now(UTC) - timedelta(days=n)).replace(tzinfo=None)  # naive UTC
        return self.last_played >= cutoff
