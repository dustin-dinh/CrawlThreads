import re
from dataclasses import asdict, dataclass, field


@dataclass
class ScoreResult:
    hook_score: int
    curiosity_score: int
    horror_score: int
    twist_score: int
    emotion_score: int
    story_structure_score: int
    short_video_fit_score: int
    source_quality_score: int
    total_score: int
    penalties: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


FIRST_PERSON = ["mình", "tôi", "em", "tui", "we ", " i ", "my "]
PROGRESSION = ["hôm đó", "sau đó", "đột nhiên", "cho đến khi", "sáng hôm sau", "nhưng", "lúc đó", "then", "suddenly", "until"]
HORROR = ["ma", "bóng người", "tiếng khóc", "gõ cửa", "máu", "người lạ", "3 giờ sáng", "chết", "mất tích", "camera", "cctv", "bệnh viện", "nghĩa trang", "ám ảnh", "kinh dị", "ghost", "haunted", "scream", "dead", "blood", "paranormal"]
CURIOSITY = ["không hiểu sao", "không ai biết", "không giải thích được", "cho đến giờ", "điều kỳ lạ", "nhưng rồi", "đáng sợ nhất", "unexplained", "nobody knows", "strangest", "what happened next"]
TWIST = ["hóa ra", "thì ra", "nhưng không phải", "đến khi xem lại", "phát hiện", "cuối cùng", "turns out", "wasn't", "realized", "footage"]
EMOTION = ["sợ", "run", "khóc", "ám ảnh", "hoảng", "lạnh người", "rùng mình", "terrified", "afraid", "crying", "panic", "chills"]
SPAM = ["giảm giá", "khuyến mãi", "giveaway", "mua ngay", "inbox giá", "affiliate", "sale off"]
POLITICS = ["bầu cử", "quốc hội", "đảng phái", "election", "politician"]


def _term_score(text: str, terms: list[str], base: int, cap: int = 100) -> tuple[int, int]:
    count = sum(1 for term in terms if term in text)
    return min(cap, count * base), count


def score_story(text: str, source: str = "unknown", reply_count: int | None = None, like_count: int | None = None) -> ScoreResult:
    clean = " " + re.sub(r"\s+", " ", text.lower()).strip() + " "
    length = len(clean)
    words = clean.split()
    penalties: list[str] = []
    reasons: list[str] = []

    first_points, first_hits = _term_score(clean, FIRST_PERSON, 18, 36)
    progression_points, progression_hits = _term_score(clean, PROGRESSION, 13, 52)
    horror_score, horror_hits = _term_score(clean, HORROR, 13)
    curiosity_score, curiosity_hits = _term_score(clean, CURIOSITY, 19)
    twist_score, twist_hits = _term_score(clean, TWIST, 22)
    emotion_score, emotion_hits = _term_score(clean, EMOTION, 17)

    hook_score = min(100, first_points + curiosity_points(clean[:260]) + (15 if "?" in clean[:260] else 0))
    story_structure_score = min(100, first_points + progression_points + (15 if twist_hits else 0))
    if 220 <= length <= 1800:
        short_video_fit_score = 88
    elif 100 <= length < 220 or 1800 < length <= 3200:
        short_video_fit_score = 65
    elif 60 <= length < 100 or 3200 < length <= 5000:
        short_video_fit_score = 42
    else:
        short_video_fit_score = 20

    source_quality_score = {"threads": 76, "reddit": 82, "demo": 68}.get(source.lower(), 60)
    engagement = (reply_count or 0) + min((like_count or 0) // 5, 20)
    source_quality_score = min(100, source_quality_score + min(engagement, 20))

    penalty = 0
    if length < 60:
        penalties.append("Văn bản quá ngắn")
        penalty += 22
    if length > 5000 and progression_hits < 2:
        penalties.append("Văn bản dài nhưng thiếu diễn tiến")
        penalty += 14
    if any(term in clean for term in SPAM):
        penalties.append("Có tín hiệu quảng cáo/spam")
        penalty += 35
    if any(term in clean for term in POLITICS) and horror_hits == 0:
        penalties.append("Chủ đề chính trị không liên quan")
        penalty += 24
    if len(words) < 20 and ("http://" in clean or "https://" in clean):
        penalties.append("Nội dung chủ yếu là liên kết")
        penalty += 25

    if first_hits:
        reasons.append("Có ngôi kể thứ nhất")
    if progression_hits >= 2:
        reasons.append("Có diễn tiến câu chuyện")
    if horror_hits:
        reasons.append(f"Có {horror_hits} tín hiệu kinh dị/bí ẩn")
    if curiosity_hits:
        reasons.append("Tạo khoảng trống tò mò")
    if twist_hits:
        reasons.append("Có dấu hiệu nút thắt hoặc cú lật")

    dimensions = [hook_score, curiosity_score, horror_score, twist_score, emotion_score, story_structure_score, short_video_fit_score, source_quality_score]
    weights = [0.15, 0.14, 0.16, 0.13, 0.10, 0.13, 0.13, 0.06]
    total = max(0, min(100, round(sum(s * w for s, w in zip(dimensions, weights)) - penalty)))
    return ScoreResult(
        hook_score=hook_score,
        curiosity_score=curiosity_score,
        horror_score=horror_score,
        twist_score=twist_score,
        emotion_score=emotion_score,
        story_structure_score=story_structure_score,
        short_video_fit_score=short_video_fit_score,
        source_quality_score=source_quality_score,
        total_score=total,
        penalties=penalties,
        reasons=reasons,
    )


def curiosity_points(text: str) -> int:
    points, _ = _term_score(text, CURIOSITY, 20, 60)
    return points

