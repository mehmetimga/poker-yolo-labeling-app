from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .api import projects, images, annotations, schemas, export, tasks, training
from .api import auth_router, users as users_api, review, assignments, dashboard

# Ensure all models are imported so Base.metadata knows about them
from .models import user as _user_model  # noqa: F401
from .models import auth_models as _auth_models  # noqa: F401

from .services.auth_service import create_admin_if_none
from .database import async_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    # Seed admin user if no users exist
    async with async_session() as db:
        await create_admin_if_none(
            db,
            username=settings.default_admin_username,
            password=settings.default_admin_password,
            email=settings.default_admin_email,
        )
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
app.include_router(training.router, tags=["training"])
app.include_router(auth_router.router, tags=["auth"])
app.include_router(users_api.router, tags=["users"])
app.include_router(review.router, tags=["review"])
app.include_router(assignments.router, tags=["assignments"])
app.include_router(dashboard.router, tags=["dashboard"])


@app.get("/health")
async def health():
    return {"status": "ok"}
