import csv
import io
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.ai.provider import analyze_story
from app.core.config import get_config
from app.database import get_db
from app.models import AIAnalysis, ContentIdea, SavedStory, SearchQuery, SearchRun, Setting, Source, StoryCandidate
from app.schemas.api import IdeaUpdate, KeywordCreate, KeywordUpdate, PaginatedStories, SearchRequest, SettingsUpdate, StoryOut, StoryUpdate
from app.services.ideas import create_content_idea
from app.services.search import adapters, execute_search

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "app": get_config().app_name}


@router.get("/bootstrap")
def bootstrap(db: Session = Depends(get_db)) -> dict:
    return {
        "setup_complete": _setting(db, "setup_complete", False),
        "demo_mode": _setting(db, "demo_mode", True),
        "sources": _source_status(db),
        "notice": "Luôn kiểm tra nguồn và viết lại nội dung trước khi xuất bản.",
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    counts = {
        "stories_today": _count(db, StoryCandidate.discovered_at >= today),
        "unreviewed": _count(db, StoryCandidate.status == "UNREVIEWED"),
        "saved": _count(db, StoryCandidate.status == "SAVED"),
        "rejected": _count(db, StoryCandidate.status == "REJECTED"),
        "high_potential": _count(db, StoryCandidate.total_score >= 70),
        "content_ideas": db.scalar(select(func.count()).select_from(ContentIdea)) or 0,
    }
    top = db.scalars(
        select(StoryCandidate)
        .options(joinedload(StoryCandidate.score))
        .where(StoryCandidate.status != "REJECTED")
        .order_by(desc(StoryCandidate.total_score), desc(StoryCandidate.discovered_at))
        .limit(10)
    ).all()
    keywords = db.execute(
        select(StoryCandidate.query, func.count(StoryCandidate.id), func.avg(StoryCandidate.total_score))
        .group_by(StoryCandidate.query).order_by(desc(func.avg(StoryCandidate.total_score))).limit(6)
    ).all()
    sources = db.execute(
        select(StoryCandidate.source, func.count(StoryCandidate.id), func.avg(StoryCandidate.total_score))
        .group_by(StoryCandidate.source).order_by(desc(func.avg(StoryCandidate.total_score)))
    ).all()
    return {
        "counts": counts,
        "top_stories": [StoryOut.model_validate(item) for item in top],
        "top_keywords": [{"name": name, "count": count, "average_score": round(avg or 0, 1)} for name, count, avg in keywords],
        "top_sources": [{"name": name, "count": count, "average_score": round(avg or 0, 1)} for name, count, avg in sources],
    }


@router.post("/search")
async def search(request: SearchRequest, db: Session = Depends(get_db)) -> dict:
    runs = await execute_search(db, request)
    return {"runs": [_run_dict(run) for run in runs], "new_results": sum(run.new_results for run in runs), "errors": [run.errors for run in runs if run.errors]}


@router.post("/search/presets")
async def search_presets(
    source: str = Query(default="demo", pattern="^(demo|threads|reddit)$"),
    limit_queries: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    queries = db.scalars(select(SearchQuery.phrase).where(SearchQuery.enabled.is_(True)).limit(limit_queries)).all()
    return await search(SearchRequest(queries=list(queries), sources=[source], limit=10), db)


@router.get("/search-runs")
def search_runs(page: int = 1, page_size: int = Query(default=25, le=100), db: Session = Depends(get_db)) -> dict:
    total = db.scalar(select(func.count()).select_from(SearchRun)) or 0
    rows = db.scalars(select(SearchRun).order_by(desc(SearchRun.started_at)).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [_run_dict(row) for row in rows], "total": total, "page": page, "pages": max(1, math.ceil(total / page_size))}


@router.post("/search-runs/{run_id}/retry")
async def retry_search(run_id: int, db: Session = Depends(get_db)) -> dict:
    run = db.get(SearchRun, run_id)
    if not run:
        raise HTTPException(404, "Không tìm thấy lần tìm kiếm")
    values = dict(run.options_json or {})
    values["queries"] = [run.query]
    values["sources"] = [run.source]
    request = SearchRequest.model_validate(values)
    return await search(request, db)


@router.get("/stories", response_model=PaginatedStories)
def stories(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    source: str | None = None,
    min_score: int = Query(default=0, ge=0, le=100),
    q: str | None = None,
    demo: bool | None = None,
    sort: str = Query(default="score", pattern="^(score|recent|oldest)$"),
    db: Session = Depends(get_db),
) -> PaginatedStories:
    statement = select(StoryCandidate).options(joinedload(StoryCandidate.score))
    count_statement = select(func.count()).select_from(StoryCandidate)
    filters = [StoryCandidate.total_score >= min_score]
    if status:
        filters.append(StoryCandidate.status == status)
    if source:
        filters.append(StoryCandidate.source == source)
    if demo is not None:
        filters.append(StoryCandidate.is_demo.is_(demo))
    if q:
        pattern = f"%{q.strip()}%"
        filters.append(StoryCandidate.title.ilike(pattern) | StoryCandidate.text.ilike(pattern))
    statement = statement.where(*filters)
    count_statement = count_statement.where(*filters)
    ordering = StoryCandidate.total_score.desc() if sort == "score" else (StoryCandidate.discovered_at.asc() if sort == "oldest" else StoryCandidate.discovered_at.desc())
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.order_by(ordering).offset((page - 1) * page_size).limit(page_size)).all()
    return PaginatedStories(items=[StoryOut.model_validate(item) for item in items], total=total, page=page, page_size=page_size, pages=max(1, math.ceil(total / page_size)))


@router.get("/stories/{story_id}", response_model=StoryOut)
def story_detail(story_id: int, db: Session = Depends(get_db)) -> StoryOut:
    story = db.scalar(select(StoryCandidate).options(joinedload(StoryCandidate.score)).where(StoryCandidate.id == story_id))
    if not story:
        raise HTTPException(404, "Không tìm thấy câu chuyện")
    return StoryOut.model_validate(story)


@router.patch("/stories/{story_id}", response_model=StoryOut)
def update_story(story_id: int, update: StoryUpdate, db: Session = Depends(get_db)) -> StoryOut:
    story = db.get(StoryCandidate, story_id)
    if not story:
        raise HTTPException(404, "Không tìm thấy câu chuyện")
    values = update.model_dump(exclude_unset=True)
    previous_status = story.status
    for key, value in values.items():
        setattr(story, key, value)
    if update.status == "SAVED" and not db.scalar(select(SavedStory).where(SavedStory.story_id == story.id)):
        db.add(SavedStory(story_id=story.id))
        keyword = db.scalar(select(SearchQuery).where(SearchQuery.phrase == story.query))
        if keyword and previous_status != "SAVED":
            keyword.saved_count += 1
    db.commit()
    db.refresh(story)
    return StoryOut.model_validate(story)


@router.post("/stories/{story_id}/idea")
def new_idea(story_id: int, db: Session = Depends(get_db)) -> dict:
    story = db.scalar(select(StoryCandidate).options(joinedload(StoryCandidate.idea)).where(StoryCandidate.id == story_id))
    if not story:
        raise HTTPException(404, "Không tìm thấy câu chuyện")
    return _idea_dict(create_content_idea(db, story))


@router.post("/stories/{story_id}/analyze")
async def ai_analysis(story_id: int, db: Session = Depends(get_db)) -> dict:
    story = db.get(StoryCandidate, story_id)
    if not story:
        raise HTTPException(404, "Không tìm thấy câu chuyện")
    provider = _setting(db, "ai_provider", "openai")
    try:
        result, provider_name, model = await analyze_story(story.text, provider)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(400, str(exc)) from exc
    analysis = AIAnalysis(story_id=story.id, provider=provider_name, model=model, result_json=result)
    db.add(analysis)
    db.commit()
    return result


@router.get("/stories/{story_id}/analysis")
def latest_analysis(story_id: int, db: Session = Depends(get_db)) -> dict | None:
    row = db.scalar(select(AIAnalysis).where(AIAnalysis.story_id == story_id).order_by(desc(AIAnalysis.created_at)).limit(1))
    return row.result_json if row else None


@router.get("/ideas")
def ideas(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(ContentIdea).options(joinedload(ContentIdea.source_story)).order_by(desc(ContentIdea.updated_at))).all()
    return [_idea_dict(row) for row in rows]


@router.get("/ideas/{idea_id}")
def idea_detail(idea_id: int, db: Session = Depends(get_db)) -> dict:
    idea = db.get(ContentIdea, idea_id)
    if not idea:
        raise HTTPException(404, "Không tìm thấy ý tưởng")
    return _idea_dict(idea)


@router.patch("/ideas/{idea_id}")
def update_idea(idea_id: int, update: IdeaUpdate, db: Session = Depends(get_db)) -> dict:
    idea = db.get(ContentIdea, idea_id)
    if not idea:
        raise HTTPException(404, "Không tìm thấy ý tưởng")
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(idea, key, value)
    db.commit()
    db.refresh(idea)
    return _idea_dict(idea)


@router.get("/keywords")
def keywords(category: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    statement = select(SearchQuery).order_by(SearchQuery.category, SearchQuery.phrase)
    if category:
        statement = statement.where(SearchQuery.category == category)
    rows = db.scalars(statement).all()
    return [{
        "id": row.id, "phrase": row.phrase, "category": row.category, "language": row.language,
        "enabled": row.enabled, "queries_run": row.queries_run, "stories_found": row.stories_found,
        "saved_rate": round(row.saved_count / row.stories_found * 100, 1) if row.stories_found else 0,
        "average_score": round(row.score_total / row.stories_found, 1) if row.stories_found else 0,
    } for row in rows]


@router.post("/keywords", status_code=201)
def create_keyword(item: KeywordCreate, db: Session = Depends(get_db)) -> dict:
    if db.scalar(select(SearchQuery).where(SearchQuery.phrase == item.phrase)):
        raise HTTPException(409, "Từ khóa đã tồn tại")
    row = SearchQuery(**item.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, **item.model_dump()}


@router.patch("/keywords/{keyword_id}")
def update_keyword(keyword_id: int, item: KeywordUpdate, db: Session = Depends(get_db)) -> dict:
    row = db.get(SearchQuery, keyword_id)
    if not row:
        raise HTTPException(404, "Không tìm thấy từ khóa")
    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    return {"id": row.id, "phrase": row.phrase, "category": row.category, "language": row.language, "enabled": row.enabled}


@router.delete("/keywords/{keyword_id}", status_code=204)
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)) -> Response:
    row = db.get(SearchQuery, keyword_id)
    if not row:
        raise HTTPException(404, "Không tìm thấy từ khóa")
    db.delete(row)
    db.commit()
    return Response(status_code=204)


