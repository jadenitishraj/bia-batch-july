# Classroom JWT authentication

## The flow

1. Register or log in with an email and password.
2. The Python backend returns `access_token`, `token_type`, `expires_in` and `user`.
3. The frontend sends `Authorization: Bearer <access_token>` on trip requests.
4. The server verifies the signature, expiry, issuer, audience and existing account.
5. SQLite queries filter by that account's ID, never a browser-supplied owner ID.

The frontend keeps the JWT in memory, not localStorage. Refreshing the page or
logging out forgets it. A copied JWT stays valid until its one-hour expiry:
logout here is client-side only. There are no refresh tokens or password-reset flows.

## Public endpoints

`POST /api/auth/register` creates an account and returns a JWT (201).
`POST /api/auth/login` checks credentials and returns a JWT (200).
Both accept exactly `email` and `password`, as JSON. Emails are normalized to lowercase.
Passwords require 8–128 characters. Registration does not verify email ownership.

```json
{"email":"learner@example.com","password":"choose-your-own-password"}
```

Duplicate registration: 409. Invalid credentials: 401. Invalid fields: 400.
Auth requests share a per-IP limit of ten attempts per minute (429 when exceeded).
The local in-memory limit resets when the process restarts.

## Postman: get a token, then read your database records

1. Send POST to `http://127.0.0.1:8003/api/auth/register` with the JSON above.
2. For an existing account, use `/api/auth/login` with the same credentials.
3. Copy `access_token` from the response.
4. Send GET to `http://127.0.0.1:8003/api/trips`.
5. Choose Authorization → Bearer Token and paste the token, without quotes.

You initially receive `[]`. Create a trip with POST `/api/trips`, using the
README payload and the same Bearer token. GET will now return your saved trip.
POST, PUT and DELETE require the same token. Another account cannot list, read,
update or delete your trips: another owner's item URL returns 404.

Missing, expired, forged or otherwise invalid JWTs return 401. Do not put tokens
in URLs. The token identifies an account; it contains no password or trip details.
Responses are JSON with Cache-Control: no-store. Existing trip validation and
cross-origin write protection remain enabled.

## Passwords and signing keys

Passwords use PBKDF2-HMAC-SHA256 with 600,000 iterations and a random salt.
Only hashes and salts are stored. The backend uses PyJWT with a fixed HS256
algorithm; the caller cannot choose the verification algorithm.

At startup, a random local signing key is created beside the SQLite file as
`travel_planner.jwt-key`. File permissions are 0600 and the file is excluded from
Git. Preserve it across restarts if existing tokens should remain valid.
Alternatively set `JWT_SECRET` to at least 32 random bytes in the backend's
ignored `.env` file or the server environment. Never put it in frontend code.

## Existing SQLite data

Startup adds `users`, an `owner_id` column and its index without deleting trips.
Older rows have no owner. They remain in SQLite but are hidden from every account.
They are not silently claimed by the first person who registers. Associating
legacy trips with an account requires an explicit, reviewed data migration.
Back up a real database before running any schema update on it.

## Scope

This is a local authentication lesson. It does not add a cloud identity provider,
Supabase, a chatbot, production hosting, email verification or account recovery.
Use HTTPS and a reviewed deployment/authentication configuration before public use.
