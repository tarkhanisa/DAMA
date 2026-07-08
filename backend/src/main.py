from fastapi import FastAPI

from src.api import (
    health_router,
    content_router,
    models_router,
    generate_router,
    content_generation_router,
    providers_router,
    system_router,
    index_router,
)
from src.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0"
)

app.include_router(index_router)
app.include_router(health_router)
app.include_router(content_router)
app.include_router(models_router)
app.include_router(generate_router)
app.include_router(content_generation_router)
app.include_router(providers_router)
app.include_router(system_router)


@app.get("/")
async def root():
    return {
        "project": settings.APP_NAME,
        "status": "running"
    }

from src.api.projects import router as projects_router

app.include_router(projects_router)

from src.api.content_assets import router as content_assets_router

app.include_router(content_assets_router)

from src.api.workflows import router as workflows_router

app.include_router(workflows_router)

from src.api.exports import router as exports_router

app.include_router(exports_router)
