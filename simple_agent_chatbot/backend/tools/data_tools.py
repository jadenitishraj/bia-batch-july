"""
data_tools.py
-------------
Tools that read our own data (the "corpus").

The corpus is just a JSON file: data/corpus.json
It is a list of documents. Each document has: id, title, topic, text.

You can imagine these documents came from a website, so the search result
looks like a small "web search result".

The search here is very simple on purpose:
we just check if the words of the question appear in the document.
No embeddings, no vector database. Easy to read, easy to explain.
"""

import json
import os

from langchain_core.tools import tool


# Path of data/corpus.json
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FOLDER = os.path.dirname(os.path.dirname(HERE))
CORPUS_FILE = os.path.join(PROJECT_FOLDER, "data", "corpus.json")


def load_corpus():
    """Read the JSON file and return the list of documents."""
    with open(CORPUS_FILE, "r") as f:
        return json.load(f)


@tool
def search_knowledge_base(query: str) -> str:
    """Search the CloudDesk company documents for a topic.
    Use this for any question about pricing, plans, refunds, policies,
    support, security, integrations or product features.
    Give a short query with the important words, for example 'refund policy'."""

    documents = load_corpus()

    # Split the question into lowercase words
    words = query.lower().split()

    results = []

    for doc in documents:
        # Put the whole document into one lowercase string to search inside
        haystack = (doc["title"] + " " + doc["topic"] + " " + doc["text"]).lower()

        # Count how many words of the question appear in this document
        score = 0
        for word in words:
            if word in haystack:
                score = score + 1

        if score > 0:
            results.append({"score": score, "doc": doc})

    if len(results) == 0:
        return "No documents found for: " + query

    # Sort so the document with the most matching words comes first
    results.sort(key=lambda item: item["score"], reverse=True)

    # Keep only the top 3 results
    results = results[:3]

    # Build a readable answer for the model
    output = "Found " + str(len(results)) + " document(s):\n\n"
    for item in results:
        doc = item["doc"]
        output = output + "[" + doc["id"] + "] " + doc["title"] + "\n"
        output = output + doc["text"] + "\n\n"

    return output


@tool
def get_document(doc_id: str) -> str:
    """Get the full text of one document using its id, for example 'doc-3'."""

    documents = load_corpus()

    for doc in documents:
        if doc["id"] == doc_id:
            return doc["title"] + "\n" + doc["text"]

    return "No document found with id: " + doc_id


@tool
def list_topics() -> str:
    """List all the topics available in the company documents."""

    documents = load_corpus()

    topics = []
    for doc in documents:
        if doc["topic"] not in topics:
            topics.append(doc["topic"])

    return "Available topics: " + ", ".join(topics)
