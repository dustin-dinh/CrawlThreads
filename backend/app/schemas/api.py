from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    hook_score: int
    curiosity_score: int
    horror_score: int
    twist_score: int
    emotion_score: int
    story_structure_score: int
    short_video_fit_score: int
    source_quality_score: int
    penalties: list[str]
    reasons: list[str]


class StoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    external_id: str
    source: str
    source_url: str
    author: str | None
    author_url: str | None
    text: str
    title: str
    created_at: datetime | None
    discovered_at: datetime
    language: str | None
    query: str
    tags: list[str]
    reply_count: int | None
    like_count: int | None
    share_count: int | None
    view_count: int | None
    media_type: str | None
    status: str
    is_demo: bool
    duplicate_of_id: int | None
    duplicate_similarity: float | None
    notes: str
    total_score: int
    score: ScoreOut | None = None


class PaginatedStories(BaseModel):
    items: list[StoryOut]
    total: int
    page: int
    page_size: int
    pages: int


class SearchRequest(BaseModel):
    queries: list[str] = Field(min_length=1, max_length=100)
    sources: list[Literal["demo", "threads", "reddit"]] = ["demo"]
    search_type: Literal["TOP", "RECENT"] = "RECENT"
    language: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    min_text_length: int = Field(default=60, ge=0, le=100_000)
    max_text_length: int = Field(default=5000, ge=1, le=200_000)
    has_replies: bool | None = None
    has_media: bool | None = None
    min_story_score: int = Field(default=0, ge=0, le=100)
    limit: int = Field(default=25, ge=1, le=100)

    @field_validator("queries")
    @classmethod
    def clean_queries(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            raise ValueError("Cần ít nhất một từ khóa")
        return cleaned


class StoryUpdate(BaseModel):
    status: Literal["UNREVIEWED", "SAVED", "REJECTED", "DUPLICATE"] | None = None
    notes: str | None = Field(default=None, max_length=20_000)
    duplicate_of_id: int | None = None


class IdeaUpdate(BaseModel):
    working_title: str | None = Field(default=None, max_length=500)
    premise: str | None = None
    hook_1: str | None = None
    hook_2: str | None = None
    hook_3: str | None = None
    story_outline: str | None = None
    suggested_video_length: int | None = Field(default=None, ge=15, le=600)
    ending_question: str | None = None
    visual_background: str | None = None
    story_type: Literal["REAL CLAIM", "PERSONAL ANECDOTE", "URBAN LEGEND", "FICTION", "UNKNOWN"] | None = None
    category: str | None = None
    status: Literal["DISCOVERED", "SHORTLISTED", "SCRIPTING", "READY_TO_EDIT", "EDITING", "UPLOADED", "REJECTED"] | None = None
    notes: str | None = None


class KeywordCreate(BaseModel):
    phrase: str = Field(min_length=1, max_length=300)
    category: str = Field(default="Khác", max_length=100)
    language: str = Field(default="vi", max_length=10)
    enabled: bool = True


class KeywordUpdate(BaseModel):
    phrase: str | None = Field(default=None, min_length=1, max_length=300)
    category: str | None = Field(default=None, max_length=100)
    language: str | None = Field(default=None, max_length=10)
    enabled: bool | None = None


class SettingsUpdate(BaseModel):
    setup_complete: bool | None = None
    demo_mode: bool | None = None
    duplicate_similarity_threshold: float | None = Field(default=None, ge=0.5, le=1)
    default_page_size: int | None = Field(default=None, ge=10, le=100)
    ai_provider: Literal["openai", "ollama"] | None = None
