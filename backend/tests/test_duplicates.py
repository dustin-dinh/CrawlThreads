from app.services.duplicates import cosine_similarity, normalize_text


def test_normalization_removes_urls_punctuation_and_whitespace():
    assert normalize_text("  Chuyện, MA! https://example.com/x \n LẠ  ") == "chuyện ma lạ"


def test_near_duplicate_similarity():
    original = "Mình nghe tiếng gõ cửa lúc ba giờ sáng và nhìn thấy một bóng người ngoài hành lang"
    duplicate = "Mình nghe tiếng gõ cửa lúc ba giờ sáng, và nhìn thấy một bóng người ngoài hành lang!"
    unrelated = "Hôm nay trời đẹp và tôi đi mua một ly cà phê"
    assert cosine_similarity(original, duplicate) > 0.95
    assert cosine_similarity(original, unrelated) < 0.2

