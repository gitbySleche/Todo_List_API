# Todo List API

A RESTful API for managing personal to-do lists, built with Flask and SQLite. Each user registers their own account and can only view, create, update, and delete their own to-do items.

Project built from the specs of https://roadmap.sh/projects/todo-list-api to practice user authentication, relational schema design, and RESTful API conventions on top of prior CRUD-only projects.

## Features

- User registration and login with hashed passwords (Argon2)
- Token-based authentication (`Authorization: Bearer <token>`), with expiring tokens
- Full CRUD for to-do items, scoped to the authenticated user
- Ownership enforcement — users can only modify or delete their own items (403 Forbidden otherwise)
- Pagination on the to-do list endpoint
- Request body validation — missing required fields return a clean 400 instead of crashing
- SQLite foreign key constraints enforced between users, tokens, and todos

## Tech Stack

- **Language**: Python
- **Framework**: Flask
- **Database**: SQLite3
- **Password hashing**: Argon2 (`argon2-cffi`)
- **Token generation**: `secrets.token_urlsafe()`

## Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE tokens (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE todo (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

Foreign key constraints are enforced per-connection via `PRAGMA foreign_keys = ON`.

## Setup

1. Clone the repository and navigate into it.
2. Install dependencies:
   ```bash
   pip install flask argon2-cffi
   ```
3. Run the app:
   ```bash
   python app.py
   ```
   The API will be available at `http://localhost:5000`.

## API Endpoints

### Register

```
POST /register
```

**Body** (all fields required):
```json
{
  "name": "John Doe",
  "email": "john@gmail.com",
  "password": "password"
}
```

Email must end in `@gmail.com` or `@hotmail.com`.

**Response:** `201 Created`
```json
{ "token": "kJ8x_2mP9qR..." }
```

**Errors:** `400` for missing fields, invalid email format, or an email already registered.

### Login

```
POST /login
```

**Body** (all fields required):
```json
{
  "email": "john@gmail.com",
  "password": "password"
}
```

**Response:** `200 OK`
```json
{ "token": "kJ8x_2mP9qR..." }
```

**Errors:** `400` for missing fields, invalid email format, email not found, or incorrect password.

Note: logging in issues a brand-new token without invalidating previous ones — a user can hold multiple valid tokens at once (e.g. one from registration, one from a later login).

### Create a To-Do

```
POST /todos
```

**Headers:** `Authorization: Bearer <token>`

**Body** (both fields required):
```json
{
  "title": "Buy groceries",
  "description": "Buy milk, eggs, and bread"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Buy milk, eggs, and bread"
}
```

**Errors:** `400` for missing fields, `401` for a missing/invalid/expired token.

### Update a To-Do

```
PUT /todos/<id>
```

**Headers:** `Authorization: Bearer <token>`

**Body** (both fields required):
```json
{
  "title": "Buy groceries",
  "description": "Buy milk, eggs, bread, and cheese"
}
```

**Response:** `200 OK` — updated item.

**Errors:** `400` for missing fields or a nonexistent item, `401` for a missing/invalid/expired token, `403` if the token doesn't belong to the item's creator.

### Delete a To-Do

```
DELETE /todos/<id>
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `204 No Content`

**Errors:** `400` for a nonexistent item, `401` for a missing/invalid/expired token, `403` if the token doesn't belong to the item's creator.

### Get To-Do Items (paginated)

```
GET /todos?page=1&limit=10
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "data": [
    { "id": 1, "title": "Buy groceries", "description": "Buy milk, eggs, bread" },
    { "id": 2, "title": "Pay bills", "description": "Pay electricity and water bills" }
  ],
  "page": 1,
  "limit": 10,
  "total": 2
}
```

`page` and `limit` both default to `1` and `10` respectively if omitted.

## Authentication Notes

- Tokens are opaque random strings (`secrets.token_urlsafe()`), stored server-side in the `tokens` table alongside the owning `user_id` and an expiry timestamp (1 hour from issue).
- Sent as `Authorization: Bearer <token>` on every protected route.
- Every protected route checks that the submitted token exists **and** hasn't expired before proceeding.
- `user_id` for any write operation is always derived from the verified token — never trusted from client-supplied request data.
- Ownership checks on update/delete compare the token's `user_id` against the to-do item's stored `user_id`, returning 403 on mismatch.
- Multiple valid tokens per user are currently allowed at once (no single-session enforcement).

## What This Project Practices

- Password hashing vs. encryption, and why passwords are never stored reversibly
- Token-based auth as a stateless alternative to session cookies, including expiry
- Relational schema design with foreign keys across users/tokens/todos
- Authorization vs. authentication (401 vs. 403)
- SQL pagination via `LIMIT`/`OFFSET`
- Transaction handling and connection cleanup with SQLite
- Defensive input validation against missing/malformed request bodies

## Possible Next Steps

- Refresh token mechanism
- Rate limiting
- Filtering/sorting on the to-do list endpoint
- Unit tests
- Scheduled cleanup of expired tokens
- Optional: single-session enforcement (invalidate old tokens on new login)
