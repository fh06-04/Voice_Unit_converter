"""FastAPI server for the Voice Unit Converter."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import database
from config import settings
from converter import ConversionError, convert_text, list_units
from logging_config import setup_logging

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
log = logging.getLogger("voice-converter")


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    database.init_db()
    log.info("Database ready at %s", settings.db_path)
    yield


app = FastAPI(title="Voice Unit Converter", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ConvertRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/convert")
def api_convert(req: ConvertRequest) -> dict:
    try:
        result = convert_text(req.text).to_dict()
    except ConversionError as exc:
        log.info("Rejected %r: %s", req.text, exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result["id"] = database.add_history(req.text.strip(), result["display"], result["category"])
    result["query"] = req.text.strip()
    return result


@app.get("/api/units")
def api_units() -> dict:
    return list_units()


@app.get("/api/history")
def api_history(limit: int = Query(default=settings.history_limit, ge=1, le=100)) -> list[dict]:
    return database.list_history(limit)


@app.delete("/api/history")
def api_clear_history() -> dict:
    database.clear_history()
    return {"cleared": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port)
