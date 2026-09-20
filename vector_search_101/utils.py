"""Utility functions for the Vector Search 101 practical package.

The notebook keeps the teaching narrative visible. This file contains reusable
helpers for loading data, building sparse and dense indexes, searching, and
evaluating retrieval quality.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Callable, Iterable, Literal

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Suppress harmless Apple Accelerate BLAS FPU flag warnings on macOS ARM
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*encountered in matmul")



def load_support_articles(path: str | Path) -> pd.DataFrame:
    """Load the support knowledge-base articles.

    Params:
        path: CSV path containing doc_id, title, category, text, and keywords.

    Returns:
        DataFrame with an added searchable_text column.
    """
    dataframe = pd.read_csv(path)
    required_columns = {"doc_id", "title", "category", "text", "keywords"}
    missing = required_columns.difference(dataframe.columns)
    if missing:
        raise ValueError(f"Missing required article columns: {sorted(missing)}")

    dataframe = dataframe.copy()
    dataframe["searchable_text"] = (
        dataframe["title"].fillna("")
        + ". "
        + dataframe["category"].fillna("")
        + ". "
        + dataframe["text"].fillna("")
        + " Keywords: "
        + dataframe["keywords"].fillna("")
    )
    return dataframe


def load_labelled_queries(path: str | Path) -> pd.DataFrame:
    """Load labelled retrieval-evaluation queries.

    Params:
        path: CSV path containing query, relevant_doc_ids, and why columns.

    Returns:
        DataFrame where relevant_doc_ids is converted to a list of document IDs.
    """
    dataframe = pd.read_csv(path)
    required_columns = {"query", "relevant_doc_ids", "why"}
    missing = required_columns.difference(dataframe.columns)
    if missing:
        raise ValueError(f"Missing required query columns: {sorted(missing)}")

    dataframe = dataframe.copy()
    dataframe["relevant_doc_ids"] = dataframe["relevant_doc_ids"].apply(
        lambda value: [item.strip() for item in str(value).split("|") if item.strip()]
    )
    return dataframe


def build_tfidf_index(texts: Iterable[str]) -> tuple[TfidfVectorizer, object]:
    """Build a simple sparse keyword-search index using TF-IDF.

    Params:
        texts: Iterable of document strings.

    Returns:
        Fitted TfidfVectorizer and sparse document-term matrix.
    """
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
    )
    matrix = vectorizer.fit_transform(list(texts))
    return vectorizer, matrix


def keyword_search(
    query: str,
    articles: pd.DataFrame,
    vectorizer: TfidfVectorizer,
    matrix: object,
    top_k: int = 5,
) -> pd.DataFrame:
    """Search the TF-IDF sparse index.

    Params:
        query: User query.
        articles: Article DataFrame containing doc_id, title, category, and text.
        vectorizer: Fitted TF-IDF vectorizer.
        matrix: Sparse TF-IDF document matrix.
        top_k: Number of results to return.

    Returns:
        DataFrame of ranked results with score.
    """
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix).ravel()
    ranked_indices = np.argsort(scores)[::-1][:top_k]

    results = articles.iloc[ranked_indices][["doc_id", "title", "category", "text"]].copy()
    results.insert(0, "rank", range(1, len(results) + 1))
    results["score"] = scores[ranked_indices].round(4)
    return results


def load_sentence_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """Load a SentenceTransformer embedding model with a friendly error message.

    Params:
        model_name: Hugging Face model name.

    Returns:
        Loaded SentenceTransformer model.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "sentence-transformers is not installed. Run: pip install -r requirements.txt"
        ) from exc

    try:
        return SentenceTransformer(model_name)
    except Exception as exc:
        raise RuntimeError(
            f"Could not load embedding model '{model_name}'. "
            "Check your internet connection for the first download, or verify the model is cached."
        ) from exc


