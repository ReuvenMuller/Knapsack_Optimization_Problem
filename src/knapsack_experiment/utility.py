from __future__ import annotations

import math
import re
from collections import Counter


_WORD_PATTERN = re.compile(r"[A-Za-z0-9]+", re.UNICODE)


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    v_min = min(values)
    v_max = max(values)
    if abs(v_max - v_min) < 1e-12:
        return [1.0 for _ in values]
    return [(v - v_min) / (v_max - v_min) for v in values]


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _WORD_PATTERN.findall(text)]


def lexical_tfidf_scores(query: str, chunks: list[str]) -> list[float]:
    """
    Lightweight TF-IDF cosine proxy without external dependencies.
    """
    if not chunks:
        return []

    query_tokens = _tokenize(query)
    query_tf = Counter(query_tokens)

    chunk_tokens = [_tokenize(chunk) for chunk in chunks]
    doc_freq: Counter[str] = Counter()
    for tokens in chunk_tokens:
        doc_freq.update(set(tokens))

    n_docs = len(chunks)
    scores: list[float] = []
    for tokens in chunk_tokens:
        tf = Counter(tokens)
        score = 0.0
        for term, q_count in query_tf.items():
            if term not in tf:
                continue
            idf = math.log((n_docs + 1) / (doc_freq[term] + 1)) + 1.0
            score += (q_count * idf) * (tf[term] * idf)
        scores.append(score)

    return _normalize(scores)


def semantic_embedding_scores(
    query: str,
    chunks: list[str],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> list[float]:
    """
    Sentence-transformer embedding cosine scores.

    Requires optional dependency:
      pip install sentence-transformers
    """
    if not chunks:
        return []

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'sentence-transformers'. Install with: "
            "pip install sentence-transformers"
        ) from exc

    model = SentenceTransformer(model_name)
    query_vec = model.encode([query], normalize_embeddings=True)[0]
    chunk_vecs = model.encode(chunks, normalize_embeddings=True)

    scores = []
    for vec in chunk_vecs:
        # Dot product == cosine because vectors are normalized.
        score = float(sum(a * b for a, b in zip(query_vec, vec)))
        scores.append(score)
    return _normalize(scores)


def compute_utilities(
    query: str,
    chunks: list[str],
    method: str = "lexical",
    semantic_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    alpha: float = 0.7,
    beta: float = 0.3,
) -> list[float]:
    """
    Utility methods:
    - lexical: TF-IDF style lexical relevance
    - semantic: embedding similarity
    - hybrid: alpha * semantic + beta * lexical
    """
    method = method.lower()
    if method == "lexical":
        return lexical_tfidf_scores(query, chunks)
    if method == "semantic":
        return semantic_embedding_scores(query, chunks, model_name=semantic_model_name)
    if method == "hybrid":
        lexical = lexical_tfidf_scores(query, chunks)
        try:
            semantic = semantic_embedding_scores(query, chunks, model_name=semantic_model_name)
        except RuntimeError:
            # Graceful fallback so experiments still run without heavy dependencies.
            return lexical
        return [alpha * s + beta * l for s, l in zip(semantic, lexical)]

    raise ValueError(f"Unknown utility method '{method}'")
