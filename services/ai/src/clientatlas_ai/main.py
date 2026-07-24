from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from jwt import InvalidTokenError

app = FastAPI(
    title="ClientAtlas AI Service",
    description="Ingestion, retrieval, generation, and evaluation APIs.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)


@app.exception_handler(InvalidTokenError)
async def invalid_token_handler(
    _request: Request,
    _error: InvalidTokenError,
) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"error": {"code": "invalid_access_token"}},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.get("/health", tags=["operations"])
async def health() -> dict[str, object]:
    return {
        "data": {
            "service": "clientatlas-ai",
            "status": "ok",
        }
    }
