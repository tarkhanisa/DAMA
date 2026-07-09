from __future__ import annotations
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from typing import Any

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.content import router as content_router
from src.api.content_assets import router as content_assets_router
from src.api.content_generation import router as content_generation_router
from src.api.dashboard import router as dashboard_router
from src.api.developer import router as developer_router
from src.api.exports import router as exports_router
from src.api.generate import router as generate_router
from src.api.health import router as health_router
from src.api.index import router as index_router
from src.api.maintenance import router as maintenance_router
from src.api.models import router as models_router
from src.api.projects import router as projects_router
from src.api.search import router as search_router
from src.api.providers import router as providers_router
from src.api.system import router as system_router
from src.api.workflows import router as workflows_router


app = FastAPI(
    title="DAMA Backend",
    description="AI Content Automation Platform backend.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3001",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "status_code": exc.status_code,
                "message": str(exc.detail),
                "path": request.url.path,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "status_code": 422,
                "message": "Request validation failed.",
                "path": request.url.path,
                "details": exc.errors(),
            }
        },
    )


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "DAMA",
        "status": "running",
        "api": "/api",
        "docs": "/docs",
    }


app.include_router(index_router)
app.include_router(health_router)
app.include_router(content_router)
app.include_router(models_router)
app.include_router(generate_router)
app.include_router(content_generation_router)
app.include_router(providers_router)
app.include_router(system_router)
app.include_router(projects_router)
app.include_router(search_router)
app.include_router(content_assets_router)
app.include_router(workflows_router)
app.include_router(exports_router)
app.include_router(dashboard_router)
app.include_router(maintenance_router)
app.include_router(developer_router)
