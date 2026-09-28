from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime
)

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        String(80),
        unique=True,
        nullable=False,
        index=True
    )

    username = Column(String(120), nullable=False)

    age = Column(Integer, nullable=False)

    weight = Column(Float, nullable=False)

    goal = Column(String(40), nullable=False)

    intensity = Column(String(20), nullable=False)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String(80), nullable=False, index=True)

    original_plan = Column(Text, nullable=False)

    updated_plan = Column(Text, nullable=True)

    nutrition_tip = Column(Text, nullable=False)

    feedback = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(DateTime, nullable=True)