"""
Utility methods:
- lexical: TF/IDF
- semantic: embedding similarity
- hybrid: pct_semantic * semantic + pct_lexical * lexical
"""

from __future__ import annotations

import re
import numpy as np
from collections import Counter

_split_tokens = re.compile(r"[A-Za-z0-9]+", re.UNICODE)
_semantic_model_cache = {}

def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    v_min = min(values)
    v_max = max(values)
    if abs(v_max - v_min) < 1e-10:
        return [1.0 for _ in values]
    return [(v - v_min) / (v_max - v_min) for v in values]


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _split_tokens.findall(text)]

# lexical - tf_idf
def lexical(query: str, chunks: list[str]) -> list[float]:
    if not chunks:
        return []

    query_tokens = _tokenize(query)
    query_tf = Counter(query_tokens)

    chunk_tokens = [_tokenize(chunk) for chunk in chunks]
    doc_freq: Counter[str] = Counter()
    for tokens in chunk_tokens:
        doc_freq.update(set(tokens))

    N = len(chunks)
    scores: list[float] = []
    for tokens in chunk_tokens:
        tf = Counter(tokens)
        score = 0.0
        for term, q_count in query_tf.items():
            if term not in tf:
                continue
            idf = np.log((N + 1) / (doc_freq[term] + 1)) + 1.0
            score += (q_count * idf) * (tf[term] * idf)
        scores.append(score)

    return _normalize(scores)


def semantic(
    query: str,
    chunks: list[str],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> list[float]:

    if not chunks:
        return []

    if model_name not in _semantic_model_cache:
        from sentence_transformers import SentenceTransformer

        _semantic_model_cache[model_name] = SentenceTransformer(model_name)

    model = _semantic_model_cache[model_name]
    query_vec = model.encode([query], normalize_embeddings=True)[0]
    chunk_vecs = model.encode(chunks, normalize_embeddings=True)

    scores = []
    for vec in chunk_vecs:
        score = np.dot(query_vec,vec)
        scores.append(score)
    return _normalize(scores)

def compute_utilities(
    query: str,
    chunks: list[str],
    method: str = "lexical",
    semantic_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    pct_semantic: float = 0.75,
    pct_lexical: float = 0.25,
) -> list[float]:

    method = method.lower()
    if method == "lexical":
        return lexical(query, chunks)
    if method == "semantic":
        return semantic(query, chunks, model_name=semantic_model_name)
    if method == "hybrid":
        lexical_scores = lexical(query, chunks)
        semantic_scores = semantic(query, chunks, model_name=semantic_model_name)
        return [
            pct_semantic * semantic_score + pct_lexical * lexical_score
            for semantic_score, lexical_score in zip(semantic_scores, lexical_scores)
        ]

    raise ValueError(f"Unknown utility method '{method}'")
