"""
math_tools.py
-------------
Math tools. One tool = one small python function.

The @tool decorator from LangChain turns a normal python function into a TOOL
that the model is allowed to call.

Two things are very important for the model:

1. The function NAME       -> the model uses it to pick the tool.
2. The DOCSTRING (the text in triple quotes, right under the def line)
   -> this becomes the tool DESCRIPTION.
   The model reads this text to decide when to use the tool.

So the docstring is not a comment for humans only. The model really reads it.
"""

from langchain_core.tools import tool


@tool
def add(a: float, b: float) -> float:
    """Add two numbers together. Use this for any addition."""
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """Subtract number b from number a. Use this for any subtraction."""
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers. Use this for any multiplication."""
    return a * b


@tool
def divide(a: float, b: float) -> str:
    """Divide number a by number b. Use this for any division."""
    if b == 0:
        return "Error: cannot divide by zero."

    return str(a / b)


@tool
def percent_of(percent: float, number: float) -> float:
    """Calculate a percentage of a number.
    Use this for questions like 'what is 15 percent of 200' or 'give me 20% discount on 500'.
    Here percent=15 and number=200, and the answer is 30."""
    return (percent / 100) * number
