from fastapi import FastAPI

from src.api import health_router, content_router, models_router
from src.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(content_router)
app.include_router(models_router)


@app.get("/")
async def root():
    return {
        "project": settings.APP_NAME,
        "status": "running"
    }
