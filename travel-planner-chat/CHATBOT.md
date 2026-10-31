# One agent, three tools

The right-side Trip chat panel can open and close. Sign in first.

Try: “Create a 3-day Jaipur trip for 2 people, budget ₹20,000.”
Then: “Change the Jaipur budget to ₹25,000.”
Then: “Delete the Jaipur trip.”

## Setup

Install the updated backend requirements with Python 3.12 or later.
Sign in locally with the AWS CLI. Copy `backend/.env.example` to `backend/.env`
to choose the AWS region and Bedrock model.
The server loads this file on startup. Restart the backend after editing it.
AWS credentials come from the local AWS profile or an EC2 instance role.
Never put AWS credentials in frontend code or commit them.
Model calls use Amazon Bedrock and may incur AWS charges. No OpenAI key is used.

## Follow the flow

1. `frontend/src/chat.js` sends the message to `POST /api/chat` with the login token.
2. `backend/chat_handlers.py` checks the login and message format.
3. It reads the user's saved trips and creates tools bound to that user's token.
4. `backend/chat_graph.py` runs one LangGraph agent.
5. The model answers or chooses one tool.
6. `backend/trip_tools.py` runs the chosen function through the existing trip API.
7. LangGraph passes the tool result back to the same agent for a short reply.
8. The screen refreshes the saved trips.

```text
message → agent → tool → same agent → reply
             └──────────────────────→ reply (when no tool is needed)
```

## Exactly three tools

Each function has its own `@tool` decorator and a short description.

| Tool | Purpose | Existing trip endpoint |
| --- | --- | --- |
| create_trip | Save a new plan | POST /api/trips |
| update_trip | Change supplied fields, keep other fields | GET then PUT /api/trips/{id} |
| delete_trip | Remove the requested trip | DELETE /api/trips/{id} |

The tool factory keeps the login token out of tool arguments and model messages.
The agent cannot choose a different API address or another user's token.
Trip endpoints still check ownership and validate all saved fields.
Reading saved trips for context is ordinary server code, not a fourth tool.
The agent sees summaries of up to 50 recently edited trips; ask by title when needed.

## Chat contract

POST `/api/chat` requires the same Bearer token as trip endpoints.

```json
{"message":"Change the Jaipur budget to 25000","history":[]}
```

Success: `200` with `{"reply":"..."}`. Invalid input: `400`.
Missing/invalid login: `401`. Wrong method: `405`. Unavailable AI/settings: `503`.
The existing 100 KB body and origin checks also apply.
Message length: 1–2000 characters. History: at most 12 user/assistant messages,
each 1–8000 characters. System messages and tool calls cannot be supplied by clients.

## Classroom limits

Chat history lives in the current browser page and clears on logout or refresh.
Closing the panel keeps the conversation. Saved trips remain in SQLite.
Suggestions and budgets are estimates, not live prices or bookings.
The agent asks for missing trip details and ambiguous targets.
No automatic retry runs after a model failure. The screen refreshes trips even on
errors because an action may have succeeded before the final reply failed.
Check saved trips before repeating a request after a failure.

The graph has a short step limit; model calls have timeouts and no automatic retries.
This is a local teaching app, not a production service.

## Repeat the transport check without paid model calls

With Postman CLI installed, start `postman simulation run postman/simulations/chat.sim.yaml --port 4519 --no-history`.
In another terminal run `backend/.venv/bin/python scripts/check_chat_transport.py`.
This uses fake credentials against a local Bedrock-shaped stand-in, with the real
SDK, LangGraph, HTTP trip endpoints and disposable SQLite database. It checks all
three operations and throttling. It does not test natural-language understanding.
The stand-in was built from the SDK's Converse request/response shapes; no owning
team mock was available in this local project. It is never an application fallback.

Framework references: [LangGraph quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
and [tool decorators](https://docs.langchain.com/oss/python/langchain/tools).
