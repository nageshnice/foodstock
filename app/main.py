from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import SecurityHeadersMiddleware
from app.database.session import close_database
from app.routers.admin import router as admin_router
from app.routers.admin_events import router as admin_events_router
from app.routers.auth import router as auth_router
from app.routers.cart import router as cart_router
from app.routers.catalog import router as catalog_router
from app.routers.customer import router as customer_router
from app.routers.health import router as health_router
from app.routers.orders import router as orders_router
from app.utils.constants import API_DESCRIPTION, API_PREFIX, API_VERSION


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await close_database()


def add_cors_middleware(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def create_application() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    root = settings.root_path.rstrip("/")
    docs_url = f"{root}/docs" if root else "/docs"
    openapi_url = f"{root}/openapi.json" if root else "/openapi.json"
    redoc_url = f"{root}/redoc" if root else "/redoc"

    application = FastAPI(
        title=settings.app_name,
        description=API_DESCRIPTION,
        version=API_VERSION,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url=docs_url,
        openapi_url=openapi_url,
        redoc_url=redoc_url,
    )
    add_cors_middleware(application, settings)
    application.add_middleware(SecurityHeadersMiddleware)
    register_exception_handlers(application)

    admin_dist = Path(__file__).resolve().parent.parent / "admin" / "dist"
    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    uploads_mount = f"{root}/uploads" if root else "/uploads"
    application.mount(uploads_mount, StaticFiles(directory=str(uploads_dir)), name="uploads")

    if admin_dist.is_dir():
        application.mount("/admin/assets", StaticFiles(directory=str(admin_dist / "assets")), name="admin_assets")

        async def _admin_spa(_: Request) -> FileResponse:
            return FileResponse(str(admin_dist / "index.html"))

        application.add_route("/admin", _admin_spa, ["GET"])
        application.add_route("/admin/{path:path}", _admin_spa, ["GET"])

    application.include_router(health_router)
    application.include_router(auth_router, prefix=API_PREFIX)
    application.include_router(catalog_router, prefix=API_PREFIX)
    application.include_router(cart_router, prefix=API_PREFIX)
    application.include_router(customer_router, prefix=API_PREFIX)
    application.include_router(orders_router, prefix=API_PREFIX)
    application.include_router(admin_router, prefix=API_PREFIX)
    application.include_router(admin_events_router, prefix=API_PREFIX)
    for route in application.routes:
        if isinstance(route, APIRoute):
            route.response_model_by_alias = False

    if root:
        _configure_openapi_servers(application, root)

    return application


def _configure_openapi_servers(application: FastAPI, root: str) -> None:
    """Point Swagger 'Try it out' at the reverse-proxy subpath."""

    def custom_openapi() -> dict:
        if application.openapi_schema:
            return application.openapi_schema

        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=application.title,
            version=application.version,
            openapi_version=application.openapi_version,
            description=application.description,
            routes=application.routes,
        )
        schema["servers"] = [{"url": root}]
        application.openapi_schema = schema
        return schema

    application.openapi = custom_openapi  # type: ignore[method-assign]


app = create_application()
