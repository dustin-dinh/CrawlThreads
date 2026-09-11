import json

import httpx

from app.core.config import get_config


SYSTEM_PROMPT = """Bạn là trợ lý biên tập nội dung ngắn. Phân tích câu chuyện làm dữ liệu nghiên cứu, không sao chép và không khẳng định là thật. Chỉ trả JSON với các khóa: summary, hook_score, curiosity_score, horror_score, twist_score, viral_potential, recommended_duration_seconds, suggested_angles, risk_flags, reasoning_summary. Điểm từ 0 đến 100; reasoning_summary phải ngắn gọn, không đưa chuỗi suy luận nội bộ."""


async def analyze_story(text: str, provider: str = "openai") -> tuple[dict, str, str]:
    config = get_config()
    if not config.ai_enabled:
        raise ValueError("AI đang tắt. Đặt AI_ENABLED=true trong .env để sử dụng.")
    if provider == "ollama":
        base_url, api_key, model = config.ollama_base_url, "ollama", config.ai_model
    else:
        base_url, api_key, model = config.ai_base_url, config.ai_api_key, config.ai_model
    if provider != "ollama" and not api_key:
        raise ValueError("Chưa cấu hình AI_API_KEY.")
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text[:12000]},
                ],
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content), provider, model