def embed_texts(
    model,
    texts: Iterable[str],
    normalize: bool = True,
    batch_size: int = 32,
) -> np.ndarray:
    """Generate dense embeddings using a SentenceTransformer model.

    Params:
        model: Loaded SentenceTransformer model.
        texts: Iterable of strings to embed.
        normalize: Whether to L2-normalize embeddings.
        batch_size: Batch size for model.encode.

    Returns:
        NumPy float32 matrix of shape [num_texts, embedding_dimensions].
    """
    text_list = [str(text) for text in texts]
    if not text_list:
        raise ValueError("No texts were provided for embedding.")

    embeddings = model.encode(
        text_list,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
        show_progress_bar=False,
    )
    return np.asarray(embeddings, dtype="float32")


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors to unit length.

    Params:
        vectors: NumPy matrix or vector.

    Returns:
        L2-normalized NumPy array with zero-vector protection.
    """
    array = np.asarray(vectors, dtype="float32")
    if array.ndim == 1:
        array = array.reshape(1, -1)
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return array / norms


def build_faiss_index(
    embeddings: np.ndarray,
    metric: Literal["ip", "l2"] = "ip",
):
    """Build a FAISS flat index.

    Params:
        embeddings: Float32 embedding matrix.
        metric: 'ip' for inner product or 'l2' for Euclidean distance.

    Returns:
        FAISS index with embeddings added.
    """
    try:
        import faiss
    except ImportError as exc:
        raise ImportError("faiss-cpu is not installed. Run: pip install -r requirements.txt") from exc

    matrix = np.asarray(embeddings, dtype="float32")
    if matrix.ndim != 2:
        raise ValueError("Embeddings must be a 2D matrix.")

    dimensions = matrix.shape[1]
    if metric == "ip":
        index = faiss.IndexFlatIP(dimensions)
    elif metric == "l2":
        index = faiss.IndexFlatL2(dimensions)
    else:
        raise ValueError("metric must be either 'ip' or 'l2'.")

    index.add(matrix)
    return index


def search_faiss(
    index,
    query_embedding: np.ndarray,
    top_k: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Search a FAISS index.

    Params:
        index: FAISS index.
        query_embedding: Query embedding vector or matrix.
        top_k: Number of results to retrieve.

    Returns:
        Tuple of distances/scores and integer indices from FAISS.
    """
    query_matrix = np.asarray(query_embedding, dtype="float32")
    if query_matrix.ndim == 1:
        query_matrix = query_matrix.reshape(1, -1)
    scores, indices = index.search(query_matrix, top_k)
    return scores, indices


def results_from_indices(
    articles: pd.DataFrame,
    scores: np.ndarray,
    indices: np.ndarray,
    score_name: str = "score",
) -> pd.DataFrame:
    """Convert FAISS result arrays into a readable DataFrame.

    Params:
        articles: Article DataFrame.
        scores: FAISS scores or distances.
        indices: FAISS integer result indices.
        score_name: Name for the score column.

    Returns:
        Ranked DataFrame with document metadata and score.
    """
    flat_scores = scores[0]
    flat_indices = indices[0]
    rows = []
    for rank, (score, article_index) in enumerate(zip(flat_scores, flat_indices), start=1):
        if article_index == -1:
            continue
        article = articles.iloc[int(article_index)]
        rows.append(
            {
                "rank": rank,
                "doc_id": article["doc_id"],
                "title": article["title"],
                "category": article["category"],
                score_name: round(float(score), 4),
                "text": article["text"],
            }
        )
    return pd.DataFrame(rows)


def dense_search(
    query: str,
    model,
    index,
    articles: pd.DataFrame,
    top_k: int = 5,
    normalize: bool = True,
) -> pd.DataFrame:
    """Embed a query and search the dense FAISS index.

    Params:
        query: User query.
        model: Loaded SentenceTransformer model.
        index: FAISS index built over document embeddings.
        articles: Article DataFrame.
        top_k: Number of results to retrieve.
        normalize: Whether to normalize the query embedding.

    Returns:
        Ranked dense-search results.
    """
    query_embedding = embed_texts(model, [query], normalize=normalize)
    scores, indices = search_faiss(index, query_embedding, top_k=top_k)
    return results_from_indices(articles, scores, indices, score_name="dense_score")


def min_max_scale(values: np.ndarray) -> np.ndarray:
    """Scale numeric scores into the [0, 1] range.

    Params:
        values: Numeric NumPy array.

    Returns:
        Min-max scaled NumPy array.
    """
    array = np.asarray(values, dtype=float)
    minimum = float(np.min(array))
    maximum = float(np.max(array))
    if maximum == minimum:
        return np.ones_like(array)
    return (array - minimum) / (maximum - minimum)


