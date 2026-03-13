from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .api import projects, images, annotations, schemas, export, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="Poker YOLO Labeling API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(images.router, tags=["images"])
app.include_router(annotations.router, tags=["annotations"])
app.include_router(schemas.router, prefix="/schemas", tags=["schemas"])
app.include_router(export.router, tags=["export"])
app.include_router(tasks.router, tags=["tasks"])


@app.get("/health")
async def health():
    return {"status": "ok"}
