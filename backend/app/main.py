from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from .core.config import settings
from .core.database import init_db
from .core.logging import logger
from .api.auth import router as auth_router
from .api.task import router as task_router
from .api.resource import router as resource_router
from .api.debug import router as debug_router
from .api.log import router as log_router
from .api.websocket import router as websocket_router
from .api.result import router as result_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Crawler Web Platform...")
    init_db()
    yield
    logger.info("Shutting down Crawler Web Platform...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="网络爬虫Web平台后端API服务",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "请求参数验证失败",
            "details": exc.errors(),
        },
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "数据验证失败",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "details": str(exc) if settings.DEBUG else None,
        },
    )


api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


api_router.include_router(auth_router)
api_router.include_router(task_router)
api_router.include_router(resource_router)
api_router.include_router(debug_router)
api_router.include_router(log_router)
api_router.include_router(result_router)

app.include_router(websocket_router)
app.include_router(api_router, prefix="/api")
