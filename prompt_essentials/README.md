# Prompt Essentials Practical Lab

A notebook-first practical package for learning how to design, template, test, and debug prompts for LLM applications.

This package complements the Prompt Essentials theory deck. It focuses on hands-on comparison: vague vs structured prompts, zero-shot vs one-shot vs few-shot prompts, sampling behavior, system messages, LangChain prompt templates, and LangSmith tracing.

## Prerequisites

- Python 3.10 or 3.11
- VS Code or JupyterLab
- OpenAI API key for live model calls
- Optional LangSmith account and API key for tracing
- Windows, macOS, or Linux

The notebook can run without an API key using built-in simulated outputs. Live calls are recommended for the full classroom experience.

## Setup

### Option A: venv

```bash
cd prompt_essentials
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
python -m ipykernel install --user --name prompt-essentials --display-name "Prompt Essentials"
```

### Option B: conda

```bash
cd prompt_essentials
conda create -n prompt-essentials python=3.11 -y
conda activate prompt-essentials
pip install -r requirements.txt
python -m ipykernel install --user --name prompt-essentials --display-name "Prompt Essentials"
```

## Configure `.env`

Copy the sample file:

```bash
cp .env.sample .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.sample .env
```

Edit `.env`:

```text
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

For LangSmith tracing, also set:

```text
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_your-langsmith-key-here
LANGSMITH_PROJECT=BIA_Prompt_Essentials
```

## How to run

Launch JupyterLab:

```bash
jupyter lab
```

Open `notebook.ipynb` and select the `Prompt Essentials` kernel if prompted.

Recommended classroom flow:

1. Run the setup cells.
2. Run the bad-vs-good prompt comparison.
3. Compare zero-shot, one-shot, and few-shot outputs.
4. Run the sampling parameter experiment.
5. Run the system-message JSON contract experiment.
6. Convert a prompt into a reusable LangChain template.
7. Enable LangSmith tracing and inspect the trace.
8. Complete the debugging lab.

## What each file does

- `notebook.ipynb` — main guided practical lab.
- `utils.py` — helper functions for environment checks, live model calls, fallback outputs, and JSON validation.
- `.env.sample` — safe template for API keys and tracing configuration.
- `requirements.txt` — pinned dependencies for the practical.
- `README.md` — setup and run instructions.
- `trainer_guide.md` — minute-by-minute teaching guidance and troubleshooting.
- `sample_outputs.md` — expected fallback outputs for offline teaching.
- `prompt_quality_checklist.md` — reusable prompt debugging checklist.
- `data/support_tickets.csv` — small ticket-routing dataset for examples.
- `data/travel_requests.jsonl` — travel request examples for the debugging lab.

## Expected output

You should see:

- A setup status showing whether live model calls and LangSmith tracing are enabled.
- Side-by-side outputs showing how better prompts produce more specific answers.
- A comparison of zero-shot, one-shot, and few-shot classification behavior.
- Different response styles when temperature changes.
- JSON-style outputs from stronger system-message prompts.
- A reusable `ChatPromptTemplate` example.
- LangSmith traces if tracing is enabled.

## Estimated API cost

A full live run uses short text prompts and should typically stay below **$0.05** with `gpt-4o-mini`, assuming normal classroom use and no repeated reruns. The exact cost depends on how often cells are rerun and current API pricing.

The notebook includes a small cost-estimation helper so trainers can discuss token cost without needing a separate billing dashboard.

## Troubleshooting

### `OPENAI_API_KEY not found`

Check that `.env` exists in the project root and contains the key. Restart the notebook kernel after editing `.env`.

### LangSmith traces do not appear

Check that:

```text
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=BIA_Prompt_Essentials
```

Then rerun the setup cell and one model-call cell.

### `ModuleNotFoundError`

Activate the correct virtual environment and run:

```bash
pip install -r requirements.txt
```

Then restart the notebook kernel.

### JSON parsing fails

This is a teaching moment. It means the prompt did not create a strong enough output contract. Improve the system message, explicitly require valid JSON, and list required keys.

## Further reading

- OpenAI prompt engineering guide
- OpenAI API reference
- LangChain prompt template documentation
- LangSmith observability and tracing documentation
