# Trainer Guide — Vector Search 101 Practical

## Demo goal

Build retrieval intuition before full RAG. The class should leave knowing:

- why keyword search is not enough,
- what embeddings make possible,
- how similarity metrics change retrieval,
- how FAISS searches dense vectors,
- why dense retrieval still fails,
- how to measure retrieval quality before connecting an LLM.

Do **not** turn this into a full RAG build. That belongs in the Text-RAG Pipeline session.

## Recommended teaching flow

### 0–10 min — Frame the practical

Show the support knowledge base and ask:

> Which article should match “How can I get my money back after cancelling?”

Let learners notice that the words “money back” may not exactly match “refund”.

### 10–25 min — Keyword baseline

Run the TF-IDF section.

Talking points:

- TF-IDF is sparse retrieval: most dimensions are zero.
- It is strong for exact terms like `E1042`, `GST`, and `SAML`.
- It can miss paraphrases.

### 25–45 min — Embeddings

Run the MiniLM loading and embedding cells.

Talking points:

- Every article becomes one vector.
- The dimensions are learned features, not manually named spreadsheet columns.
- The vector only has meaning under the model that produced it.

Pause after showing embedding shape. Ask learners what the number of rows and columns represent.

### 45–60 min — Similarity metrics

Run the metric comparison section.

Talking points:

- Cosine similarity cares about direction.
- Dot product behaves like cosine when vectors are normalized.
- L2 is distance: lower is better.
- Ranking is what matters in retrieval, not the raw score alone.

### 60–85 min — FAISS

Run the FAISS index section.

Talking points:

- FAISS stores vectors and returns nearest vector IDs.
- FAISS does not know your article titles or categories.
- You must map integer result IDs back to source documents.
- This is an index, not a full vector database.

### 85–105 min — Sparse vs dense vs hybrid

Run the comparison cells.

Suggested queries:

- `E1042 import failed`
- `How do I get my money back?`
- `I changed phones and cannot approve login`
- `wrong GST number on invoice`

Talking points:

- Exact identifiers often favor sparse search.
- Paraphrases often favor dense search.
- Hybrid retrieval is common in production because both failure modes matter.

### 105–125 min — Evaluation

Run precision@3 for keyword, dense, and hybrid retrieval.

Talking points:

- Retrieval must be evaluated before LLM generation.
- A good answer cannot be generated if the right context was never retrieved.
- Precision@k is simple but not enough for all real systems.
- Later sessions can add recall@k, MRR, RAGAS, reranking, and faithfulness checks.

### 125–140 min — Optional OpenAI comparison

Run only if the OpenAI key is configured and timing allows.

Talking points:

- Hosted embeddings simplify deployment consistency.
- Local embeddings reduce cost and keep data local.
- Always compare on your own data, not just model leaderboard claims.

### 140–160 min — Exercises and wrap

Assign one or two exercises live:

1. Add three new support articles and test where keyword vs dense search wins.
2. Change the hybrid `alpha` and observe ranking changes.
3. Add a query whose correct answer is not in the corpus and discuss what retrieval should do.

## Likely questions and ideal answers

### “Are embeddings like database IDs?”

No. IDs are arbitrary identifiers. Embeddings are learned numeric representations where distance carries meaning.

### “Can we understand what each embedding dimension means?”

Usually not directly. Some dimensions may correlate with features, but embedding spaces are distributed representations.

### “Why not always use vector search?”

Because exact terms matter. Error codes, legal clause numbers, SKU IDs, invoice numbers, and names often require lexical precision.

### “Is FAISS a vector database?”

Not by itself. FAISS is a similarity-search library/index. A vector database adds persistence, metadata filtering, access control, APIs, scaling, and operational tooling.

### “Does a higher similarity score always mean the answer is correct?”

No. It only means the vector is close under the embedding model. The retrieved document can still be irrelevant, stale, or incomplete.

### “What does top-k mean?”

The number of nearest results returned. Higher k increases the chance of including relevant context, but also increases noise.

### “Why evaluate retrieval before using an LLM?”

Because an LLM can only answer from the context it receives. Poor retrieval leads to hallucination or vague answers.

### “Should we use OpenAI embeddings or local embeddings?”

Use local embeddings for learning, prototyping, privacy-sensitive experiments, and zero-cost demos. Use hosted embeddings when you need managed reliability, consistent deployment, and strong general-purpose quality.

## Common errors and fixes

### FAISS import fails

Install `faiss-cpu` in the same environment as the notebook kernel.

### Notebook kernel uses wrong environment

In Jupyter, choose the kernel associated with the virtual environment or conda environment created for this package.

### Model loading fails

The first run needs internet to download MiniLM. Retry with stable internet. After download, the model is cached.

### Scores confuse learners

Remind them:

- Cosine / inner product: higher is usually better.
- L2 distance: lower is better.
- Scores are comparable within a retrieval setup, not across every model or metric.

### Results are not perfect

That is a feature of the lesson. Use imperfect results to teach failure analysis.

## What to skip if running short

Essential:

- Keyword baseline
- MiniLM embeddings
- FAISS search
- Sparse vs dense comparison
- Precision@3 evaluation

Skippable:

- Optional OpenAI embedding section
- Hybrid alpha tuning
- FAISS save/load section
- All extension exercises

## Extension ideas

- Add metadata filters by category.
- Try a stronger sentence-transformers model and compare precision@3.
- Add a reranker as a preview of advanced retrieval.
- Create a “no answer found” threshold experiment.
- Persist FAISS index and metadata to disk.
