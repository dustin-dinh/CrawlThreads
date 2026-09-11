from sqlalchemy import select

from app.models import ContentIdea, StoryCandidate, StoryScore
from app.services.ideas import create_content_idea
from app.services.duplicates import normalize_text


def test_story_crud_and_content_idea_persist(db):
    story = StoryCandidate(
        external_id="test-1", source="demo", source_url="https://example.com/test-1",
        author="tester", text="Mình từng gặp một chuyện lạ. Sau đó camera ghi được bóng người.",
        normalized_text=normalize_text("Mình từng gặp một chuyện lạ."), title="Chuyện thử",
        query="chuyện lạ", tags=["Test"], total_score=70,
    )
    story.score = StoryScore(hook_score=70, curiosity_score=60, horror_score=80, twist_score=40, emotion_score=50, story_structure_score=60, short_video_fit_score=75, source_quality_score=60)
    db.add(story); db.commit(); db.refresh(story)
    found = db.scalar(select(StoryCandidate).where(StoryCandidate.external_id == "test-1"))
    assert found and found.score.horror_score == 80
    idea = create_content_idea(db, found)
    assert db.get(ContentIdea, idea.id).source_story_id == story.id
    assert found.status == "SAVED"

