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

Choose the provider in `.env`, which stays on the backend and is ignored by Git.
For Gemini, set `CHAT_PROVIDER=gemini`, privately add your existing `GOOGLE_API_KEY`
(or `GEMINI_API_KEY`), and optionally set `GEMINI_MODEL=gemini-3.1-flash-lite`.
For the original OpenAI setup, use `CHAT_PROVIDER=openai` and `OPENAI_API_KEY`.
Restart the backend after changing these settings. All five travel agents, the
request classifier and document answer writer share this provider configuration.
The manager routing, parallel specialists, synthesis, critic and revision stay the same.
The copied RAG indexing, embedding, reranking and image parsing pipeline still uses
its original OpenAI integrations; changing those requires separate work and reindexing.

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

## Classroom observability

**LangSmith shows the workflow.** One `@traceable` wraps the fixed demo request;
LangGraph automatically adds the manager, specialist, model and tool spans.
The graph itself is unchanged. Ordinary planner requests stay untraced.

Set `TRAVEL_PLANNER_LANGSMITH_API_KEY` privately in the ignored `.env`, restart
the backend, and run `.venv/bin/python scripts/trace_demo.py`. The script uses
sample flight data and never reads uploaded documents. Inputs, outputs and
application metadata are hidden for every span. Failed runs stay marked as failed.
Open the `bia-july-travel-planner-demo` project in LangSmith to inspect the tree.

**Helicone is the model gateway.** The path is app → Helicone → model provider.
Set `CHAT_PROVIDER=helicone`, `HELICONE_API_KEY` and `HELICONE_MODEL` in `.env`,
then restart. For Gemini use `gemini-3.1-flash-lite/google-ai-studio`; an existing
OpenAI provider can use `gpt-4o-mini/openai`. `CHAT_PROVIDER=gemini` restores direct
Gemini. There is no silent application fallback.

The gateway demo uses Gemini 3.1 Flash Lite. For this unregistered model, the
hosted BYOK gateway returns native Gemini JSON. A small adapter delegates parsing
to the pinned Gemini integration, preserving text, tool calls and token usage;
standard OpenAI responses keep the normal parser. This uses an internal parser
from the pinned dependency, so rerun the adapter tests before upgrading it.
Google's older 2.5 Flash Lite is unavailable to this account despite its quota row.
The current project is Free tier; 3.1 Flash Lite displays limits of 15 requests/minute,
250,000 tokens/minute and 500 requests/day. Check AI Studio before classroom use.

The app sends only the Helicone key to the gateway. The upstream provider must
already be configured in Helicone or have credits available. Adding a provider key
to Helicone is a separate credential-sharing decision. Nothing changes billing or
organization limits. Request and response body logging is omitted.

Helicone labels each model call with `App` and `Agent`, so the dashboard can show
status, latency and tokens by agent. This model currently shows **Cost Unsupported**
in Helicone; use Google AI Studio for project usage rather than treating that as $0.
Local tool execution stays in Python;
look at LangSmith for the tool spans. The manager also handles synthesis/revision.
The request classifier and document answer writer use the selected provider too;
the separate RAG indexing and embedding pipeline retains its original integrations.

Use Helicone's Rate Limits page to inspect actual throttling. When an active policy
applies, responses may include `Helicone-RateLimit-Limit`, `Helicone-RateLimit-Policy`
and `Helicone-RateLimit-Remaining`. A 429 can also mean insufficient credits, so
check its cause. No load test or rate-limit rule is needed for this classroom demo.

**Grafana shows app events and process metrics.** The standard Python logger writes
Pino-style JSON to the console and Loki. Events include node/tool start and finish,
routing decisions, duration and error type; they exclude prompts, tool arguments,
results and credentials. A background queue keeps log delivery outside the response stream.

Configure `GRAFANA_CLOUD_TOKEN`, `GRAFANA_LOKI_URL`, `GRAFANA_LOKI_USER`,
`GRAFANA_PROMETHEUS_URL` and `GRAFANA_PROMETHEUS_USER` privately, then restart.
The OpenTelemetry exporter sends metrics directly every ten seconds; no local
Prometheus service is needed. In Grafana Explore, select Loki and query
`{app="travel-planner"} | json`. Select Prometheus for
`travel_planner_process_cpu_seconds_s`,
`travel_planner_process_peak_resident_memory_bytes_By` and
`travel_planner_http_requests`. CPU is cumulative app-process CPU time and memory
is the app process's peak resident memory, not current memory or whole-computer usage.
The HTTP counter increments when each response, including streaming, completes.