def hybrid_search(
    query: str,
    articles: pd.DataFrame,
    vectorizer: TfidfVectorizer,
    tfidf_matrix: object,
    model,
    embeddings: np.ndarray,
    alpha: float = 0.5,
    top_k: int = 5,
) -> pd.DataFrame:
    """Blend sparse keyword scores and dense embedding scores.

    Params:
        query: User query.
        articles: Article DataFrame.
        vectorizer: Fitted TF-IDF vectorizer.
        tfidf_matrix: Sparse TF-IDF document matrix.
        model: Loaded SentenceTransformer model.
        embeddings: Normalized document embedding matrix.
        alpha: Weight for dense scores. 0 = keyword only, 1 = dense only.
        top_k: Number of results to return.

    Returns:
        Ranked DataFrame with keyword, dense, and blended scores.
    """
    if not 0 <= alpha <= 1:
        raise ValueError("alpha must be between 0 and 1.")

    keyword_scores = cosine_similarity(vectorizer.transform([query]), tfidf_matrix).ravel()
    query_embedding = embed_texts(model, [query], normalize=True)
    dense_scores = (query_embedding @ embeddings.T).ravel()

    keyword_scaled = min_max_scale(keyword_scores)
    dense_scaled = min_max_scale(dense_scores)
    blended = alpha * dense_scaled + (1 - alpha) * keyword_scaled

    ranked_indices = np.argsort(blended)[::-1][:top_k]
    results = articles.iloc[ranked_indices][["doc_id", "title", "category", "text"]].copy()
    results.insert(0, "rank", range(1, len(results) + 1))
    results["keyword_score"] = keyword_scores[ranked_indices].round(4)
    results["dense_score"] = dense_scores[ranked_indices].round(4)
    results["hybrid_score"] = blended[ranked_indices].round(4)
    return results


def precision_at_k(retrieved_doc_ids: list[str], relevant_doc_ids: list[str], k: int) -> float:
    """Calculate precision@k for one query.

    Params:
        retrieved_doc_ids: Ranked list of retrieved document IDs.
        relevant_doc_ids: Ground-truth relevant document IDs.
        k: Cutoff rank.

    Returns:
        Precision@k score between 0 and 1.
    """
    if k <= 0:
        raise ValueError("k must be positive.")
    retrieved_at_k = retrieved_doc_ids[:k]
    if not retrieved_at_k:
        return 0.0
    relevant_set = set(relevant_doc_ids)
    hits = sum(1 for doc_id in retrieved_at_k if doc_id in relevant_set)
    return hits / k


def evaluate_retriever(
    labelled_queries: pd.DataFrame,
    search_function: Callable[[str, int], pd.DataFrame],
    k: int = 3,
) -> pd.DataFrame:
    """Evaluate a search function over labelled queries.

    Params:
        labelled_queries: DataFrame with query and relevant_doc_ids columns.
        search_function: Callable that accepts (query, top_k) and returns results with doc_id.
        k: Cutoff rank.

    Returns:
        DataFrame with per-query precision@k and retrieved IDs.
    """
    rows = []
    for _, row in labelled_queries.iterrows():
        query = row["query"]
        relevant_doc_ids = row["relevant_doc_ids"]
        results = search_function(query, k)
        retrieved_doc_ids = results["doc_id"].tolist()
        rows.append(
            {
                "query": query,
                "relevant_doc_ids": ", ".join(relevant_doc_ids),
                "retrieved_doc_ids": ", ".join(retrieved_doc_ids),
                f"precision@{k}": round(precision_at_k(retrieved_doc_ids, relevant_doc_ids, k), 3),
                "why": row.get("why", ""),
            }
        )
    return pd.DataFrame(rows)


def estimate_openai_embedding_cost(
    num_tokens: int,
    price_per_million_tokens: float = 0.02,
) -> float:
    """Estimate OpenAI embedding cost for a given token count.

    Params:
        num_tokens: Estimated input token count.
        price_per_million_tokens: Price per 1M input tokens.

    Returns:
        Estimated cost in USD.
    """
    return (num_tokens / 1_000_000) * price_per_million_tokens


def openai_embed_texts(
    texts: Iterable[str],
    model_name: str = "text-embedding-3-small",
) -> np.ndarray:
    """Generate embeddings with OpenAI if OPENAI_API_KEY is configured.

    Params:
        texts: Iterable of strings to embed.
        model_name: OpenAI embedding model name.

    Returns:
        NumPy float32 matrix of embeddings.

    Raises:
        EnvironmentError: If OPENAI_API_KEY is not configured.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Copy .env.sample to .env and add a key, "
            "or skip the optional OpenAI comparison section."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError("openai is not installed. Run: pip install -r requirements.txt") from exc

    client = OpenAI(api_key=api_key)
    text_list = [str(text) for text in texts]
    response = client.embeddings.create(model=model_name, input=text_list)
    return np.asarray([item.embedding for item in response.data], dtype="float32")
