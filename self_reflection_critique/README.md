# Self-Reflection & Critique Practical

Build a writing critic agent that improves a draft through a generate → critique → refine loop.

You paste a draft into the terminal and watch the score move. The system judges your text against explicit criteria, creates reflection memory, revises the draft, and stops when a threshold is met or the retry budget runs out.

The brief, rubric and constitution stay as files. Those are the standards, and every run has to be graded against the same bar for the scores to be comparable. The draft is the only thing you supply.

## Prerequisites

- Python 3.10 or 3.11
- VS Code, Jupyter, or another notebook runner
- An OpenAI API key for live model calls
- Optional: AutoGen packages for the evaluator-agent preview cell

## Setup

Download or clone this folder, then open a terminal in the project root.

### Option A: virtual environment

```bash
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
```

### Option B: conda environment

```bash
conda create -n self-reflection-critique python=3.11 -y
conda activate self-reflection-critique
pip install -r requirements.txt
```

### Configure environment variables

```bash
cp .env.sample .env
```

Add your OpenAI API key to `.env`:

```text
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

For a no-network classroom fallback, set:

```text
BIA_OFFLINE_DEMO=true
```

## How to run

### Notebook path

```bash
jupyter notebook notebook.ipynb
```

Run all cells from top to bottom. Nothing asks for anything until the last code cell, which prompts you to paste a draft.

**To finish entering the draft, type `END` on a line of its own, or press Enter twice.** The box reappearing after each line is it asking for the next line, not an error.

That one cell prints the entire run:

1. the draft you gave it,
2. for every round — what the critic saw, exactly what it returned (score, issues, severities, revision instructions, reflection memory), and the rewrite the refiner produced from it,
3. a bar chart of how the score moved across the rounds,
4. the verdict, and the final draft at the bottom.

The notebook prints everything and writes nothing, so the whole run stays on screen where the room can see it.

### Command-line path

```bash
python main.py
```

It asks you to paste a draft. Type as many lines as you like, then finish with `END` on a line of its own, two blank lines, or Ctrl-D:

```text
==============================================================================
Paste the draft you want the critic to improve.
To finish: type END on a line of its own, or press Enter twice.
==============================================================================
draft (END to finish) > AI is changing the world and you should learn it now.
draft (END to finish) > Join now to become future ready.
draft (END to finish) > END
```

It then prints the iteration trace, the outcome, and saves outputs to `demo_outputs/`.

You can also pipe a file in, since Ctrl-D and end-of-input are treated the same way:

```bash
python main.py < my_draft.txt
```

### Optional AutoGen preview

AutoGen is only previewed here. Install the optional dependencies when you want to run the AutoGen evaluator-agent cell:

```bash
pip install -r requirements_autogen.txt
```

## What each file does

- `notebook.ipynb` — guided walkthrough; run every cell, the last one asks for your draft and prints the whole run.
- `main.py` — command-line version; asks you to paste a draft, prints the run, and saves it to `demo_outputs/`.
- `critic_loop.py` — reusable generate, critique, refine, and loop functions.
- `llm_client.py` — OpenAI client wrapper with JSON mode and offline fallback.
- `prompts.py` — prompt builders for generator, critic, and refiner roles.
- `schemas.py` — Pydantic models for structured evaluator output.
- `autogen_evaluator_preview.py` — optional AutoGen wrapper for a critic agent.
- `data/writing_brief.txt` — main classroom writing task (the standard, not the input).
- `data/rubric.md` — scoring criteria.
- `data/constitution.md` — principles for safe and useful critique.
- `data/travel_planner_bridge_brief.txt` — bridge to the upcoming travel planner build.
- `.env.sample` — environment variable template.
- `requirements.txt` — pinned core dependencies.
- `requirements_autogen.txt` — pinned optional AutoGen dependencies.
- `trainer_guide.md` — teaching flow, timings, questions, and troubleshooting.

## Expected output

A typical marketing-style draft scores low on the first pass — usually 3 or 4 out of 10 — because it is fluent but vague, hype-heavy and thin on evidence. Watch the score on each round rather than the final text.

A run will show:

- one to three critique iterations,
- structured JSON critique,
- reflection memory after each attempt,
- a clear PASSED or NOT PASSED verdict with the score behind it.

The notebook prints all of that in the cell output. The CLI prints it too, and additionally saves `final_draft.txt` and `iteration_trace.json` into `demo_outputs/` so a trainer can reopen a run after class.

**A run that never reaches 8/10 is a normal result, not a bug.** Scores of 3 → 7 → 7 mean the loop fixed everything that was a wording problem and then ran out of things it could fix without new facts. That plateau is the most useful thing in the demo, so both the notebook and the CLI label it `NOT PASSED` instead of presenting a 7/10 as a finished draft. In that case the draft shown was never scored — it is the rewrite made after the last critique, produced just as the retry budget ran out.

## Estimated API cost

With `gpt-4o-mini`, the full demo usually uses a small number of short text calls. A typical classroom run should stay well below ₹50 / US$0.50, depending on current provider pricing, prompt length, and the number of retries.

## Troubleshooting

**`OPENAI_API_KEY was not found`**  
Copy `.env.sample` to `.env`, add the key, and restart the notebook kernel.

**Evaluator output is not valid JSON**  
Re-run the critique cell. If it repeats, lower the model temperature to `0.0` and confirm the prompt still says “Return ONLY valid JSON.”

**AutoGen import error**  
The AutoGen preview uses a separate optional requirements file. Run `pip install -r requirements_autogen.txt`.

**The loop stops without passing**  
That is expected on a weak draft. Reduce `PASS_SCORE` in `main.py` to 7 for a quick classroom demo, or raise `MAX_ITERATIONS` for deeper refinement.

**The input box keeps coming back and will not let me out**  
That is the reader asking for the next line of your draft. Type `END` on a line of its own, or press Enter twice, to finish. `end`, `End` and `DONE` all work too. In a terminal, Ctrl-D also ends the input.

## Further reading

- Reflexion: Language Agents with Verbal Reinforcement Learning — https://arxiv.org/abs/2303.11366
- Self-Refine: Iterative Refinement with Self-Feedback — https://arxiv.org/abs/2303.17651
- Constitutional AI: Harmlessness from AI Feedback — https://arxiv.org/abs/2212.08073
- OpenAI Python SDK — https://pypi.org/project/openai/
- AutoGen AgentChat documentation — https://microsoft.github.io/autogen/stable/
