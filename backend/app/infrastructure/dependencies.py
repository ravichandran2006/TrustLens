from __future__ import annotations

from functools import lru_cache

from app.application.use_cases.analyze_agreement import AnalyzeAgreementUseCase
from app.application.use_cases.answer_question import AnswerQuestionUseCase
from app.config.settings import get_settings
from app.infrastructure.embeddings.embedding_service import EmbeddingService
from app.infrastructure.llm.gemini_client import GeminiClient
from app.infrastructure.mongodb.mongodb_client import MongoDBClient
from app.infrastructure.rag.chunker import AgreementChunker
from app.infrastructure.rag.context_builder import ContextBuilder
from app.infrastructure.rag.retriever import InMemoryAgreementRetriever, PineconeAgreementRetriever
from app.infrastructure.vector_db.pinecone_client import PineconeVectorStore


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoDBClient:
    settings = get_settings()
    return MongoDBClient(uri=settings.mongodb_uri, database_name=settings.mongodb_database)


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    return EmbeddingService(model_name=settings.embedding_model_name)


@lru_cache(maxsize=1)
def get_vector_store() -> PineconeVectorStore:
    settings = get_settings()
    return PineconeVectorStore(api_key=settings.pinecone_api_key, index_name=settings.pinecone_index_name, namespace=settings.pinecone_namespace)


@lru_cache(maxsize=1)
def get_retriever() -> PineconeAgreementRetriever | InMemoryAgreementRetriever:
    settings = get_settings()
    embedding_service = get_embedding_service()
    if settings.pinecone_api_key:
        return PineconeAgreementRetriever(
            embedding_service=embedding_service,
            vector_store=get_vector_store(),
        )
    # Use in-memory retriever for testing
    return InMemoryAgreementRetriever(embedding_service=embedding_service)


@lru_cache(maxsize=1)
def get_gemini_client() -> GeminiClient:
    settings = get_settings()
    return GeminiClient(api_key=settings.gemini_api_key, model_name=settings.gemini_model)


@lru_cache(maxsize=1)
def get_analyze_use_case() -> AnalyzeAgreementUseCase:
    mongo_client = get_mongo_client()
    return AnalyzeAgreementUseCase(
        agreement_repository=mongo_client,
        chunker=AgreementChunker(),
        retriever=get_retriever(),
        context_builder=ContextBuilder(),
    )


@lru_cache(maxsize=1)
def get_question_use_case() -> AnswerQuestionUseCase:
    retriever = get_retriever()
    gemini_client = get_gemini_client() if get_settings().gemini_api_key else None
    return AnswerQuestionUseCase(retriever=retriever, context_builder=ContextBuilder(), llm_client=gemini_client)
