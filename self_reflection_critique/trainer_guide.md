# Trainer Guide — Self-Reflection & Critique Practical

## Demo goal

Build a writing critic agent that takes a draft **the room supplies**, evaluates it against a rubric, writes reflection memory, revises the draft, and stops when the score passes a threshold or the retries run out.

The practical is intentionally framed around writing quality because everyone in the room can judge whether the answer improved. The same loop then transfers to agent outputs such as travel itineraries, research summaries, code reviews, and retrieval answers.

## Recommended teaching flow

### 0–10 min — Reconnect to prior prompting work

Ask a student to write four or five lines of marketing copy on the spot, or paste in one you prepared. Put it on the screen and ask: “What is wrong with this answer even though it sounds acceptable?”

Do not use a saved sample file. The point of the session is that the loop improves *a draft somebody handed it*, and that is invisible if the input was typed into a file last week.

Expected observations:
- too generic,
- no strong audience fit,
- vague promise of opportunities,
- weak call to action,
- does not prove practical value.

### 10–20 min — Explain the loop before code

Draw this verbally before opening functions:

```text
brief + draft
    ↓
critic scores against rubric
    ↓
reflection memory captures lesson
    ↓
refiner rewrites
    ↓
stop if score ≥ threshold or max retries reached
```

Emphasize that the code, not the model, owns the stopping rule.

### 20–35 min — Run setup and inspect files

Open `notebook.ipynb` and run every cell from the top. Nothing prompts you and no model call fires until the last cell, so you can walk through the three standards while the rest of the notebook is already loaded:
- `writing_brief.txt`,
- `rubric.md`,
- `constitution.md`.

Then run the last cell. It asks for the draft — paste the class's text in front of them and type `END` on its own line (pressing Enter twice does the same thing). Everything after that prints in that one cell: each critic response, each rewrite, the score on every round, and the final draft at the bottom.

On the command line the same thing happens with `python main.py`.

Two things to say out loud:

- The critic needs both a rubric and principles. Without those, critique becomes vague opinion.
- The standards stay as files on purpose. If students supplied those too, every run would be graded against a different bar and no two scores could be compared.

### 35–55 min — Run the first critique

Run the critique cell first, before showing full automation. Let the class inspect the JSON.

Talking points:
- `score` is useful for thresholding,
- `issues` are useful for targeted revision,
- `reflection_memory` is useful across retries,
- `revised_strategy` tells the next model call how to improve.

### 55–75 min — Run one refinement manually

Show how the refiner uses the structured critique. Compare before and after.

Good questions to ask:
- Which issue was fixed?
- Which issue remained?
- Did the revision add unsupported claims?
- Would this pass the original brief?

### 75–90 min — Run the full loop

Run `run_refinement_loop(...)`.

Explain the three controls:
- `pass_score`,
- `max_iterations`,
- blocking issues.

The notebook prints the whole run in the last cell's output — nothing is written to a file, so it stays on screen in front of the room. Scroll back through it and read one critic response aloud in full: the class should see that every issue names a criterion, a severity, what is wrong, and what to change.

Land the verdict properly. If the run stops below the pass mark, say so out loud: the loop fixed every wording problem it could find and then hit a wall, because what is left needs a fact nobody gave it. Do not read the last draft out as if it passed.

If you want a copy of a run to open after class, use `python main.py` instead — the CLI saves `final_draft.txt` and `iteration_trace.json` to `demo_outputs/`.

### Optional extension — AutoGen evaluator preview

Only run the AutoGen preview when setup is stable and time remains. Position it as a role-wrapping preview, not a deep framework lesson.

## Likely questions and ideal answers

**Why not simply ask the model to improve the answer?**  
Because “improve” is vague. Rubrics create criteria, JSON output creates inspectable structure, and thresholds create a stopping rule.

**Can the same model critique its own output reliably?**  
It can help, but it is not a guarantee. Reliability improves when the critic receives explicit criteria, examples, external evidence, or a separated evaluator role.

**Why use reflection memory if the full critique is already available?**  
Reflection memory compresses the lesson from a failed attempt. It is useful when the next attempt should remember the pattern, not the entire prior critique.

**What makes this different from ReAct?**  
ReAct helps an agent reason and act during a task. This loop helps the system evaluate the result, learn from feedback, and retry with a better strategy.

**Should every production agent use self-reflection?**  
No. Use it where quality matters enough to justify extra latency and cost. Do not add it blindly to simple, deterministic tasks.

**What if the evaluator is wrong?**  
Treat evaluator output as another model output. Calibrate it with examples, compare to human judgments, and use external checks when factual correctness matters.

**Why separate generator, critic, and refiner roles?**  
Role separation reduces prompt confusion and makes the system easier to debug. It also prepares the architecture for multi-agent workflows.

**Does a higher score mean the answer is factually true?**  
Not necessarily. A score is only as good as the rubric and available evidence. For factual tasks, add tools, retrieval, or verification checks.

## Common errors and fixes

**Missing API key**  
Use `.env.sample`, create `.env`, fill `OPENAI_API_KEY`, and restart the kernel.

**JSON parsing failure**  
Re-run with temperature `0.0` for the critic. Confirm the critic prompt still requests only JSON.

**Draft becomes too long**  
Add word count enforcement to the critic rubric or lower the refiner token budget.

**AutoGen dependency conflict**  
Skip the optional AutoGen cell. The direct evaluator loop is the core practical for this session.

**Network or billing issue during class**  
Set `BIA_OFFLINE_DEMO=true` and re-run. The deterministic fallback keeps the teaching flow intact.

## Demo timing controls

Essential:
- setup,
- inspect brief/rubric/constitution,
- run one critique,
- run one refinement,
- run the full loop.

Skip if running short:
- generated first draft from scratch,
- AutoGen preview,
- bridge brief customization.

## Extension ideas

- Replace the writing brief with a travel itinerary brief.
- Add a second evaluator focused only on factual claims.
- Add a “no unsupported promises” validator.
- Compare self-critique vs evaluator-generator scoring.
- Save every iteration to a trace dashboard in a later observability session.

## What this prepares for

The same critique loop will be useful in the upcoming travel planner build. There, the evaluator can critique itinerary feasibility, budget realism, personalization, and missing constraints before the final itinerary is shown.
