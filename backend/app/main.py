import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.api.v1.health import router as health_router
from app.config import get_settings
from app.schemas.common import ErrorDetail, ErrorResponse
from app.utils.exceptions import AppException
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode...")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


def create_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "CivicAI Backend Orchestration Layer for AI-powered civic empowerment and legal assistance. "
            "Manages conversations, guided civic form sessions, legal complaint drafting workflows, "
            "and proxies to the RAG/AI microservice."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. CORS Middleware
    origins = settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Request Timing & Logging Middleware
    @app.middleware("http")
    async def log_and_time_requests(request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method

        logger.info(f"--> {method} {path}")
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
            logger.info(f"<-- {method} {path} | Status: {response.status_code} | Time: {process_time:.2f}ms")
            return response
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"<-- {method} {path} | FAILED | Time: {process_time:.2f}ms | Error: {exc}", exc_info=True)
            raise exc

    # 3. Custom Domain Exception Handler
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=exc.error_code,
                    message=exc.message,
                    details=exc.details,
                ),
            ).model_dump(mode="json"),
        )

    # 4. Request Validation Exception Handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code="VALIDATION_ERROR",
                    message="Request payload validation failed",
                    details=exc.errors(),
                ),
            ).model_dump(mode="json"),
        )

    # 5. Starlette / FastAPI HTTP Exception Handler
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code="HTTP_ERROR",
                    message=str(exc.detail),
                ),
            ).model_dump(mode="json"),
        )

    # 6. Global Catch-all Unhandled Exception Handler
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.critical(f"Unhandled internal server error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message="An unexpected internal server error occurred",
                ),
            ).model_dump(mode="json"),
        )

    # Include Routes
    app.include_router(health_router)
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
