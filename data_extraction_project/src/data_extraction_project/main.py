# import from app.py and run it
# fastapi code

from contextlib import asynccontextmanager

from fastapi import FastAPI
from data_extraction_project.api.middleware.cors import add_cors_middleware
from data_extraction_project.api.v1.exception_handlers import register_exception_handlers

from data_extraction_project.api.v1.routes.gemini_routes import router as gemini_router
from data_extraction_project.api.v1.routes.groq_routes import router as groq_router
from data_extraction_project.api.v1.routes.pdf_markdown_routes import router as pdf_markdown_router
from data_extraction_project.api.v1.routes.paddleocr_routes import router as paddleocr_router
from data_extraction_project.api.v1.routes.tesseract_routes import router as tesseract_router
from data_extraction_project.api.v1.deps import get_ocr_service

import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: open DB pools, connect clients, etc.
    get_ocr_service()
    yield
    # Shutdown: close connections, flush buffers, etc.


def create_app() -> FastAPI:
    app = FastAPI(
        title="Data extraction",
        version="0.1.0",
        lifespan=lifespan,
    )

    add_cors_middleware(app)

    register_exception_handlers(app)

    app.include_router(paddleocr_router, prefix="/api/v1")

    app.include_router(tesseract_router, prefix="/api/v1")

    app.include_router(gemini_router, prefix="/api/v1")

    app.include_router(groq_router, prefix="/api/v1")

    app.include_router(pdf_markdown_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Include routers here, e.g.:
    # from project_name.api.v1.routes import router as v1_router
    # app.include_router(v1_router, prefix="/api/v1")

    return app

app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "data_extraction_project.main:app",
        host="localhost",
        port=8000,
        reload=True,
    )