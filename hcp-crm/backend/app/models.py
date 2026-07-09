import datetime as dt

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    Time,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    hospital = Column(String(255), nullable=True)
    specialty = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=True)

    # Denormalized copy so the form always has a readable snapshot
    hcp_name = Column(String(255), nullable=True)
    hospital = Column(String(255), nullable=True)
    specialty = Column(String(255), nullable=True)

    interaction_type = Column(String(100), nullable=True)  # Meeting, Call, Email, Conference...
    interaction_date = Column(Date, nullable=True)
    interaction_time = Column(Time, nullable=True)

    attendees = Column(JSON, nullable=True, default=list)
    topics_discussed = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)  # Positive, Neutral, Negative
    materials_shared = Column(JSON, nullable=True, default=list)

    follow_up_actions = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    # AI generated
    summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True, default=list)
    entities = Column(JSON, nullable=True, default=dict)
    suggested_next_steps = Column(JSON, nullable=True, default=list)
    meeting_outcome = Column(String(100), nullable=True)

    status = Column(String(50), default="Logged")  # Logged, Draft, Needs Follow-up
    session_id = Column(String(100), nullable=True, index=True)

    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
    follow_ups = relationship("FollowUpTask", back_populates="interaction")


class FollowUpTask(Base):
    __tablename__ = "follow_up_tasks"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String(50), default="Pending")  # Pending, Completed, Cancelled
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    interaction = relationship("Interaction", back_populates="follow_ups")
