import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from financial_pipeline.db import create_tables
from financial_pipeline.routes.dashboard import router as dashboard_router
from financial_pipeline.routes.inbox import router as inbox_router
from financial_pipeline.routes.settings import router as settings_router
from financial_pipeline.routes.transactions import router as transactions_router
from financial_pipeline.routes.upload import router as upload_router
from financial_pipeline.routes.widgets import router as widgets_router

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = Path(
    os.environ.get("FINANCIAL_PIPELINE_STATIC_DIR", str(PROJECT_ROOT / "static"))
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await create_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR, follow_symlink=True),
    name="static",
)

app.include_router(dashboard_router)
app.include_router(inbox_router)
app.include_router(settings_router)
app.include_router(transactions_router)
app.include_router(upload_router)
app.include_router(widgets_router)


@app.get("/")
async def index():
    return RedirectResponse(url="/dashboard")


if __name__ == "__main__":
    uvicorn.run("financial_pipeline.main:app", host="127.0.0.1", port=8097, reload=True)
