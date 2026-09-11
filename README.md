# Tôi Kể Chuyện Lạ — Story Miner

Ứng dụng Windows local-first để **khám phá → lọc → xếp hạng → lưu → phân tích → phát triển ý tưởng** từ các câu chuyện công khai. Story Miner giữ nguyên URL, nền tảng, tác giả và thời gian nguồn; phần “Ý tưởng nội dung” luôn tách khỏi văn bản gốc.

> Luôn kiểm tra nguồn và viết lại nội dung trước khi xuất bản. Không khẳng định một câu chuyện là thật nếu nguồn không chứng minh.

## Chạy nhanh trên Windows

Yêu cầu: Python 3.11+ và Node.js 20+.

1. Chạy `setup.bat` một lần. Script tạo `.venv`, cài dependency, build React, chạy migration và seed hơn 100 từ khóa.
2. Chạy `run.bat` ở các lần sau.
3. Trình duyệt tự mở tại <http://127.0.0.1:8765>.

Nếu PowerShell chặn `npm.ps1`, không cần thay execution policy: các script đã gọi `npm.cmd` trực tiếp.

## Tính năng

- Dashboard với thống kê, nguồn/từ khóa hiệu quả và top ứng viên.
- Discover hỗ trợ nhiều truy vấn, nhóm AND bằng dấu `+`, nguồn, khoảng ngày, ngôn ngữ, độ dài, media, replies, TOP/RECENT và điểm tối thiểu.
- Lịch sử từng search run, lỗi riêng theo nguồn và retry.
- Kho truyện phân trang, lọc, lưu, loại, ghi chú, đánh dấu trùng và mở nguồn.
- Bộ chấm điểm heuristic 0–100 với 8 thành phần, lý do và penalty hiển thị rõ.
- Phát hiện trùng chính xác theo source ID/URL và gần trùng bằng cosine similarity trên word bigram chuẩn hóa. Chỉ gắn cờ, không xóa.
- Content Idea tách biệt, biên tập được, có 3 hook, premise, outline Hook/Setup/Escalation/Twist/Payoff/CTA, loại câu chuyện và Kanban kéo-thả.
- Keyword Lab với hơn 100 truy vấn Việt/Anh, nhóm, bật/tắt, thống kê lượt chạy và tỷ lệ lưu.
- Xuất CSV UTF-8 BOM (mở đúng tiếng Việt trong Excel) và JSON.
- Setup wizard, demo mode, SQLite/WAL, structured rotating logs và AI tùy chọn.
- Secrets chỉ đọc từ `.env` phía server, không bao giờ trả về frontend.

## Cấu hình `.env`

`setup.bat` tạo `.env` từ `.env.example` nếu chưa có. Điền credential rồi khởi động lại `run.bat`.

### Threads API

Adapter dùng API chính thức của Meta:

```text
GET https://graph.threads.net/v1.0/keyword_search
q=...
search_type=TOP|RECENT
search_mode=KEYWORD
fields=id,media_product_type,media_type,permalink,username,text,timestamp,shortcode,is_quote_post,has_replies
```

