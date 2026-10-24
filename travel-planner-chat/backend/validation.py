"""Validate complete create/update payloads before writing to SQLite."""
from database import FIELDS


def validate_trip(value):
    if not isinstance(value, dict) or set(value) != set(FIELDS):
        raise ValueError('Provide title, destination, days, travelers, budget, and plan.')
    cleaned = {}
    for field, maximum in [('title', 100), ('destination', 100), ('plan', 20000)]:
        text = value[field]
        if not isinstance(text, str) or not text.strip() or len(text.strip()) > maximum:
            raise ValueError(f'{field.capitalize()} must contain 1–{maximum} characters.')
        cleaned[field] = text.strip()
    for field, maximum in [('days', 365), ('travelers', 100), ('budget', 100000000)]:
        number = value[field]
        minimum = 0 if field == 'budget' else 1
        if type(number) is not int or not minimum <= number <= maximum:
            raise ValueError(f'{field.capitalize()} must be a whole number from {minimum} to {maximum}.')
        cleaned[field] = number
    return cleaned
