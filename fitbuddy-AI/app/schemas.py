from typing import Literal

from pydantic import BaseModel, Field


class UserInput(BaseModel):

    username: str = Field(
        min_length=2,
        max_length=120
    )

    user_id: str = Field(
        min_length=2,
        max_length=80,
        pattern=r"^[A-Za-z0-9_-]+$"
    )

    age: int = Field(
        ge=16,
        le=100
    )

    weight: float = Field(
        gt=20,
        le=400
    )

    goal: Literal[
        "Weight loss",
        "Muscle gain",
        "General wellness",
        "Flexibility"
    ]

    intensity: Literal[
        "Low",
        "Medium",
        "High"
    ]