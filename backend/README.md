# TrustLens Backend

Clean Architecture FastAPI backend for TrustLens.

## What it provides

- `POST /api/analyze` for agreement analysis
- `POST /api/question` for agreement Q&A
- `GET /health` for service checks

## Local Run

1. Create a Python virtual environment.
2. Install dependencies from `requirements.txt`.
3. Configure environment variables in `.env`.
4. Start the API:

```bash
uvicorn main:app --reload
```

## Environment

- `GEMINI_API_KEY`
- `MONGODB_URI`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `PINECONE_NAMESPACE`
- `EMBEDDING_MODEL_NAME`

## Deployment Notes

- Render: deploy as a FastAPI web service with `uvicorn main:app`.
- MongoDB Atlas: set `MONGODB_URI` to your Atlas connection string.
- Pinecone: set the Pinecone API key and index name.
- Chrome extension frontend will call these APIs after the backend is deployed.
