from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

from .routes import router


def make_app() -> FastAPI:
    app = FastAPI(
        openapi_url="",
        docs_url=None,
        redoc_url=None,
    )
    app.include_router(router)
    mcp = FastApiMCP(app)
    mcp.mount()
    return app
