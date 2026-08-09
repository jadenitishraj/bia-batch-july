"""
trace.py
--------
This file is only for LEARNING. It does not make the agent smarter.

Its job: take the list of messages that LangChain produced, and show
every phase of what happened, in the terminal and in the React screen.

You need to understand ONE thing here: the agent is just a LIST OF MESSAGES
that keeps growing. There are 4 kinds of message:

  SystemMessage  -> the rules (our system prompt)
  HumanMessage   -> what the user typed
  AIMessage      -> what the model answered.
                    IMPORTANT: if the model wants a tool, this message has
                    an empty text and a `tool_calls` list instead.
  ToolMessage    -> the RESULT that our python function returned.
                    This is sent BACK to the model as a new message.

So a tool call is really:
    AIMessage(tool_calls=[add(2,3)])   ->   ToolMessage("5")   ->   AIMessage("The answer is 5")

The model never runs your code. It only asks for it. LangChain runs the
function and puts the answer back into the message list as a ToolMessage.
"""


def build_steps(messages, system_prompt=""):
    """
    Turn a list of LangChain messages into a simple list of steps
    that we can print and also send to the React frontend.

    Each step is a small dictionary: {"phase": ..., "title": ..., "detail": ...}

    Note: agent.py sends us only the messages of the CURRENT question.
    The older messages from short term memory are not shown here, otherwise
    the screen would repeat the whole conversation every time.
    """
    steps = []

    # LangChain keeps the system prompt inside the agent, not inside the
    # message list, so we add it here ourselves as the first phase.
    if system_prompt:
        steps.append({
            "phase": "SYSTEM PROMPT",
            "title": "Rules given to the model (sent before every question)",
            "detail": system_prompt,
        })

    for message in messages:
        kind = message.__class__.__name__

        if kind == "SystemMessage":
            steps.append({
                "phase": "SYSTEM PROMPT",
                "title": "Rules given to the model",
                "detail": message.content,
            })

        elif kind == "HumanMessage":
            steps.append({
                "phase": "USER MESSAGE",
                "title": "What the user typed",
                "detail": message.content,
            })

        elif kind == "AIMessage":
            # Case 1: the model decided to call one or more tools
            if message.tool_calls:
                for call in message.tool_calls:
                    steps.append({
                        "phase": "TOOL CALL",
                        "title": "Model asked for tool: " + call["name"],
                        "detail": "arguments = " + str(call["args"]),
                    })
            # Case 2: the model gave the final text answer
            else:
                steps.append({
                    "phase": "FINAL ANSWER",
                    "title": "Model answered the user",
                    "detail": message.content,
                })

        elif kind == "ToolMessage":
            steps.append({
                "phase": "TOOL RESULT",
                "title": "Our python function returned",
                "detail": str(message.content),
            })

    return steps


def print_steps(steps):
    """Print the steps in the terminal so the trainer can show them live."""

    print("\n" + "=" * 70)
    print("AGENT RUN - every phase, in order")
    print("=" * 70)

    number = 1
    for step in steps:
        detail = step["detail"]

        # Do not print a huge system prompt in the terminal
        if len(detail) > 300:
            detail = detail[:300] + " ...(cut)"

        print("\n[" + str(number) + "] " + step["phase"])
        print("    " + step["title"])
        print("    " + detail.replace("\n", "\n    "))
        number = number + 1

    print("\n" + "=" * 70 + "\n")
