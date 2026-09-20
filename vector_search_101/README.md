# Vector Search 101 — Practical Teaching Package

This practical teaches how meaning-based search works before connecting it to full Retrieval-Augmented Generation. You will build sparse keyword search, dense embedding search, FAISS indexing, hybrid search, and retrieval evaluation on a small support knowledge base.

## Prerequisites

- Python 3.10 or 3.11 recommended
- Windows, macOS, or Linux
- Internet connection for the first `sentence-transformers/all-MiniLM-L6-v2` model download
- Optional: OpenAI API key for the hosted embedding comparison section

The main practical runs locally and does **not** require a paid API key.

## Setup

### Option A — venv

```bash
cd vector_search_101
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Then install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Option B — conda

```bash
cd vector_search_101
conda create -n vector-search-101 python=3.11 -y
conda activate vector-search-101
pip install -r requirements.txt
```

### Configure `.env`

The OpenAI section is optional. The rest of the notebook works without `.env`.

```bash
cp .env.sample .env
```

Then add your key only if you want to run the OpenAI embedding comparison.

## How to run

```bash
jupyter notebook notebook.ipynb
```

Run the notebook from top to bottom.

Recommended teaching mode:

1. Run the TF-IDF keyword-search baseline first.
2. Ask the class where keyword search should win and where it should fail.
3. Generate MiniLM embeddings and show nearest-neighbor retrieval.
4. Build the FAISS index.
5. Compare keyword, dense, and hybrid search.
6. Evaluate precision@3 using labelled queries.
7. Run the optional OpenAI section only if the trainer wants a hosted-model comparison.

## What each file does

| File | Purpose |
|---|---|
| `notebook.ipynb` | Main teaching notebook with explanations, code, outputs, and exercises |
| `utils.py` | Helper functions for loading data, TF-IDF search, embedding generation, FAISS, hybrid search, and evaluation |
| `data/support_articles.csv` | Small support knowledge base used as the document corpus |
| `data/labelled_queries.csv` | Evaluation queries with known relevant document IDs |
| `.env.sample` | Optional environment-variable template for OpenAI embedding comparison |
| `requirements.txt` | Pinned dependencies |
| `trainer_guide.md` | Detailed live-teaching flow, timing, questions, and troubleshooting |
| `smoke_test.py` | Quick local check for the data and sparse-search utilities |

## Expected output

By the end of the notebook, you should see:

- A TF-IDF keyword-search result table
- MiniLM embedding shape, usually one vector per article with hundreds of dimensions
- Similarity rankings for cosine/dot/L2 comparison
- FAISS top-k search results
- Side-by-side sparse vs dense retrieval differences
- A hybrid-search result table
- Precision@3 evaluation tables for keyword, dense, and hybrid retrieval
- Optional OpenAI embedding shape and cost estimate

## Estimated API cost

Default run: **$0**, because embeddings are generated locally with `sentence-transformers`.

Optional OpenAI comparison: typically far below **$0.01** for this small dataset. The notebook estimates cost before the optional call.

## Troubleshooting

### `ModuleNotFoundError: sentence_transformers`

Run:

```bash
pip install -r requirements.txt
```

Make sure the notebook kernel is using the same environment where you installed dependencies.

### Model download is slow or fails

The first run downloads `sentence-transformers/all-MiniLM-L6-v2`. Check internet access, restart the notebook kernel, and rerun the model-loading cell. Once cached, future runs are faster.

### `ImportError: faiss`

Run:

```bash
pip install faiss-cpu==1.14.2
```

On some older systems, conda can be easier:

```bash
conda install -c pytorch faiss-cpu
```

### OpenAI section says the API key is missing

That section is optional. To run it, copy `.env.sample` to `.env` and set `OPENAI_API_KEY`.

### FAISS results look different from keyword results

That is expected. Keyword search rewards exact term overlap. Dense search rewards semantic similarity. The point of the practical is to observe when each approach helps.

## Further reading

- Sentence Transformers documentation: https://www.sbert.net/
- FAISS documentation: https://faiss.ai/
- FAISS PyPI project: https://pypi.org/project/faiss-cpu/
- OpenAI embeddings documentation: https://platform.openai.com/docs/guides/embeddings
- OpenAI pricing: https://openai.com/api/pricing/
