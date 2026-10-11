"""External validation for the live ticket notebook; no paid/network calls.

Run with the notebook dependencies installed:
    python validation/test_microsoft_ticket_solver.py
Fixtures below are test support, not part of the teaching implementation.
"""
import ast
import asyncio
import contextlib
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx2
from openai import AsyncOpenAI
import agent_framework.openai as provider
from agent_framework import InMemoryCheckpointStorage, WorkflowContext

NOTEBOOK = Path(__file__).resolve().parents[1] / "Simple_Microsoft_Agent_Framework_Ticket_Solver.ipynb"
SAMPLE = "My account is locked and I have an important meeting in 10 minutes."

class FixedAgent:
    """Deterministic test responses; not an LLM or arbitrary-ticket classifier."""
    def __init__(self):
        self.prompts = []

    async def run(self, prompt):
        self.prompts.append(prompt)
        if prompt.startswith("Summarize"):
            text = "The customer needs urgent access to a locked account before a meeting."
        elif prompt.startswith("Return only one category"):
            text = "account"
        elif prompt.startswith("Return only one urgency"):
            text = "high"
        elif "Give the final decision:" in prompt:
            text = "Yes. Escalate to a human because account access is time-sensitive."
        else:
            text = "I'm sorry your account is locked. Please try the account recovery option; our support team can help urgently before your meeting."
        return SimpleNamespace(text=text)

async def validate():
    notebook = json.loads(NOTEBOOK.read_text())
    requests, states, routed = [], [], []
    fixture = FixedAgent()
    original_set, original_send = WorkflowContext.set_state, WorkflowContext.send_message

    def record_set(ctx, key, value):
        if key == "ticket":
            assert all(ctx.get_state(k) is None for k in ("ticket", "analysis", "decision", "reply"))
            assert all(ctx.state is not state for state in states)
            states.append(ctx.state)
        return original_set(ctx, key, value)

    async def record_send(ctx, message, *args, **kwargs):
        assert message == "continue"
        routed.append(message)
        return await original_send(ctx, message, *args, **kwargs)

    async def respond(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert len(payload["messages"]) == 1
        text = (await fixture.run(payload["messages"][-1]["content"])).text
        return httpx2.Response(200, json={
            "id": "test-response", "object": "chat.completion", "created": 0,
            "model": payload["model"], "choices": [{"index": 0,
                "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        })

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as http:
        sdk = AsyncOpenAI(api_key="test-placeholder", http_client=http)
        original_provider = provider.OpenAIChatCompletionClient

        def build_client(*args, **kwargs):
            assert kwargs["api_key"] == "test-placeholder"
            assert kwargs["base_url"] == "https://api.openai.com/v1"
            kwargs["async_client"] = sdk
            return original_provider(*args, **kwargs)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-placeholder"}, clear=True), \
             patch.object(provider, "OpenAIChatCompletionClient", build_client), \
             patch.object(WorkflowContext, "set_state", record_set), \
             patch.object(WorkflowContext, "send_message", record_send), \
             contextlib.redirect_stdout(io.StringIO()) as captured:
            namespace = {}
            for index, cell in enumerate(notebook["cells"]):
                if cell["cell_type"] != "code":
                    continue
                source = "\n".join(line for line in "".join(cell["source"]).splitlines()
                                   if not line.startswith("%pip"))
                result = eval(compile(source, f"cell-{index}", "exec",
                                      flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT), namespace)
                if result is not None:
                    await result
            first = namespace["result"]
            assert len(requests) == 5
            assert all(r["model"] == "gpt-4o-mini" for r in requests)
            # Compare the original LangGraph node prompts/outputs, not a rewritten algorithm.
            original = json.loads((NOTEBOOK.parent / "Simple_LangGraph_Ticket_Solver.ipynb").read_text())
            langgraph_ns = {}
            for cell in original["cells"]:
                source = "".join(cell["source"])
                if cell["cell_type"] == "code" and any(marker in source for marker in ("class TicketState", "def clean_node", "def analyse_node", "def decision_node", "def reply_node")):
                    exec(source, langgraph_ns)
            original_prompts = []
            answers = iter([first["analysis"]["summary"], first["analysis"]["category"],
                            first["analysis"]["urgency"], first["decision"], first["reply"]])
            class OriginalModel:
                def invoke(self, prompt):
                    original_prompts.append(prompt)
                    return SimpleNamespace(content=next(answers))
            langgraph_ns["model"] = OriginalModel()
            original_state = {"ticket": SAMPLE}
            for step in ("clean_node", "analyse_node", "decision_node", "reply_node"):
                original_state.update(langgraph_ns[step](original_state))
            assert original_state == first
            assert original_prompts == [r["messages"][-1]["content"] for r in requests]
            second = await namespace["solve_ticket"]("  Another customer ticket  ")
            assert second["ticket"] == "Another customer ticket"
            assert first["ticket"] == SAMPLE
            assert second["analysis"] is not first["analysis"]
            assert len(requests) == 10
            before = len(requests)
            try:
                await namespace["solve_ticket"]("   ")
            except Exception as exc:
                errors = []
                while exc is not None:
                    errors.append(str(exc))
                    exc = exc.__cause__ or exc.__context__
                assert any("Ticket cannot be empty." in error for error in errors)
            else:
                raise AssertionError("Empty input must fail")
            assert len(requests) == before
            a, b = await asyncio.gather(namespace["create_workflow"]().run("First ticket"),
                                        namespace["create_workflow"]().run("Second ticket"))
            assert a.get_outputs()[0]["ticket"] == "First ticket"
            assert b.get_outputs()[0]["ticket"] == "Second ticket"
            storage = InMemoryCheckpointStorage()
            workflow = namespace["create_workflow"]()
            full = await workflow.run(SAMPLE, checkpoint_storage=storage)
            checkpoints = await storage.list_checkpoints(workflow_name=workflow.name)
            saved = next(c for c in checkpoints if "analysis" in c.state and "decision" not in c.state)
            before = len(requests)
            replay = await namespace["create_workflow"]().run(
                checkpoint_id=saved.checkpoint_id, checkpoint_storage=storage)
            assert len(requests) - before == 2
            assert replay.get_outputs() == full.get_outputs()
            assert "test-placeholder" not in captured.getvalue()
            assert namespace["TicketState"].__required_keys__ == frozenset({"ticket", "analysis", "decision", "reply"})
            assert namespace["TicketState"].__optional_keys__ == frozenset()
    assert len(states) == 5
    assert len(routed) == 16  # 5 complete runs, plus the replay's decision trigger.
    print("PASS: full live notebook through real Agent/provider/SDK with intercepted HTTP; "
          "original model/schema/prompts/sample/output fidelity; five calls per ticket; validation/typing; repeated/concurrent native state isolation; "
          "optional checkpoint replay runs only decision/reply. No network or paid calls.")

if __name__ == "__main__":
    asyncio.run(validate())