References: [LangSmith tracing](https://docs.langchain.com/langsmith/trace-without-env-vars),
[Helicone gateway](https://docs.helicone.ai/gateway/integrations/langchain),
[Helicone rate limits](https://docs.helicone.ai/features/advanced-usage/custom-rate-limits).

## Project files

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

AI requests use the configured provider and may incur usage charges. The UI makes one independent trip request at a time; it does not retain chat context. New trip clears the current view. The sample data supports Singapore flights from Mumbai, Delhi and Bangalore; it is not live booking inventory. The notebook's unused duplicate `retriver` tool was omitted. The broken notebook `result['fina']` return is avoided by returning the graph's actual `final_plan`.

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
- The pipeline's existing behavior is preserved: graph extraction is best-effort, retrieval searches vector + BM25 + graph, uploads append rather than replace, and repeated uploads can duplicate chunks.

`backend/rag_v2-copy-manifest.json` records hashes from the exact initial copy, including its initial storage files. The test suite verifies that copied Python source files remain unchanged except the explicitly updated parser, chunker, evaluator and retriever. Runtime storage naturally changes as files are indexed.

Live verification indexed the clearly labelled `backend/tests/fixtures/travel-planner-demo.md` sample and confirmed its vector entry, graph relationships, BM25 chunk and correctly sourced answer through the UI. This sample appears in the library alongside the copied documents. After explicit user approval for sending retrieved excerpts to OpenAI, a live mixed request also passed: the original flight answer was retained exactly and the sourced document answer was appended, including the verified 9:15 AM meeting time and LAVENDER-915 reference code.

## Run Ragas evaluation

From the `travel-planner` folder:

```sh
.venv/bin/python scripts/evaluate_ragas.py
```

This runs two live document questions and scores faithfulness, answer relevance, context precision, context recall and factual correctness using the simplified `rag_v2.ragas_evaluation.run_ragas_evaluation` function. It sends retrieved excerpts and generated answers to OpenAI and consumes API usage. Results are written to `reports/ragas-evaluation.json`.

The separate runner adapts the retriever's string output. The evaluator uses the standard Ragas `evaluate()` call with five metrics. Recall and factual correctness use expected answers checked against the stored source documents. Its module entry point also accepts the retriever's string output. The copied golden-set script also assumes a dictionary, and its reference answers are labelled as placeholders, so it is not used by this runner. The two-question runner is a small teaching check, not a comprehensive benchmark. No dummy-context fallback is used.

## Classroom upload walkthrough

The Upload documents tab streams an **Inside your upload** walkthrough: parsing/classification, selected parser and chunking settings, expandable actual chunks (full text, IDs and metadata), saving, persisted storage verification and completion. Chroma and BM25 counts verify this upload's chunk IDs. The graph count is labelled as the whole knowledge base and does not claim graph extraction succeeded for a particular file.

This is implemented in `backend/app/upload_trace.py` by calling the original `configure_settings`, `parse_file`, `chunk_document` and `index_chunks` functions in the same order; no `rag_v2` source edits are needed. The standard JSON upload endpoint remains available, and `?trace=true` enables streamed progress. The walkthrough remains visible while switching tabs, until another upload or a page refresh.

## Fresh clone

Credentials, uploaded files, local database contents and generated evaluation reports are excluded from Git. After cloning, configure `.env` and upload your own documents in the Upload documents tab. The local development copy includes previously indexed documents, but a fresh clone starts with an empty knowledge base. Upload `backend/tests/fixtures/travel-planner-demo.md` to try its example prompt; the Veridia prompt and evaluation also require the corresponding document to be uploaded.

## PNG charts and uploaded transcripts

PNG uploads use LlamaIndex `ImageBlock` and its `OpenAI` integration to send images to a vision model (`RAG_VISION_MODEL`, default `gpt-4o-mini`) to extract visible meaning, labels, relationships, values and trends. Meaningful descriptions are chunked with LlamaIndex `MarkdownNodeParser`; blank/unreadable images are rejected before indexing. This uses paid OpenAI calls.

Upload transcript JSON, SRT or VTT files. LlamaIndex `JSONReader` loads JSON (including transcript exports) as text; `pysubs2` reads SRT/VTT caption text. LlamaIndex `TokenTextSplitter` chunks the resulting document with a 512-token budget and 50-token overlap. JSON fields, including timestamps, remain in the text; no per-chunk timestamp metadata is assigned. Plain TXT scripts continue to use content-based strategy selection.

As explicitly requested, the travel-planner copy's `parser.py` and `chunker.py` now include this support, with a vision helper in `image_parser.py`. Earlier notes about all RAG code being byte-identical refer to the original implementation; the evaluator was simplified and graph retrieval was connected on request; other original RAG Python files remain unchanged. The source project in Documents/agents and the downloaded multimodal project are untouched.

Graph retrieval uses LlamaIndex `KnowledgeGraphRAGRetriever` with the existing `SimpleGraphStore`, follows relationships up to two hops, and joins vector/BM25 results in reciprocal-rank fusion before LLM reranking. Logs show graph candidates after fusion. Empty graph matches add no evidence. Graph results are labelled as extracted relationships because the original graph does not store source filenames. This compatible LlamaIndex retriever is deprecated upstream; migration to PropertyGraphIndex would require a separate storage change.
