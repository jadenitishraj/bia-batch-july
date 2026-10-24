# Travel Planner Chat — development rules

## Product and scope

- Build the classroom app incrementally. Implement only the requested lesson.
- Keep `frontend/` and `backend/` separate. Frontend uses Vite; backend uses Python
  and SQLite. Do not add a chatbot, AI provider, login or cloud service unless asked.
- Keep the original `travel-planner/` app and unrelated work untouched.
- The current app is single-user and local-only. Do not imply production readiness.

## Readability and file size

- Every handwritten source, test and project instruction file must be **150 lines
  or fewer**, including comments and blank lines. Run the size check before delivery.
- Split oversized files by meaningful responsibility, not arbitrary line ranges.
- Do not minify code, cram statements onto one line, remove useful comments or use
  meaningless wrapper files to satisfy the limit.
- Use clear names, normal formatting, small functions and explicit inputs/outputs.
- Keep related code together. Avoid both giant modules and needless abstraction.
- Generated dependency lockfiles, dependencies, build output and SQLite files are
  machine-managed artifacts, not handwritten code. Never manually shorten them.

## Frontend

- Separate HTTP requests, rendering and interaction coordination when responsibilities
  grow. Reuse helpers rather than copying logic.
- Render user text with safe DOM APIs, never unsanitized HTML.
- Use semantic HTML, associated labels, keyboard controls, visible focus and accessible
  dialogs. Provide clear loading, empty, success, validation and error states.
- Keep layout responsive; review the affected desktop and mobile screens.
- Prevent repeated submissions while requests run. Keep entered values after failures.
- Do not put database access, secrets or authorization decisions in browser code.
- Add dependencies only when they solve a real requirement. Keep the lockfile in Git.

## Backend and database

- Keep request handling, validation and persistence in cohesive modules.
- Validate types, ranges, lengths and required fields on the server. Reject malformed
  requests with useful, consistent status codes and safe JSON errors.
- Use parameterized SQL and transactions. Close connections promptly.
- Preserve existing data. Schema changes need an explicit migration plan and tests.
- Never log secrets or return tracebacks/database internals to clients.
- Keep request-size limits, loopback binding and browser-origin checks intact.
- Do not disable security checks to make an integration pass; test the valid path.
- If authentication is added later, enforce ownership on every protected server action.

## Tests and verification

- Maintain separate automated frontend and backend test suites.
- Every behavior change needs meaningful tests. Fixes need a regression test.
- Test success, invalid input, missing records, failure handling and persistence.
- Exercise real HTTP and temporary SQLite databases for API integration tests.
- Never use classroom/user data for destructive tests. Isolate disposable test data.
- For frontend changes, verify actual browser interactions and relevant keyboard,
  responsive, empty and error states. API tests alone do not establish UI correctness.
- Run ESLint for frontend source, configuration and tests. Run Ruff for Python
  source, scripts and tests. Fix findings; do not silence rules without justification.
- Run both linters, frontend tests, backend tests, file-size check and frontend build
  before declaring completion.
- Do not weaken tests or checks to hide failures. State exactly what is unverified.

## Git and delivery

- Use a focused `codex/` branch and review the diff before committing.
- Keep secrets, runtime databases, uploads, caches and build output out of Git.
- Update the relevant README/API contract when behavior or setup changes.
- Push and open/update a PR only within the user's authorization. Never merge or
  deploy without authorization. Preserve unrelated changes.
- Report implemented, tested, pushed, merged and deployed states separately.

## Classroom checks

From this folder:

```sh
python3 scripts/check_file_sizes.py
python3 -m unittest discover -s backend/tests -v
npm --prefix frontend ci
backend/.venv/bin/ruff check backend scripts --config backend/ruff.toml
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
```
