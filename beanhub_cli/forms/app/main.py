import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_wtf import CSRFProtectMiddleware

from . import constants
from .routes import router
from .settings import settings

logging.basicConfig(level=logging.INFO if not settings.DEBUG_LOG else logging.DEBUG)


def make_app() -> FastAPI:
    app = FastAPI(
        openapi_url="",
        middleware=[
            Middleware(
                SessionMiddleware,
                secret_key=settings.SECRET_KEY,
                max_age=settings.SESSION_MAX_AGE,
            ),
            Middleware(CSRFProtectMiddleware, csrf_secret=settings.SECRET_KEY),
        ],
        docs_url=None,
        redoc_url=None,
    )

    app.include_router(router)
    app.mount(
        "/static",
        StaticFiles(directory=constants.FORMS_PACKAGE_DIR / "app" / "static"),
        name="static",
    )
    return app
