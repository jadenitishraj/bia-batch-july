# Records everything that happened during one chatbot answer.
# This is what the "eye" button in the app shows, so students can see exactly what was
# sent to the LLM, which tools it asked for, and what those tools sent back.

import json

from agents import ItemHelpers
from agents.items import MessageOutputItem, ToolCallItem, ToolCallOutputItem


def read_arguments(raw: str) -> dict:
    """The LLM sends tool arguments as a JSON string. Turn it back into a dictionary."""
    return json.loads(raw or "{}")


def list_steps(result) -> list[dict]:
    """Walk through the run and describe each thing that happened, in order."""
    steps = []
    tool_of_call = {}  # remembers which tool a call id belonged to

    for item in result.new_items:
        if isinstance(item, ToolCallItem):
            tool_of_call[item.raw_item.call_id] = item.raw_item.name
            steps.append(
                {
                    "who": "LLM",
                    "what": "asked us to run a tool",
                    "tool": item.raw_item.name,
                    "arguments": read_arguments(item.raw_item.arguments),
                }
            )

        elif isinstance(item, ToolCallOutputItem):
            call_id = dict(item.raw_item).get("call_id")
            steps.append(
                {
                    "who": "Our Python code",
                    "what": "ran the tool and sent the result back to the LLM",
                    "tool": tool_of_call.get(call_id, "unknown"),
                    "result": item.output,
                }
            )

        elif isinstance(item, MessageOutputItem):
            steps.append(
                {
                    "who": "LLM",
                    "what": "wrote the final answer",
                    "text": ItemHelpers.text_message_output(item),
                }
            )

    return steps


def build_trace(agent, message: str, history: list[dict], result) -> dict:
    """Everything a student needs to understand one question and its answer."""
    usage = result.context_wrapper.usage
    return {
        "sent_to_llm": {
            "model": agent.model,
            "system_instructions": agent.instructions.strip(),
            "tools_offered": [tool.name for tool in agent.tools],
            "conversation_so_far": history,
            "new_user_message": message,
        },
        "steps": list_steps(result),
        "conversation_after_the_run": result.to_input_list(),
        "usage": {
            "calls_to_the_llm": usage.requests,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
        },
    }
