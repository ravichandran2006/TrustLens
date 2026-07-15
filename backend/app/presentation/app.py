from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.infrastructure.dependencies import get_mongo_client, get_retriever, get_vector_store
from app.presentation.routes.analyze_route import router as analyze_router
from app.presentation.routes.health_route import router as health_router
from app.presentation.routes.question_route import router as question_router

logger = logging.getLogger(__name__)


def _validate_database_connections() -> None:
    settings = get_settings()
    mongo = get_mongo_client()
    vector_store = get_vector_store()
    retriever = get_retriever()

    if settings.mongodb_uri and mongo._db is None:
        logger.warning("MONGODB_URI is set but MongoDB client is unavailable. Data will be stored in memory only.")
    elif mongo._db is not None:
        try:
            mongo._client.admin.command("ping")
            logger.info("MongoDB connected to database '%s'.", settings.mongodb_database)
        except Exception as exc:
            logger.error("MongoDB connection failed: %s", exc)

    if settings.pinecone_api_key and vector_store._index is None:
        logger.warning("PINECONE_API_KEY is set but Pinecone client is unavailable. Vectors will be stored in memory only.")
    elif vector_store._index is not None:
        logger.info("Pinecone connected to index '%s' namespace '%s'.", settings.pinecone_index_name, settings.pinecone_namespace)

    if settings.pinecone_api_key and type(retriever).__name__ == "InMemoryAgreementRetriever":
        logger.warning("Pinecone is configured but the in-memory retriever is active. Install the pinecone package.")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        _validate_database_connections()

    app.include_router(health_router)
    app.include_router(analyze_router)
    app.include_router(question_router)
    return app
