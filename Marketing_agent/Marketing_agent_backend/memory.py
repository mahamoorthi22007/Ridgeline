import os
import numpy as np
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding

# கோப்பகங்கள் மற்றும் கலெக்ஷன் பெயர்
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qdrant_data")
COLLECTION = "campaign_memory"
EMBED_MODEL = "BAAI/bge-small-en"

_client: QdrantClient | None = None
_embedding_model: TextEmbedding | None = None

def get_client() -> QdrantClient:
    """Qdrant client-ஐ உருவாக்குகிறது."""
    global _client
    if _client is not None:
        return _client
    _client = QdrantClient(path=DATA_DIR)
    return _client

def get_embedding_model() -> TextEmbedding:
    """FastEmbed மாடலை லோட் செய்கிறது."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name=EMBED_MODEL)
    return _embedding_model

def store_content(campaign_name: str, content_type: str, text: str, extra: dict | None = None) -> None:
    """கண்டென்ட்டை மெமரியில் சேமிக்கிறது."""
    client = get_client()
    model = get_embedding_model()
    
    # கலெக்ஷன் இல்லையென்றால் உருவாக்குதல்
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
        )

    payload = {"campaign_name": campaign_name, "content_type": content_type, "text": text}
    if extra:
        payload.update(extra)

    # வெக்டார் உருவாக்கம்
    vector_data = list(model.embed([text]))[0].tolist()

    point_id = abs(hash(f"{campaign_name}:{content_type}:{text[:50]}")) % (2**63)
    
    client.upsert(
        collection_name=COLLECTION,
        points=[
            models.PointStruct(
                id=point_id,
                vector=vector_data,
                payload=payload,
            )
        ],
    )

def search_similar(query_text: str, content_type: str | None = None, limit: int = 3) -> list[dict]:
    """மெமரியிலிருந்து தொடர்புடைய தகவலைத் தேடுகிறது."""
    client = get_client()
    model = get_embedding_model()
    
    query_vector = list(model.embed([query_text]))[0].tolist()

    query_filter = None
    if content_type:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="content_type", match=models.MatchValue(value=content_type))]
        )

    try:
        response = client.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
        )
    except Exception:
        return []

    return [
        {
            "campaign_name": point.payload.get("campaign_name"),
            "content_type": point.payload.get("content_type"),
            "text": point.payload.get("text"),
            "score": point.score,
        }
        for point in response
    ]