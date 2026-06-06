from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .frontend import frontend_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="EAGL Frontend",
    description="Frontend pages for the EAGL system",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(frontend_router)
