from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SearchQuery(Base):
    __tablename__ = "search_queries"
    id: Mapped[int] = mapped_column(primary_key=True)
    phrase: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(100), default="Khác", index=True)
    language: Mapped[str] = mapped_column(String(10), default="vi")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    queries_run: Mapped[int] = mapped_column(Integer, default=0)
    stories_found: Mapped[int] = mapped_column(Integer, default=0)
    saved_count: Mapped[int] = mapped_column(Integer, default=0)
    score_total: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SearchRun(Base):
    __tablename__ = "search_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    query: Mapped[str] = mapped_column(String(500), index=True)
    options_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="RUNNING", index=True)
    results_found: Mapped[int] = mapped_column(Integer, default=0)
    new_results: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class StoryCandidate(Base):
    __tablename__ = "story_candidates"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external_id"),
        Index("ix_story_source_created", "source", "created_at"),
        Index("ix_story_discovered_score", "discovered_at", "total_score"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(250), index=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    source_url: Mapped[str] = mapped_column(String(2048), unique=True)
    author: Mapped[str | None] = mapped_column(String(250), nullable=True)
    author_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    query: Mapped[str] = mapped_column(String(500), index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    reply_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    like_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    share_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    view_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="UNREVIEWED", index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    duplicate_of_id: Mapped[int | None] = mapped_column(ForeignKey("story_candidates.id"), nullable=True)
    duplicate_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    total_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    score: Mapped["StoryScore"] = relationship(back_populates="story", uselist=False, cascade="all, delete-orphan")
    idea: Mapped["ContentIdea | None"] = relationship(back_populates="source_story", uselist=False)


class StoryScore(Base):
    __tablename__ = "story_scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("story_candidates.id", ondelete="CASCADE"), unique=True)
    hook_score: Mapped[int] = mapped_column(Integer, default=0)
    curiosity_score: Mapped[int] = mapped_column(Integer, default=0)
    horror_score: Mapped[int] = mapped_column(Integer, default=0)
    twist_score: Mapped[int] = mapped_column(Integer, default=0)
    emotion_score: Mapped[int] = mapped_column(Integer, default=0)
    story_structure_score: Mapped[int] = mapped_column(Integer, default=0)
    short_video_fit_score: Mapped[int] = mapped_column(Integer, default=0)
    source_quality_score: Mapped[int] = mapped_column(Integer, default=0)
    penalties: Mapped[list[str]] = mapped_column(JSON, default=list)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    story: Mapped[StoryCandidate] = relationship(back_populates="score")


class SavedStory(Base):
    __tablename__ = "saved_stories"
    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("story_candidates.id", ondelete="CASCADE"), unique=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentIdea(Base):
    __tablename__ = "content_ideas"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_story_id: Mapped[int] = mapped_column(ForeignKey("story_candidates.id"), unique=True, index=True)
    working_title: Mapped[str] = mapped_column(String(500))
    premise: Mapped[str] = mapped_column(Text)
    hook_1: Mapped[str] = mapped_column(Text)
    hook_2: Mapped[str] = mapped_column(Text)
    hook_3: Mapped[str] = mapped_column(Text)
    story_outline: Mapped[str] = mapped_column(Text)
    suggested_video_length: Mapped[int] = mapped_column(Integer, default=60)
    ending_question: Mapped[str] = mapped_column(Text)
    visual_background: Mapped[str] = mapped_column(Text)
    story_type: Mapped[str] = mapped_column(String(30), default="UNKNOWN")
    category: Mapped[str] = mapped_column(String(100), default="Chuyện lạ")
    status: Mapped[str] = mapped_column(String(30), default="DISCOVERED", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    source_story: Mapped[StoryCandidate] = relationship(back_populates="idea")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("story_candidates.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value_json: Mapped[Any] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
