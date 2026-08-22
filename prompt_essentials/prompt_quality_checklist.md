# Prompt Quality Checklist

Use this checklist while debugging prompts during the lab.

## 1. Task clarity

- Does the prompt say exactly what task should be completed?
- Is the input clearly separated from the instruction?
- Is the desired output format explicit?

## 2. Context and role

- Is the model told what role it is playing?
- Does the role add useful constraints, or is it just decorative?
- Are domain limits and uncertainty rules stated?

## 3. Constraints

- Does the prompt specify what the model must not do?
- Does it say what to do when information is missing?
- Does it avoid asking the model to invent live facts?

## 4. Examples

- Is zero-shot enough for the task?
- Would one example clarify format?
- Would a few examples teach edge cases?
- Are examples realistic and not misleading?

## 5. Output contract

- Can another program parse the output?
- Are required keys listed?
- Are allowed values constrained?
- Is the output short enough to be useful?

## 6. Trace-based debugging

- Which exact prompt version produced the bad output?
- Was the failure caused by unclear task, weak examples, missing constraints, or sampling?
- Did the revised prompt improve the specific failure?
