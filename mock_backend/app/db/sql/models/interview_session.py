import uuid
import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.sql.base import Base

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    status: Mapped[str] = mapped_column(String, default="active")
    
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    answered_count: Mapped[int] = mapped_column(Integer, default=0)

    interview: Mapped["Interview"] = relationship("Interview", back_populates="sessions")
    candidate: Mapped["User"] = relationship("User", foreign_keys=[candidate_id])