@router.get("/sources")
def sources(db: Session = Depends(get_db)) -> list[dict]:
    return _source_status(db)


@router.patch("/sources/{slug}")
def update_source(slug: str, enabled: bool, db: Session = Depends(get_db)) -> dict:
    row = db.scalar(select(Source).where(Source.slug == slug))
    if not row:
        raise HTTPException(404, "Không tìm thấy nguồn")
    row.enabled = enabled
    db.commit()
    return {"slug": row.slug, "enabled": row.enabled}


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)) -> dict:
    status_rows = db.execute(select(StoryCandidate.status, func.count()).group_by(StoryCandidate.status)).all()
    source_rows = db.execute(select(StoryCandidate.source, func.count(), func.avg(StoryCandidate.total_score)).group_by(StoryCandidate.source)).all()
    daily_rows = db.execute(
        select(func.date(StoryCandidate.discovered_at), func.count()).where(StoryCandidate.discovered_at >= datetime.now(timezone.utc) - timedelta(days=14)).group_by(func.date(StoryCandidate.discovered_at)).order_by(func.date(StoryCandidate.discovered_at))
    ).all()
    return {
        "by_status": [{"name": name, "value": value} for name, value in status_rows],
        "by_source": [{"name": name, "count": count, "average_score": round(avg or 0, 1)} for name, count, avg in source_rows],
        "daily": [{"date": date, "count": count} for date, count in daily_rows],
    }


