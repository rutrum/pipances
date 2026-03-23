import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from pipances.db import create_tables
from pipances.routes.data import router as data_router
from pipances.routes.explore import router as explore_router
from pipances.routes.import_page import router as import_router
from pipances.routes.inbox import router as inbox_router
from pipances.routes.transactions import router as transactions_router
from pipances.routes.widgets import router as widgets_router

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = Path(os.environ.get("PIPANCES_STATIC_DIR", str(PROJECT_ROOT / "static")))


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

app.include_router(explore_router)
app.include_router(inbox_router)
app.include_router(data_router)
app.include_router(transactions_router)
app.include_router(import_router)
app.include_router(widgets_router)


@app.get("/")
async def index():
    return RedirectResponse(url="/explore")


if __name__ == "__main__":
    uvicorn.run("pipances.main:app", host="127.0.0.1", port=8097, reload=True)