Meta hiện yêu cầu token có `threads_basic` và `threads_keyword_search`; quyền keyword search có thể cần App Review/Advanced Access. Endpoint hỗ trợ `limit`, `since`, `until` và cursor pagination. Xem [Meta Threads Keyword Search](https://developers.facebook.com/docs/threads/keyword-search) và [collection chính thức của Meta trên Postman](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api). Nếu chưa có quyền, adapter báo “Threads chưa được cấu hình” và Demo/Reddit vẫn hoạt động.

```env
THREADS_ACCESS_TOKEN=...
THREADS_APP_ID=...
THREADS_APP_SECRET=...
```

Ứng dụng không giả lập endpoint, không lấy cookie và không vượt CAPTCHA/access control.

### Reddit

Tạo OAuth application tại Reddit, lấy client ID/secret, rồi cấu hình:

```env
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=windows:story-miner:1.0 (local research tool; contact: you)
```

Adapter dùng OAuth client-credentials và endpoint `/search` chính thức. Kết quả giữ permalink/tác giả/metadata; ý tưởng không tự chép toàn bộ bài dài. Xem [Reddit API docs](https://www.reddit.com/dev/api/#GET_search).

### AI tùy chọn

Mặc định `AI_ENABLED=false`. Heuristic không cần AI. Với API OpenAI-compatible:

```env
AI_ENABLED=true
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=...
AI_MODEL=gpt-4.1-mini
```

Với Ollama, chọn provider `ollama` trong Cài đặt, đặt `OLLAMA_BASE_URL`, và dùng tên model phù hợp trong `AI_MODEL`. Chỉ JSON phân tích ngắn được lưu; không lưu chain-of-thought.

## Dữ liệu, sao lưu và log

- Database mặc định: `data/story_miner.db`.
- Log: `logs/app.log`, xoay vòng tối đa 3 bản.
- Sao lưu: dừng `run.bat`, sau đó sao chép `data/story_miner.db` sang nơi an toàn.
- Khôi phục: dừng app và thay database bằng bản sao lưu cùng phiên bản schema.
- Demo story luôn có nhãn `DEMO DATA`, dùng URL `example.com`, và không bị trộn lẫn với dữ liệu crawl thật (`is_demo` được lưu riêng).

## Kiến trúc

```text
Browser / React + TypeScript + Tailwind
                 │ /api
FastAPI routes ──┼── Search orchestration ── Threads / Reddit / Demo adapters
                 ├── Heuristic scoring
                 ├── Duplicate detection
                 ├── Optional AI provider
                 └── SQLAlchemy + SQLite + Alembic
```

Backend phục vụ frontend production build trên cùng cổng `8765`. Adapter nguồn trả về một `StoryPayload` thống nhất; nguồn mới có thể triển khai `SourceAdapter` mà không đổi workflow lưu/chấm điểm.

## Project structure

```text
backend/app/api          FastAPI endpoints
backend/app/models       SQLAlchemy entities
backend/app/sources      Source adapters and resilient HTTP client
backend/app/scoring      Deterministic scoring engine
backend/app/services     Search, duplicates, seed, content ideas
backend/app/ai           Optional OpenAI-compatible provider
backend/alembic          Database migrations
backend/tests            Unit and integration tests
frontend/src/pages       All application screens
frontend/src/components  Shared UI
data/keywords            Seed dataset
data/demo                Clearly marked demo stories
```

## Testing

From the project root after setup:

```bat
set PYTHONPATH=%CD%\backend
.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm.cmd run build
npx.cmd playwright test
```

External API tests use mock transports and never require real credentials. Playwright may first require `npx.cmd playwright install chromium`.

## Troubleshooting

- **Frontend chưa được build**: run `setup.bat` again.
- **Port 8765 đang dùng**: close the other local process or run Uvicorn manually on another port.
- **Threads 400/403**: confirm a Threads user token, `threads_basic`, `threads_keyword_search`, app review status, and token expiry.
- **Reddit 401/403**: verify the OAuth app ID/secret and use a descriptive user-agent.
- **Database locked**: make sure only one Story Miner backend is running. WAL mode handles ordinary browser concurrency.
- **See a generic server error**: inspect `logs/app.log`; access tokens are never logged.

## Known limitations

- Threads search availability and quotas are controlled by Meta and may require app review. Engagement metrics on public keyword results are limited to fields returned by that endpoint; unavailable values remain `null`.
- Reddit app access is required; there is no browser scraping fallback.
- Near-duplicate comparison is capped to the 1,000 most recent candidates per insert for predictable local performance. Exact ID/URL detection covers the full indexed database.
- `+` groups require every term in Demo mode. External providers receive the grouped query through their supported search syntax, so exact boolean behavior depends on that official API.
- No automatic publishing, private-content access, CAPTCHA handling, or platform-control bypass is implemented.

## Security model

Single-user service bound to `127.0.0.1`; secrets stay in ignored `.env`; API errors are sanitized; user input is validated by Pydantic; database queries use SQLAlchemy parameters; source failures are isolated. Do not expose port 8765 to a public network without adding authentication and HTTPS.
