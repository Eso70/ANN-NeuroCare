from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint(
            "predicted_probability >= 0 AND predicted_probability <= 1",
            name="ck_predictions_probability",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_reference: Mapped[str | None] = mapped_column(String(100), index=True)
    input_data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    predicted_class: Mapped[int | None] = mapped_column(Integer)
    predicted_probability: Mapped[float | None] = mapped_column(Float)
    model_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
