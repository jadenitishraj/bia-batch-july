"""
text_tools.py
-------------
Small helper tools that are not math and not data.

These are here to show that a tool can be ANY python function.
"""

from datetime import datetime

from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """Get today's date and the current time. Use this when the user asks about date or time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def count_words(text: str) -> str:
    """Count how many words are in a piece of text."""
    words = text.split()
    return str(len(words)) + " words"


@tool
def to_uppercase(text: str) -> str:
    """Convert a piece of text to UPPERCASE letters."""
    return text.upper()


@tool
def reverse_text(text: str) -> str:
    """Reverse a piece of text, so 'abc' becomes 'cba'."""
    return text[::-1]
