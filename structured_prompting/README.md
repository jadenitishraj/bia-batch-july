# Structured Prompting — the practical lab

Four small notebooks, one per technique from the **Structured Prompting** deck
(`presentations/structured-prompting.html`). Every notebook follows the same shape:
a real business situation, the wrong prompt, then the right prompt.

| Notebook | Technique | The scenario |
| --- | --- | --- |
| `1_chain_of_thought.ipynb` | Show the working | Ordering workshop materials · reading customer feedback |
| `2_tree_of_thought.ipynb` | Try three, keep the best | Choosing a venue for the company offsite |
| `3_graph_of_thought.ipynb` | Combine the pieces | Four regional reports into one honest summary |
| `4_react.ipynb` | Look it up, don't guess | A customer asks for a refund — the agent checks the real order |

Notebooks 1–3 use plain prompts. Notebook 4 uses LangChain — the same
`create_agent` you saw in the `simple_agent_chatbot` project.

## Setup (once)

LangChain 1.x needs **Python 3.10 or newer**. Check first:

```bash
python3 --version
```

If that says 3.9 (the default on many Macs), install a newer Python and use it
below in place of `python3`.

```bash
cd structured_prompting
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m ipykernel install --user --name structured-prompting --display-name "Structured Prompting (.venv)"
cp .env.sample .env
```

That last install line registers the kernel, so **"Structured Prompting (.venv)"**
shows up in the kernel list of Jupyter and VS Code. Use it.

Open `.env` and paste your OpenAI key. Then:

```bash
.venv/bin/jupyter lab
```

Run the notebooks in order, top to bottom, with **Shift+Enter**.
Each one takes about 10 minutes.

## If an import fails

`ModuleNotFoundError: No module named 'langchain'` (or `openai`) means the notebook
is running a **different Python** from the one you installed into — the usual cause
in a classroom.

Step 0 of every notebook now handles this: it installs whatever is missing into the
Python the notebook is actually using, and stops with a clear message if that Python
is older than 3.10. So:

1. Run **Step 0** and read what it prints.
2. If it says the Python is too old, use **Kernel > Change Kernel** and pick
   "Structured Prompting (.venv)".
3. If it installed something, restart the kernel and run from the top.

The notebooks also run on **Google Colab** with no setup: Step 0 installs the
libraries, and Step 1 reads your key from the Colab **Secrets** panel (the key icon
on the left) if you add one named `OPENAI_API_KEY`. Otherwise it asks you to type it.

## The one rule about your key

The key goes in `.env` and nowhere else. `.env` is git-ignored.
Never paste a key into a notebook cell — notebooks get shared, keys get stolen.
