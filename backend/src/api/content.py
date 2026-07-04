from fastapi import APIRouter, Form

router = APIRouter(
    prefix="/api/v1/content",
    tags=["Content"]
)

@router.post("/")
async def create_content(
    title: str = Form(...),
    description: str = Form(...)
):
    return {
        "message": "Content received",
        "title": title,
        "description": description
    }