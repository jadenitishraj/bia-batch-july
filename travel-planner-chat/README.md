# Travel Planner Chat — classroom CRUD starter

A fresh, single-user web app: **Python + SQLite + plain HTML/CSS/JavaScript**.
Manually create, view, edit, and delete trip plans. The itinerary is plain text,
with day headings and paragraphs. There is no chatbot, AI call, RAG, login,
cloud database, or copied Travel Planner implementation.

## Run

Requires Python 3.9 or later. No packages to install.

```sh
cd travel-planner-chat
python3 app.py
```

Open http://127.0.0.1:5175/. The database is created automatically at
`data/travel_planner.db` and is ignored by Git. Start with an empty trip list.
Stop with Ctrl+C. Optional: `python3 app.py --port 5176 --database /path/to/demo.db`.

## Read the code in this order

1. `index.html` — page, create/edit form, delete confirmation.
2. `app.js` — browser interactions and HTTP calls.
3. `app.py` — HTTP routes, validation errors, static files.
4. `validation.py` — required fields and input limits.
5. `database.py` — table creation and parameterized SQLite queries.

## API contract

All payloads and responses are JSON. Errors return `{"error": "message"}`.

| Method | Path | Result |
| --- | --- | --- |
| GET | `/api/trips` | 200, all trips (newest edits first) |
| POST | `/api/trips` | 201, created trip |
| GET | `/api/trips/{id}` | 200, trip or 404 |
| PUT | `/api/trips/{id}` | 200, replaced trip or 404 |
| DELETE | `/api/trips/{id}` | 200, `{"deleted": true}` or 404 |

Create and update require all six fields:

```json
{"title":"Singapore escape","destination":"Singapore","days":4,"travelers":2,"budget":85000,"plan":"Day 1 — Arrive\nSettle into the hotel.\n\nDay 2 — Explore\nVisit the gardens."}
```

Title/destination: nonempty text up to 100 characters. Plan: nonempty text up to
20,000 characters. Days: integer 1–365. Travelers: integer 1–100. Budget: whole
rupees 0–100,000,000. Unknown fields are rejected. Invalid inputs return 400;
unsupported collection/item methods return 405; storage errors return 503.
Requests are limited to 100 KB. Browser cross-origin mutations return 403.

## Verify

```sh
python3 -m unittest discover -s tests -v
```

Tests use temporary databases and actual local HTTP requests, never classroom data.
The local server binds only to loopback. This deliberately has no authentication:
it is a local classroom starter, not a publicly deployable multi-user service.
SQLite data stays on this machine. Do not expose this server to a network.
