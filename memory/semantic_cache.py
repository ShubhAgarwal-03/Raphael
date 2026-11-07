import time
import json
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

CACHE_FILE = "memory/semantic_cache.json"
CACHE_TTL = 600  # seconds (10 min)
SIM_THRESHOLD = 0.85

# model = SentenceTransformer("all-MiniLM-L6-v2")

_model = None

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def _save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def add_to_cache(query, response):
    cache = _load_cache()

    # embedding = model.encode(query).tolist()
    embedding = get_model().encode(query).tolist()
    
    entry = {
        "query": query,
        "embedding": embedding,
        "response": response,
        "timestamp": time.time()
    }

    cache.append(entry)
    _save_cache(cache)


def lookup_cache(query):
    cache = _load_cache()
    if not cache:
        return None

    query_emb = get_model().encode(query)

    best_score = 0
    best_resp = None
    now = time.time()

    for item in cache:
        # TTL check
        if now - item["timestamp"] > CACHE_TTL:
            continue

        sim = cosine_similarity(
            [query_emb],
            [item["embedding"]]
        )[0][0]

        if sim > best_score:
            best_score = sim
            best_resp = item["response"]

    if best_score >= SIM_THRESHOLD:
        return best_resp

    return None
