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

Node.js 22.13+ (22.x) or 24.x, in a separate terminal:

```sh
cd travel-planner-chat/frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5175/. Vite forwards `/api` requests to the Python backend.
Stop each server with Ctrl+C. Keep the backend port and Vite proxy consistent.

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
npm run lint
npm run test:coverage
npm run build
```

HTTP tests use temporary databases. This app deliberately has no login and binds
to loopback only: it is a local classroom starter, not a public multi-user service.
No cloud resources, credentials, photos or existing app code are required.

Frontend tests exercise real DOM events and rendering, with simulated HTTP responses
for success and failure states. They do not replace real Python/SQLite integration
tests or desktop/mobile browser review. jsdom provides the DOM; dialog show/close
methods are shimmed because native modal behavior requires an actual browser.

## Python linting

Runtime still uses only Python's standard library. Ruff is a development tool.
From `travel-planner-chat/`:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
backend/.venv/bin/ruff check backend scripts --config backend/ruff.toml
python3 scripts/check_file_sizes.py
```

ESLint checks frontend source/config/tests. Ruff checks Python imports, errors,
common bugs and supported syntax. Tests remain separate checks, not replaced by lint.

## GitHub PR checks

The `Travel Planner Chat CI` workflow runs on matching pull requests to `main`,
relevant main-branch pushes, and manual dispatch. Its three visible checks are:

- **Lint**: frontend ESLint, backend Ruff, and the 150-line handwritten-file limit.
- **Tests**: automated frontend and backend test suites using disposable databases.
- **Build**: Vite's production frontend build.

The workflow has read-only repository permissions, time limits and cancellation
of superseded runs. It does not deploy or merge. Branch protection can separately
require these checks; this workflow alone does not enforce merge restrictions.

## ESLint policy

`eslint:recommended` supplies the baseline error checks. Explicit project rules add
strict comparisons, braces, callback returns, promise-executor checks, safe language
features, immutable parameters and consistent modern JavaScript. Maintainability
limits are 150 lines/file, 60 lines/function, complexity 12, nesting depth 3 and
four parameters. Source, configuration and tests use the same quality rules.

There is no universal Fortune 500 preset. These checks suit this small JavaScript
app; React/TypeScript rules should be added if those technologies are introduced.
Lint catches certain bugs and patterns, not all security or accessibility issues.

## Coverage gate

Both suites must reach **90%**, measured separately, without excluding untested
application code. Frontend V8 coverage includes every `src/**/*.js` file and gates
statements, branches, functions and lines. Run `npm run test:coverage` in frontend.

From backend, after installing `requirements-dev.txt`, run:

```sh
.venv/bin/python -m coverage run -m unittest discover -s tests -v
.venv/bin/python -m coverage report
.venv/bin/python -m coverage json
.venv/bin/python check_coverage.py
```

Python includes all backend Python modules, including untested ones, except tests
and dependencies. coverage.py reports statements/lines and branches, not function
coverage. The extra gate requires statements/lines and branches to each reach 90%.
CI enforces these coverage gates inside the Tests check. Reports stay out of Git.
