import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import ROOT_DIR
from app.models import SearchQuery, Setting, Source


def seed_defaults(db: Session) -> None:
    existing_sources = {row.slug for row in db.scalars(select(Source)).all()}
    for slug, name, enabled in [
        ("demo", "Dữ liệu minh họa", True),
        ("threads", "Threads", True),
        ("reddit", "Reddit", True),
    ]:
        if slug not in existing_sources:
            db.add(Source(slug=slug, name=name, enabled=enabled))

    if not db.scalar(select(SearchQuery.id).limit(1)):
        groups = json.loads((ROOT_DIR / "data" / "keywords" / "keywords.json").read_text(encoding="utf-8"))
        for group in groups:
            for phrase in group["phrases"]:
                db.add(SearchQuery(phrase=phrase, category=group["category"], language=group["language"]))

    defaults = {
        "setup_complete": False,
        "demo_mode": True,
        "duplicate_similarity_threshold": 0.88,
        "default_page_size": 25,
        "ai_provider": "openai",
    }
    existing_settings = {row.key for row in db.scalars(select(Setting)).all()}
    for key, value in defaults.items():
        if key not in existing_settings:
            db.add(Setting(key=key, value_json=value))
    db.commit()

