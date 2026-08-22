# Prompt Essentials — coding practices for Claude

A notebook-first teaching lab for prompt design. The audience is learners, not maintainers, so
**the code is the teaching material**. Every choice below follows from that: readability and a
notebook that always runs beat cleverness and coverage.

Read `README.md` for setup and `trainer_guide.md` for how the session is actually taught before
changing anything substantial.

## Before you start

- Work inside the venv: `source .venv/bin/activate` (it already exists here). If a package is
  missing, `pip install -r requirements.txt` — do not install ad-hoc packages into the lab.
- Dependencies in `requirements.txt` are **pinned on purpose** so a classroom of 20 machines
  behaves identically. Do not bump a version unless something is broken, and if you do, bump the
  pin — never leave it unpinned.
- `.env` holds a real API key. Never print it, echo it, paste it into a notebook cell, or commit
  it. `.env.sample` is the only file that shows key names, and it shows placeholders only.
- Anything you add that needs configuration gets a placeholder line in `.env.sample` and a note in
  the README's `.env` section.

## The rule that governs everything: the notebook must run without an API key

`utils.py` has two paths — live API mode, and a simulated fallback used when `OPENAI_API_KEY` is
absent or a call fails (`invoke_messages` catches `Exception` and returns `simulated_output`).
That is not defensive sloppiness, it is the feature that lets a trainer teach on airplane wifi.

So:

- Any new helper that calls the model returns a `PromptRunResult` and degrades to a fallback the
  same way. Never let a missing key raise out into a notebook cell.
- Add the matching fallback text to `simulated_output()` and document it in `sample_outputs.md`.
  Fallback text must be *plausible model output* — learners compare it against live output.
- `build_chat_model()` is the one place allowed to raise on a missing key, because callers catch it.

## Python style

Match `utils.py`. It is the reference file:

- Module docstring at the top saying what the file is for, in plain English.
- `from __future__ import annotations`, then stdlib, then third-party imports.
- Type hints on every public function. Keyword-only arguments (`*,`) for anything tunable, so call
  sites read as `temperature=0.9` rather than a bare positional.
- Google-style docstrings with `Args:` / `Returns:` / `Raises:` on **every** function, including
  short ones. Learners read these.
- Small pure functions with one job. `try_parse_json`, `has_required_keys`, `normalize_content` are
  the size to aim for.
- `@dataclass` for anything with more than two related fields, not a bare dict or tuple.
- Comments explain *why*, not what — see the LangSmith legacy-variable comment in `load_settings()`.
- No clever one-liners a beginner has to decode. Write the value out.
- Optional third-party imports go in a `try/except Exception` block that sets the name to `None`,
  with a runtime error later that tells the user exactly which pip command fixes it.

Formatting: 4-space indent, ~100 column soft limit, double quotes, snake_case functions,
UPPER_SNAKE module constants (`DEFAULT_MODEL_NAME`).

## Notebook practices

- One idea per cell, with a markdown cell above it explaining the idea before the code runs.
- Cells must be runnable **top to bottom, in order, on a fresh kernel**. No cell may depend on
  something defined only in a cell below it or in a previously-deleted cell.
- Keep logic in `utils.py` and call it from the notebook. A notebook cell should show the *prompt*
  and the *comparison*, not plumbing.
- Every model call passes `run_name=` so the LangSmith trace is readable, and `fallback_label=` so
  the offline path produces the right text.
- Never commit a notebook containing real output with keys, account names, or personal data in it.
- Keep the numbered classroom flow in the README in sync if you add or reorder a section.

## Prompt and model practices

- Model name comes from `OPENAI_MODEL` in `.env` (default `gpt-4o-mini`). Never hardcode a model
  name in the notebook — cost matters, and trainers switch models.
- Tune `temperature` **or** `top_p`, not both at once; that is the point of the sampling section.
- When a prompt must produce machine-readable output, state the contract in the system message,
  list the required keys, and validate with `try_parse_json` + `has_required_keys`. Never regex a
  JSON blob out of prose.
- New or edited prompts get run through `prompt_quality_checklist.md` before you call them done.
- Keep prompts and examples short. Token cost is visible to the class via
  `estimate_demo_cost_usd`, and a full live run should stay under about $0.05.

## Data

`data/support_tickets.csv` and `data/travel_requests.jsonl` are small, synthetic, and deliberately
messy in places — the mess is the debugging lab. Do not "clean" them. If you need new examples, add
rows in the same shape rather than introducing a third file.

## Verifying a change

Do not assume it works. Minimum bar before saying a change is done:

```bash
python -c "import utils; s = utils.load_settings(); utils.print_environment_status(s)"
```

Then, for a notebook change, restart the kernel and run all cells — **twice**: once with a key
present and once with `OPENAI_API_KEY` unset, to prove the fallback path still works.

```bash
env -u OPENAI_API_KEY jupyter lab
```

If you touched `utils.py`, restart the notebook kernel — `.env` and the module are both read once
at import.

## Scope

This package sits inside the `bia-batch-july` course repo. The slide decks are shared across the
course and live in `../presentations/` — do not copy them in here. Keep this directory to the
notebook, its helpers, its data, and the four markdown guides.
