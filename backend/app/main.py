import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_config
from app.core.logging import configure_logging
from app.database import SessionLocal, init_database
from app.services.seed import seed_defaults

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_database()
    with SessionLocal() as db:
        seed_defaults(db)
    logger.info("startup app=%s", get_config().app_name)
    yield


app = FastAPI(title=get_config().app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.exception_handler(Exception)
async def unhandled_exception(_request: Request, exc: Exception):
    logger.exception("unhandled_error")
    return JSONResponse(status_code=500, content={"detail": "Đã xảy ra lỗi nội bộ. Xem logs/app.log để biết chi tiết."})


frontend = Path(get_config().frontend_dist)
assets = frontend / "assets"
if assets.exists():
    app.mount("/assets", StaticFiles(directory=assets), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def frontend_app(full_path: str):
    index = frontend / "index.html"
    if index.exists():
        candidate = (frontend / full_path).resolve()
        if full_path and candidate.is_file() and frontend.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index)
    return JSONResponse({"detail": "Frontend chưa được build. Chạy setup.bat."}, status_code=503)

