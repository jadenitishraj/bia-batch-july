# Travel Planner Chat — development rules

## Product and scope

- Build the classroom app incrementally. Implement only the requested lesson.
- Keep `frontend/` and `backend/` separate. Frontend uses Vite; backend uses Python
  and SQLite. Do not add a chatbot, AI provider, login or cloud service unless asked.
- Keep the original `travel-planner/` app and unrelated work untouched.
- The app uses local JWT login and per-account trips. Do not imply production readiness.

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
- Preserve the recommended and project ESLint rules for correctness, unsafe language
  features and maintainability. Rule changes require rationale and config tests.

## Backend and database

- Keep request handling, validation and persistence in cohesive modules.
- Validate types, ranges, lengths and required fields on the server. Reject malformed
  requests with useful, consistent status codes and safe JSON errors.
- Use parameterized SQL and transactions. Close connections promptly.
- Preserve existing data. Schema changes need an explicit migration plan and tests.
- Never log secrets or return tracebacks/database internals to clients.
- Keep request-size limits, loopback binding and browser-origin checks intact.
- Do not disable security checks to make an integration pass; test the valid path.
- Require a verified JWT and enforce ownership on every protected trip operation.

## Tests and verification

- Maintain separate automated frontend and backend test suites.
- Require at least 90% coverage separately for frontend and backend. Frontend must
  reach 90% statements, branches, functions and lines. Python coverage.py supports
  statements/lines and branches; enforce each separately and disclose that it does
  not report function coverage. Include all executable application source, including
  untested files. Exclude only tests, dependencies and generated artifacts.
- Never weaken thresholds or omit difficult application code to make coverage pass.
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
- The PR must show passing GitHub Actions Lint, Tests and Build checks.
  Local passing results do not substitute for the remote PR checks.
- Keep secrets, runtime databases, uploads, caches and build output out of Git.
- Update the relevant README/API contract when behavior or setup changes.
- Push and open/update a PR only within the user's authorization. Never merge or
  deploy without authorization. Preserve unrelated changes.
- Report implemented, tested, pushed, merged and deployed states separately.

## Classroom checks

From this folder:

```sh
python3 scripts/check_file_sizes.py
(cd backend && .venv/bin/python -m coverage run -m unittest discover -s tests -v)
(cd backend && .venv/bin/python -m coverage report && .venv/bin/python -m coverage json)
(cd backend && .venv/bin/python check_coverage.py)
npm --prefix frontend ci
backend/.venv/bin/ruff check backend scripts --config backend/ruff.toml
npm --prefix frontend run lint
npm --prefix frontend run test:coverage
npm --prefix frontend run build
```
