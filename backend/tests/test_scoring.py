from app.scoring import score_story


def test_narrative_horror_scores_above_spam():
    narrative = "Mình ở nhà một mình. Đêm hôm đó camera ghi được bóng người. Sau đó tôi phát hiện người ấy đã chết. Đến giờ vẫn không giải thích được."
    spam = "Giảm giá! Mua ngay, inbox giá, giveaway tại https://example.com"
    good = score_story(narrative, "threads", 20, 100)
    bad = score_story(spam, "threads")
    assert good.total_score > bad.total_score
    assert good.horror_score > 0
    assert "Có ngôi kể thứ nhất" in good.reasons
    assert bad.penalties


def test_all_dimensions_are_bounded():
    result = score_story("ma " * 100 + "đột nhiên hóa ra không ai biết mình rất sợ", "reddit")
    for name, value in result.to_dict().items():
        if name.endswith("_score"):
            assert 0 <= value <= 100

