"""Smoke test for Vector Search 101 helper functions.

Run after installing requirements:
    python smoke_test.py

This does not download the embedding model. It verifies the local data and sparse
retrieval utilities.
"""

from pathlib import Path

from utils import build_tfidf_index, keyword_search, load_labelled_queries, load_support_articles

DATA_DIR = Path("data")
articles = load_support_articles(DATA_DIR / "support_articles.csv")
queries = load_labelled_queries(DATA_DIR / "labelled_queries.csv")
vectorizer, matrix = build_tfidf_index(articles["searchable_text"])
results = keyword_search("E1042 import failed", articles, vectorizer, matrix, top_k=3)

assert len(articles) >= 20
assert len(queries) >= 5
assert not results.empty
assert "KB-009" in results["doc_id"].tolist()

print("Smoke test passed.")
