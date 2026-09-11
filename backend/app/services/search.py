import logging
import time
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_config
from app.models import SearchQuery, SearchRun, Source, StoryCandidate, StoryScore
from app.schemas.api import SearchRequest
from app.scoring import score_story
from app.sources import DemoSource, RedditSource, SearchOptions, SourceAdapter, StoryPayload, ThreadsSource
from .duplicates import cosine_similarity, normalize_text

logger = logging.getLogger(__name__)


def adapters() -> dict[str, SourceAdapter]:
    return {"demo": DemoSource(), "threads": ThreadsSource(), "reddit": RedditSource()}


async def execute_search(db: Session, request: SearchRequest) -> list[SearchRun]:
    available = adapters()
    completed_runs: list[SearchRun] = []
    for query in request.queries:
        keyword = db.scalar(select(SearchQuery).where(SearchQuery.phrase == query))
        for source_slug in request.sources:
            started = time.perf_counter()
            run = SearchRun(
                source=source_slug,
                query=query,
                options_json=request.model_dump(mode="json"),
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            try:
                source_record = db.scalar(select(Source).where(Source.slug == source_slug))
                if source_record and not source_record.enabled:
                    raise ValueError(f"Nguồn {source_slug} đang bị tắt trong Cài đặt nguồn.")
                payloads = await available[source_slug].search(
                    query,
                    SearchOptions(
                        search_type=request.search_type,
                        since=request.since,
                        until=request.until,
                        limit=request.limit,
                    ),
                )
                run.results_found = len(payloads)
                for payload in payloads:
                    if not _passes_filters(payload, request):
                        continue
                    created, duplicate, stored_score = _store_payload(db, payload, request.min_story_score)
                    run.new_results += int(created)
                    run.duplicates += int(duplicate)
                    if keyword and created:
                        keyword.score_total += stored_score
                run.status = "COMPLETED"
                if keyword:
                    keyword.queries_run += 1
                    keyword.stories_found += run.new_results
            except Exception as exc:
                logger.exception("search_failed source=%s query=%s", source_slug, query)
                run.status = "FAILED"
                run.errors = str(exc)[:2000]
            finally:
                run.completed_at = datetime.now(timezone.utc)
                run.duration_ms = round((time.perf_counter() - started) * 1000)
                db.commit()
                db.refresh(run)
                completed_runs.append(run)
                logger.info("crawl_complete source=%s query=%s status=%s new=%s", source_slug, query, run.status, run.new_results)
    return completed_runs


def _passes_filters(payload: StoryPayload, request: SearchRequest) -> bool:
    length = len(payload.text)
    if length < request.min_text_length or length > request.max_text_length:
        return False
    if request.has_replies is True and not payload.reply_count:
        return False
    if request.has_replies is False and payload.reply_count:
        return False
    if request.has_media is True and payload.media_type in (None, "TEXT", "TEXT_POST", "SELF"):
        return False
    if request.language and payload.language and payload.language != request.language:
        return False
    return True


def _store_payload(db: Session, payload: StoryPayload, min_score: int) -> tuple[bool, bool, int]:
    exact = db.scalar(select(StoryCandidate).where(or_(
        StoryCandidate.source_url == payload.source_url,
        (StoryCandidate.source == payload.source) & (StoryCandidate.external_id == payload.external_id),
    )))
    if exact:
        return False, True, 0

    normalized = normalize_text(payload.text)
    score = score_story(payload.text, payload.source, payload.reply_count, payload.like_count)
    if score.total_score < min_score:
        return False, False, 0

    duplicate_of, similarity = _near_duplicate(db, payload.text)
    story = StoryCandidate(
        external_id=payload.external_id,
        source=payload.source,
        source_url=payload.source_url,
        author=payload.author,
        author_url=payload.author_url,
        text=payload.text,
        normalized_text=normalized,
        title=payload.title,
        created_at=payload.created_at,
        language=payload.language,
        query=payload.query,
        tags=payload.tags,
        reply_count=payload.reply_count,
        like_count=payload.like_count,
        share_count=payload.share_count,
        view_count=payload.view_count,
        media_type=payload.media_type,
        metadata_json=payload.metadata,
        is_demo=payload.is_demo,
        duplicate_of_id=duplicate_of.id if duplicate_of else None,
        duplicate_similarity=similarity if duplicate_of else None,
        status="DUPLICATE" if duplicate_of else "UNREVIEWED",
        total_score=score.total_score,
    )
    story.score = StoryScore(**{k: v for k, v in score.to_dict().items() if k != "total_score"})
    db.add(story)
    try:
        db.commit()
        return True, duplicate_of is not None, score.total_score
    except IntegrityError:
        db.rollback()
        return False, True, 0


def _near_duplicate(db: Session, text: str) -> tuple[StoryCandidate | None, float]:
    # Limit comparison candidates for predictable performance with 10k+ records.
    candidates = db.scalars(select(StoryCandidate).order_by(StoryCandidate.discovered_at.desc()).limit(1000)).all()
    best_story = None
    best_similarity = 0.0
    threshold = get_config().duplicate_similarity_threshold
    setting = db.get(__import__("app.models", fromlist=["Setting"]).Setting, "duplicate_similarity_threshold")
    if setting:
        threshold = float(setting.value_json)
    for candidate in candidates:
        similarity = cosine_similarity(text, candidate.text)
        if similarity > best_similarity:
            best_story, best_similarity = candidate, similarity
    return (best_story, best_similarity) if best_similarity >= threshold else (None, best_similarity)
