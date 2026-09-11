from sqlalchemy.orm import Session

from app.models import ContentIdea, StoryCandidate


def create_content_idea(db: Session, story: StoryCandidate) -> ContentIdea:
    if story.idea:
        return story.idea
    title = story.title.strip().rstrip(".?!")
    premise = _premise(story.text)
    idea = ContentIdea(
        source_story_id=story.id,
        working_title=f"Chuyện lạ: {title[:90]}",
        premise=premise,
        hook_1=f"Điều gì sẽ xảy ra nếu {premise[:160].lower()}?",
        hook_2=f"Một câu chuyện từ {story.source.title()} bắt đầu rất bình thường — cho đến chi tiết không ai giải thích được.",
        hook_3=f"{title}. Nhưng phần đáng sợ nhất lại nằm ở cuối câu chuyện.",
        story_outline=(
            "HOOK: Đặt câu hỏi hoặc hình ảnh gây tò mò, không khẳng định câu chuyện là thật.\n\n"
            f"SETUP: Giới thiệu bối cảnh và nhân vật từ tiền đề: {premise}\n\n"
            "ESCALATION: Chọn 2–3 sự kiện làm mức độ bất thường tăng dần; viết lại bằng lời kể riêng.\n\n"
            "TWIST: Chỉ dùng chi tiết có trong nguồn hoặc ghi rõ đây là giả thuyết/chuyển thể.\n\n"
            "PAYOFF: Kết lại điều bí ẩn và nhắc người xem đây là lời kể/nguồn tham khảo.\n\n"
            "CTA: Hỏi khán giả cách họ lý giải sự việc."
        ),
        suggested_video_length=75 if len(story.text) > 500 else 55,
        ending_question="Nếu ở trong tình huống này, bạn sẽ làm gì?",
        visual_background="B-roll tối giản theo bối cảnh, phụ đề rõ, tránh dùng hình ảnh nhận dạng cá nhân từ nguồn.",
        story_type="PERSONAL ANECDOTE" if any(word in story.text.lower() for word in ["mình", "tôi", "tui", "em từng", " i "]) else "UNKNOWN",
        category=(story.tags[0] if story.tags else "Chuyện lạ"),
    )
    story.status = "SAVED"
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def _premise(text: str) -> str:
    clean = " ".join(text.split())
    sentences = [part.strip() for part in clean.replace("!", ".").replace("?", ".").split(".") if part.strip()]
    return ". ".join(sentences[:2])[:500] or clean[:500]

