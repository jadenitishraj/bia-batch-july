# Travel Planner Chat — classroom CRUD starter

A fresh single-user app for manually creating, viewing, editing and deleting trip
plans. Day headings and paragraphs are plain text. No chatbot or AI integration.

## Two folders

- `frontend/`: Vite with HTML, CSS and JavaScript. React is not required for this
  first CRUD lesson.
- `backend/`: Python standard-library HTTP API and SQLite storage.

## Start the backend

Python 3.9 or later, no Python packages to install:

```sh
cd travel-planner-chat/backend
python3 app.py
```

API: http://127.0.0.1:8003/api/trips. SQLite is created at
`backend/data/travel_planner.db` and is ignored by Git.

## Start the frontend

Node.js 20 or later, in a separate terminal:

```sh
cd travel-planner-chat/frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5175/. Vite forwards `/api` requests to the Python backend.
Stop each server with Ctrl+C. Backend port/database options:
`python3 app.py --port 8004 --database /path/to/demo.db`.
If changing the backend port, update the Vite proxy too.

## Read the code

1. `frontend/index.html`: page and forms.
2. `frontend/src/main.js`: browser interactions and HTTP calls.
3. `frontend/src/style.css`: responsive layout.
4. `backend/app.py`: HTTP routes and errors.
5. `backend/validation.py`: input limits.
6. `backend/database.py`: schema and parameterized SQLite queries.

## API contract

JSON errors have an `error` message. Create/update require all six fields:

```json
{"title":"Singapore escape","destination":"Singapore","days":4,"travelers":2,"budget":85000,"plan":"Day 1 — Arrive\nRelax.\n\nDay 2 — Explore\nVisit the gardens."}
```

| Method | Path | Result |
| --- | --- | --- |
| GET | `/api/trips` | 200, all trips, newest edits first |
| POST | `/api/trips` | 201, created trip |
| GET | `/api/trips/{id}` | 200, trip or 404 |
| PUT | `/api/trips/{id}` | 200, replaced trip or 404 |
| DELETE | `/api/trips/{id}` | 200, deleted confirmation or 404 |

Title/destination: nonempty text, max 100 characters. Plan: nonempty, max 20,000
characters. Days: integer 1–365; travelers: integer 1–100; budget: whole rupees
0–100,000,000. Unknown fields and invalid payloads: 400. Unsupported methods: 405.
Storage unavailable: 503. JSON bodies max 100 KB. Cross-origin mutations: 403.

## Verify

```sh
cd travel-planner-chat/backend
python3 -m unittest discover -s tests -v
```

```sh
cd travel-planner-chat/frontend
npm ci
npm run build
```

HTTP tests use temporary databases. This app deliberately has no login and binds
to loopback only: it is a local classroom starter, not a public multi-user service.
No cloud resources, credentials, photos or existing app code are required.
