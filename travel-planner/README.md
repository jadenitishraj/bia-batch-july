# Travel Planner

A Vite chat interface and FastAPI backend for `travel_planner_langgraph_(1).ipynb`.
The notebook's prompts, sample data, tools and LangGraph workflow are preserved:
manager → selected specialists in parallel → synthesis → critic → revision.
The UI renders the exact `final_plan` string produced by the graph, with collapsible intermediate agent reports.

## Local setup

Requires Python 3.11+ and Node.js 20+.

From this folder:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
cp .env.example .env  # only if .env does not already exist
```

Set `OPENAI_API_KEY` in `.env`. It stays on the backend and is ignored by Git.

Start the backend:

```sh
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8002
```

In another terminal:

```sh
cd frontend
npm install
npm run dev
```

Open http://localhost:5174. Vite proxies `/api` to port 8002.
`npm run build` validates and builds the frontend.

## Structure

- `backend/app/data.py`: notebook's sample travel data
- `backend/app/tools.py`: seven tools
- `backend/app/registry.py`: tools allowed for each specialist
- `backend/app/agents.py`: agent prompts and model
- `backend/app/state.py`: shared graph state
- `backend/app/nodes.py`: manager, specialists, synthesis, critic, revision
- `backend/app/graph.py`: routing and compiled LangGraph
- `backend/app/main.py`: health endpoint and streamed planning endpoint
- `frontend/src/main.js`: chat, live progress and Markdown result rendering
- `frontend/src/style.css`: responsive interface

## Notes

AI requests use the configured OpenAI account and incur usage charges. The UI makes one independent trip request at a time; it does not retain chat context. New trip clears the current view. The sample data supports Singapore flights from Mumbai, Delhi and Bangalore; it is not live booking inventory. The notebook's unused duplicate `retriver` tool was omitted. The broken notebook `result['fina']` return is avoided by returning the graph's actual `final_plan`.

## Verification

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

Offline tests cover flight filters, selective and parallel worker routing, exact final-answer streaming, input validation and safe error messages. A live Singapore demo was also verified through the browser. The original notebook prompts are preserved, so model-generated costs, dates and schedules can still be inconsistent; this is a teaching demo, not a booking engine.


## Document uploads and answers

The **Upload documents** tab accepts PDF, TXT and Markdown files (up to 20 MB).
The copied `backend/rag_v2/` folder is used without source edits. Its existing knowledge base was copied too, so it starts with the original stored documents. The copy is independent of `/Users/nitish/Documents/agents`.

- `backend/app/documents.py` handles upload validation, file saving, ingestion and retrieval adapters.
- `backend/app/document_answers.py` identifies document requests and writes answers grounded in retrieved excerpts.
- Ordinary trip requests keep the original notebook workflow.
- Document-only questions search the RAG knowledge base without generating an unrelated trip.
- Mixed requests retain the trip answer and append a **From your documents** section.
- The original RAG pipeline returns text directly; this adapter consumes that text without using the incompatible legacy `/rag/search` response mapping.
- The pipeline's existing behavior is preserved: graph extraction is best-effort, retrieval searches vector + BM25, uploads append rather than replace, and repeated uploads can duplicate chunks.

`backend/rag_v2-copy-manifest.json` records hashes from the exact initial copy, including its initial storage files. The test suite verifies that all copied Python source files remain unchanged. Runtime storage naturally changes as files are indexed.

Live verification indexed the clearly labelled `backend/tests/fixtures/travel-planner-demo.md` sample and confirmed its vector entry, graph relationships, BM25 chunk and correctly sourced answer through the UI. This sample appears in the library alongside the copied documents. After explicit user approval for sending retrieved excerpts to OpenAI, a live mixed request also passed: the original flight answer was retained exactly and the sourced document answer was appended, including the verified 9:15 AM meeting time and LAVENDER-915 reference code.

## Run Ragas evaluation

From the `travel-planner` folder:

```sh
.venv/bin/python scripts/evaluate_ragas.py
```

This runs two live document questions and scores faithfulness, answer relevance and context precision using the existing, unchanged `rag_v2.ragas_evaluation.run_ragas_evaluation` function. It sends retrieved excerpts and generated answers to OpenAI and consumes API usage. Results are written to `reports/ragas-evaluation.json`.

The separate runner adapts the retriever's string output. The original evaluation CLI expects a dictionary and would fail at `search_result.get(...)`; it remains unchanged. The copied golden-set script also assumes a dictionary, and its reference answers are labelled as placeholders, so this runner reports reference-free scores rather than claiming a validated golden-set benchmark. No dummy-context fallback is used.

## Classroom upload walkthrough

The Upload documents tab streams an **Inside your upload** walkthrough: parsing/classification, selected parser and chunking settings, expandable actual chunks (full text, IDs and metadata), saving, persisted storage verification and completion. Chroma and BM25 counts verify this upload's chunk IDs. The graph count is labelled as the whole knowledge base and does not claim graph extraction succeeded for a particular file.

This is implemented in `backend/app/upload_trace.py` by calling the original `configure_settings`, `parse_file`, `chunk_document` and `index_chunks` functions in the same order; no `rag_v2` source edits are needed. The standard JSON upload endpoint remains available, and `?trace=true` enables streamed progress. The walkthrough remains visible while switching tabs, until another upload or a page refresh.

## Fresh clone

Credentials, uploaded files, local database contents and generated evaluation reports are excluded from Git. After cloning, configure `.env` and upload your own documents in the Upload documents tab. The local development copy includes previously indexed documents, but a fresh clone starts with an empty knowledge base. Upload `backend/tests/fixtures/travel-planner-demo.md` to try its example prompt; the Veridia prompt and evaluation also require the corresponding document to be uploaded.
