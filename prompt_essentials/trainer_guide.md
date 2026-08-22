# Trainer Guide — Prompt Essentials Practical Lab

## Demo goal

By the end of the practical, the class should be able to move from casual prompting to a repeatable prompt engineering workflow:

1. Write a baseline prompt.
2. Identify what is missing.
3. Add structure, examples, constraints, and output format.
4. Convert the prompt into a reusable template.
5. Inspect the run in LangSmith.
6. Improve the prompt based on a visible failure.

## Teaching flow

### 0–10 min — Setup and positioning

Run the environment check. Explain the two modes:

- Live mode if `OPENAI_API_KEY` is configured.
- Fallback mode if the key is missing or the classroom network fails.

Emphasize that fallback mode is not fake code; it lets the notebook continue while preserving the live-call structure.

### 10–25 min — Bad prompt vs strong prompt

Run the vague customer complaint prompt first. Ask the room what is missing.

Then run the improved prompt with role, task, input boundaries, and output format.

Talking point: prompt engineering is not about clever wording; it is about reducing ambiguity.

### 25–45 min — Zero-shot, one-shot, few-shot

Use the ticket-routing dataset.

Recommended sequence:

1. Run zero-shot.
2. Run one-shot.
3. Run few-shot.
4. Compare output consistency and format control.

Talking point: few-shot is not automatically better. It is useful when examples clarify format, categories, or edge cases.

### 45–60 min — Sampling parameters

Run the low-temperature and high-temperature examples.

Keep the task simple so the difference is obvious.

Talking point: parameter choice depends on the job. Reliable classification should be stable; brainstorming can tolerate variation.

### 60–80 min — System messages and output contracts

Run the weak travel-assistant system message first. It should be broad and overconfident.

Then run the strong system message that requires JSON and asks for missing details.

Talking point: a system message is a behavior contract, not a guarantee. For production, combine it with validation.

### 80–100 min — LangChain prompt templates

Show why copy-pasting prompts becomes fragile.

Convert the support ticket prompt into `ChatPromptTemplate`.

Talking point: templates make prompt behavior reusable, testable, and easier to version.

### 100–125 min — LangSmith tracing

Enable LangSmith if available. Run one prompt with a clear `run_name`.

Open LangSmith and inspect:

- Input prompt
- Final output
- Run metadata
- Latency
- Token usage if available

Talking point: without traces, prompt debugging becomes guesswork.

### 125–150 min — Prompt debugging lab

Use the travel request prompt that invents assumptions.

Ask the class to identify the failure:

- Does it invent live weather?
- Does it ignore missing budget?
- Does it sound confident without evidence?
- Does it return a parseable output?

Then run the improved prompt.

### 150–160 min — Wrap-up

Connect the lab to the upcoming structured prompting work. The next step is not just better single prompts, but reasoning patterns that help agents plan, act, and revise.

## Likely questions and ideal answers

### Why not always use few-shot?

Few-shot examples cost tokens and can bias the model toward patterns that do not fit every input. Use them when the task needs examples for format, labels, tone, or edge cases.

### Is a system message stronger than a user message?

It is intended to provide higher-level behavioral guidance, but it is not a replacement for validation, policy checks, or application logic.

### Should temperature always be zero for business use?

No. Use low temperature for extraction, classification, and agent tool decisions. Use higher temperature for ideation, drafting, and creative exploration.

### Why use LangChain templates instead of f-strings?

Templates separate prompt design from variable data. They are easier to reuse, inspect, and trace. They also fit naturally into chains and agents later.

### What should I inspect first in LangSmith?

Start with the exact input and output. Then inspect latency, token usage, errors, and whether the prompt version matches what you expected to run.

### Does LangSmith improve the answer automatically?

No. LangSmith gives visibility. The developer still needs to diagnose and revise the prompt, examples, parameters, or application logic.

### Can prompt engineering prevent hallucination?

It can reduce hallucination by setting uncertainty rules and requiring missing-information questions, but it cannot eliminate hallucination by itself.

## Common errors and fixes

### Error: `OPENAI_API_KEY is missing`

The notebook will fall back to simulated outputs. For live calls, create `.env` from `.env.sample`, add the key, and restart the kernel.

### Error: `ModuleNotFoundError: langchain_openai`

The environment is missing dependencies. Activate the intended environment and run `pip install -r requirements.txt`.

### Error: LangSmith does not show traces

Check `LANGSMITH_TRACING=true`, confirm the API key, and ensure the model-call cell actually ran after enabling tracing.

### Error: JSON parsing fails

This is expected during the lab. Improve the prompt with explicit JSON instructions, required keys, and no markdown fences.

### Error: Model output differs from sample output

That is normal. The lab teaches behavior patterns, not exact wording. Compare whether the output follows the desired contract.

## Demo timing

The full practical fits into ~90 minutes if the trainer does not over-explain every code line. Focus on observing differences in outputs.

Essential cells:

1. Setup
2. Bad vs improved prompt
3. Zero/one/few-shot comparison
4. System message and JSON validation
5. PromptTemplate
6. LangSmith trace
7. Debugging lab

Optional if time is short:

- High-temperature creative variation
- Extra travel request examples
- Exercise discussion

## What to skip if running short

Skip repeated API reruns. Show one live run and use the fallback sample outputs for comparison.

Skip detailed package-version discussion. Keep focus on prompt behavior.

Skip advanced structured outputs. Formal output parsers and validation patterns appear later in the course.

## Extension ideas

- Add two more ticket categories and test whether few-shot examples still help.
- Create a prompt version log in a spreadsheet or markdown table.
- Add a simple unit test that fails if the JSON output does not include required keys.
- Compare the same prompt on a larger model and discuss cost vs quality.
- Ask the model to generate bad examples, then critique why they are bad.
