"""Exactly three tools. Each calls the same trip API as the screen."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from langchain_core.tools import ToolException, tool

FIELDS = ('title', 'destination', 'days', 'travelers', 'budget', 'plan')


def trip_request(base_url, token, method='GET', trip_id=None, values=None):
    """The address and login token come from the server, never from the model."""
    path = '/api/trips' if trip_id is None else f'/api/trips/{trip_id}'
    body = json.dumps(values).encode() if values is not None else None
    request = Request(base_url + path, data=body, method=method, headers={
        'Authorization': token, 'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=10) as response:
            return json.load(response)
    except HTTPError as error:
        with error:
            message = json.load(error).get('error', 'Trip request failed.')
        raise ToolException(message) from None
    except (URLError, TimeoutError):
        raise ToolException('Trip service unavailable. Check your trips before retrying.') from None


def make_trip_tools(base_url, token):
    """Give each request its own tools, bound to the signed-in account."""
    @tool
    def create_trip(title: str, destination: str, days: int,
                    travelers: int, budget: int, plan: str) -> dict:
        """Create and save a trip. Budget is whole rupees; plan is day-by-day text."""
        values = dict(title=title, destination=destination, days=days,
                      travelers=travelers, budget=budget, plan=plan)
        return trip_request(base_url, token, 'POST', values=values)

    @tool
    def update_trip(trip_id: int, title: str | None = None,
                    destination: str | None = None, days: int | None = None,
                    travelers: int | None = None, budget: int | None = None,
                    plan: str | None = None) -> dict:
        """Update one saved trip by ID. Supply only the fields the user wants changed."""
        current = trip_request(base_url, token, trip_id=trip_id)
        changes = dict(title=title, destination=destination, days=days,
                       travelers=travelers, budget=budget, plan=plan)
        values = {field: current[field] for field in FIELDS}
        for field, value in changes.items():
            if value is not None:
                values[field] = value
        return trip_request(base_url, token, 'PUT', trip_id, values)

    @tool
    def delete_trip(trip_id: int) -> dict:
        """Delete one saved trip by ID when the user explicitly asks to delete it."""
        return trip_request(base_url, token, 'DELETE', trip_id)

    return [create_trip, update_trip, delete_trip]
