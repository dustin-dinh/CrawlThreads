import pytest
from sqlalchemy import func, select

from app.models import SearchRun, StoryCandidate
from app.schemas.api import SearchRequest
from app.services.search import execute_search
from app.services.seed import seed_defaults


@pytest.mark.asyncio
async def test_demo_search_end_to_end_and_exact_duplicate(db):
    seed_defaults(db)
    request=SearchRequest(queries=["camera + bóng người"],sources=["demo"],min_text_length=20)
    first=await execute_search(db,request)
    assert first[0].status=="COMPLETED"
    assert first[0].new_results>=1
    count=db.scalar(select(func.count()).select_from(StoryCandidate))
    second=await execute_search(db,request)
    assert second[0].duplicates>=1
    assert db.scalar(select(func.count()).select_from(StoryCandidate))==count
    assert db.scalar(select(func.count()).select_from(SearchRun))==2

