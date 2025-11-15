from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Team(Base):
    __tablename__ = "teams"
    
    team_name = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    members = relationship("User", back_populates="team")


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=False)
    team_name = Column(String, ForeignKey("teams.team_name"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    team = relationship("Team", back_populates="members")
    authored_prs = relationship("PullRequest", foreign_keys="PullRequest.author_id", back_populates="author")


class PullRequest(Base):
    __tablename__ = "pull_requests"
    
    pull_request_id = Column(String, primary_key=True, index=True)
    pull_request_name = Column(String, nullable=False)
    author_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    status = Column(String, default="OPEN")  # OPEN, MERGED
    assigned_reviewers = Column(ARRAY(String), default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    merged_at = Column(DateTime(timezone=True), nullable=True)
    
    author = relationship("User", foreign_keys=[author_id], back_populates="authored_prs")