@router.get("/settings")
def settings(db: Session = Depends(get_db)) -> dict:
    values = {row.key: row.value_json for row in db.scalars(select(Setting)).all()}
    config = get_config()
    return {
        **values,
        "threads_configured": bool(config.threads_access_token),
        "reddit_configured": bool(config.reddit_client_id and config.reddit_client_secret),
        "ai_enabled": config.ai_enabled,
        "ai_key_configured": bool(config.ai_api_key),
        "database_url": config.database_url.replace(str(get_config().database_url).split("///")[-1], "…/story_miner.db"),
    }


@router.patch("/settings")
def update_settings(item: SettingsUpdate, db: Session = Depends(get_db)) -> dict:
    for key, value in item.model_dump(exclude_unset=True).items():
        row = db.get(Setting, key)
        if row:
            row.value_json = value
        else:
            db.add(Setting(key=key, value_json=value))
    db.commit()
    return settings(db)


@router.get("/export/{kind}.{format}")
def export_data(kind: str, format: str, db: Session = Depends(get_db)) -> Response:
    if kind not in {"stories", "saved", "ideas"} or format not in {"csv", "json"}:
        raise HTTPException(404, "Định dạng xuất không hợp lệ")
    rows = _export_rows(db, kind)
    if format == "json":
        payload = json.dumps(rows, ensure_ascii=False, indent=2, default=str)
        return Response(payload, media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{kind}.json"'})
    stream = io.StringIO()
    if rows:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    payload = "\ufeff" + stream.getvalue()
    return Response(payload.encode("utf-8"), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{kind}.csv"'})


def _export_rows(db: Session, kind: str) -> list[dict[str, Any]]:
    if kind == "ideas":
        return [_idea_dict(row) for row in db.scalars(select(ContentIdea).options(joinedload(ContentIdea.source_story))).all()]
    statement = select(StoryCandidate)
    if kind == "saved":
        statement = statement.where(StoryCandidate.status == "SAVED")
    rows = db.scalars(statement.order_by(desc(StoryCandidate.discovered_at))).all()
    return [{
        "id": row.id, "title": row.title, "source": row.source, "source_url": row.source_url,
        "author": row.author, "created_at": row.created_at, "discovered_at": row.discovered_at,
        "query": row.query, "status": row.status, "score": row.total_score, "text": row.text,
        "is_demo": row.is_demo,
    } for row in rows]


def _source_status(db: Session) -> list[dict]:
    configured = adapters()
    return [{
        "slug": row.slug, "name": row.name, "enabled": row.enabled,
        "configured": configured[row.slug].configured, "kind": "demo" if row.slug == "demo" else "official_api",
        "message": "Sẵn sàng" if configured[row.slug].configured else ("Threads chưa được cấu hình." if row.slug == "threads" else "Reddit chưa được cấu hình."),
    } for row in db.scalars(select(Source).order_by(Source.id)).all()]


def _count(db: Session, condition) -> int:
    return db.scalar(select(func.count()).select_from(StoryCandidate).where(condition)) or 0


def _setting(db: Session, key: str, default: Any) -> Any:
    row = db.get(Setting, key)
    return row.value_json if row else default


def _run_dict(row: SearchRun) -> dict:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def _idea_dict(row: ContentIdea) -> dict:
    data = {column.name: getattr(row, column.name) for column in row.__table__.columns}
    if row.source_story:
        data["source"] = row.source_story.source
        data["source_url"] = row.source_story.source_url
        data["story_score"] = row.source_story.total_score
        data["is_demo"] = row.source_story.is_demo
    return data

