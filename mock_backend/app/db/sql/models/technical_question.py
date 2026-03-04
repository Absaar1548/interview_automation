"""
Models for subjective technical questions (Data Science / AI).
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, ForeignKey, Enum, DateTime, JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.sql.base import Base


class QuestionCategory(str, enum.Enum):
    DATA_SCIENCE = "data_science"
    AI_ML = "ai_ml"
    DEEP_LEARNING = "deep_learning"
    NLP = "nlp"
    STATISTICS = "statistics"


class TechnicalQuestion(Base):
    __tablename__ = "technical_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[QuestionCategory] = mapped_column(
        Enum(QuestionCategory, name="questioncategory"), nullable=False
    )
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    time_limit_sec: Mapped[int] = mapped_column(Integer, default=600)  # 10 min default
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Relationships
    answers: Mapped[list["TechnicalAnswer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class TechnicalAnswer(Base):
    __tablename__ = "technical_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("technical_questions.id", ondelete="CASCADE"), nullable=False
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"), nullable=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Relationships
    question: Mapped["TechnicalQuestion"] = relationship(back_populates="answers")
