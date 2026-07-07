from pydantic import BaseModel
from fastapi import APIRouter


class APIEndpointInfo(BaseModel):
    method: str
    path: str
    description: str


class APICapabilityInfo(BaseModel):
    key: str
    label: str
    description: str
    endpoints: list[APIEndpointInfo]


class APIIndexResponse(BaseModel):
    name: str
    version: str
    description: str
    capabilities: list[APICapabilityInfo]


router = APIRouter(tags=["api"])


@router.get("/api", response_model=APIIndexResponse)
def get_api_index() -> APIIndexResponse:
    """
    Return a human-readable index of DAMA backend API capabilities.
    """
    return APIIndexResponse(
        name="DAMA Backend API",
        version="1.0.0",
        description="AI content automation backend API for local model generation, prompt-driven content, providers, and system status.",
        capabilities=[
            APICapabilityInfo(
                key="models",
                label="Models",
                description="Inspect locally available AI models.",
                endpoints=[
                    APIEndpointInfo(
                        method="GET",
                        path="/models",
                        description="List locally available Ollama models.",
                    ),
                ],
            ),
            APICapabilityInfo(
                key="generation",
                label="Text Generation",
                description="Generate raw text using supported AI providers.",
                endpoints=[
                    APIEndpointInfo(
                        method="POST",
                        path="/generate",
                        description="Generate text from a direct prompt or a prompt template.",
                    ),
                ],
            ),
            APICapabilityInfo(
                key="content",
                label="Content Generation",
                description="Generate structured production content using standard content types.",
                endpoints=[
                    APIEndpointInfo(
                        method="GET",
                        path="/content/types",
                        description="List supported content generation types.",
                    ),
                    APIEndpointInfo(
                        method="GET",
                        path="/content/types/{key}",
                        description="Get one content type definition by key.",
                    ),
                    APIEndpointInfo(
                        method="POST",
                        path="/content/generate",
                        description="Generate structured content using a standard content type.",
                    ),
                ],
            ),
            APICapabilityInfo(
                key="providers",
                label="AI Providers",
                description="Inspect supported AI provider integrations.",
                endpoints=[
                    APIEndpointInfo(
                        method="GET",
                        path="/providers",
                        description="List supported AI providers.",
                    ),
                    APIEndpointInfo(
                        method="GET",
                        path="/providers/{key}",
                        description="Get one AI provider definition by key.",
                    ),
                ],
            ),
            APICapabilityInfo(
                key="system",
                label="System",
                description="Inspect backend runtime status.",
                endpoints=[
                    APIEndpointInfo(
                        method="GET",
                        path="/system/status",
                        description="Get aggregated DAMA backend system status.",
                    ),
                ],
            ),
        ],
    )
