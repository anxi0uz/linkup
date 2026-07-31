<div align="center">

# LinkUp

**A modern professional networking backend built with FastAPI.**

LinkUp is a work-in-progress LinkedIn-style application focused on clean
module boundaries, asynchronous I/O, secure authentication, and a production-
friendly runtime foundation.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-8-DC382D?logo=redis&logoColor=white)

</div>

## Current features

- user registration with an automatically created profile;
- login with Argon2 password verification outside the event loop;
- short-lived JWT access tokens;
- opaque rotating refresh tokens stored in Redis;
- HttpOnly refresh-token cookies;
- refresh-session revocation on logout;
- authenticated current-user endpoint;
- profile lookup and partial profile updates;
- company creation and owner-managed company profiles;
- personal and company posts with ownership checks and filtering;
- async SQLAlchemy sessions and PostgreSQL migrations;
- structured development and JSON production logs;
- request IDs propagated through logs and response headers;
- complete containerized runtime with health checks.

## Stack

| Area | Technology |
| --- | --- |
| API | FastAPI |
| Runtime | Python 3.13, uv, Uvicorn |
| Validation | Pydantic and pydantic-settings |
| Database | PostgreSQL 18, async SQLAlchemy, psycopg |
| Migrations | Alembic |
| Sessions | Redis 8 |
| Authentication | JWT access tokens and rotating refresh tokens |
| Password hashing | Argon2 via pwdlib |
| Logging | structlog and ASGI request middleware |
| Containers | Podman Compose and Dockerfile |

## Architecture

LinkUp is organized as a modular monolith. Infrastructure is shared, while
business behavior lives in domain modules.

```text
src/
├── linkup/
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── middleware.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   └── logger.py
│   ├── db/
│   │   ├── base.py
│   │   ├── redis.py
│   │   └── session.py
│   ├── models/
│   │   ├── company.py
│   │   ├── post.py
│   │   ├── profile.py
│   │   └── user.py
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── dependencies.py
│   │   │   ├── exceptions.py
│   │   │   ├── refresh_session.py
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── security.py
│   │   │   └── service.py
│   │   ├── companies/
│   │   ├── posts/
│   │   └── profiles/
│   └── main.py
└── migrations/
```

The routers handle HTTP concerns, services implement use cases, models describe
persistence, and dependencies connect requests to shared infrastructure.

## Requirements

For the complete containerized setup:

- Podman;
- `podman-compose`.

For running the application directly on the host:

- Python 3.13;
- [uv](https://docs.astral.sh/uv/).

## Configuration

Create `.env` in the project root:

```env
DATABASE_URL=postgresql+psycopg://linkup:linkup@localhost:5432/linkup
REDIS_URL=redis://localhost:6379/0

JWT_SECRET=replace-with-a-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
REFRESH_COOKIE_SECURE=false

DEBUG=true
SQL_ECHO=false
```

Generate a local JWT secret with:

```bash
openssl rand -hex 32
```

`REFRESH_COOKIE_SECURE=false` is intended only for local HTTP development. Use
`true` behind HTTPS in production.

Optional Compose variables:

```env
APP_PORT=8000
POSTGRES_PORT=5432
REDIS_PORT=6379
POSTGRES_DB=linkup
POSTGRES_USER=linkup
POSTGRES_PASSWORD=linkup
```

## Run with Podman Compose

Build and start the API, PostgreSQL, and Redis:

```bash
podman-compose up -d --build
```

The application container waits for healthy infrastructure, applies migrations,
and then starts Uvicorn.

Inspect the running services and application logs:

```bash
podman-compose ps
podman-compose logs -f app
```

Open:

- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>
- health check: <http://127.0.0.1:8000/health>

Stop the stack:

```bash
podman-compose down
```

## Run locally

Install locked dependencies:

```bash
uv sync --locked
```

Start only PostgreSQL and Redis:

```bash
podman-compose up -d postgres redis
```

Apply migrations and run the development server:

```bash
uv run alembic upgrade head
uv run fastapi dev src/linkup/main.py
```

## API

All application endpoints are mounted under `/api/v1`.

### Authentication

| Method | Path | Authentication | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | No | Create a user and profile, then issue tokens |
| `POST` | `/api/v1/auth/login` | No | Authenticate and issue tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh cookie | Rotate the refresh token and issue a new access token |
| `POST` | `/api/v1/auth/logout` | Refresh cookie | Revoke the refresh session and clear the cookie |
| `GET` | `/api/v1/auth/me` | Bearer token | Return the authenticated user and profile |

The access token is returned in the JSON response and should be sent as:

```http
Authorization: Bearer <access-token>
```

The refresh token is never returned in JSON. It is stored in an HttpOnly cookie
scoped to `/api/v1/auth` and rotated whenever it is consumed.

### Profiles

| Method | Path | Authentication | Description |
| --- | --- | --- | --- |
| `PATCH` | `/api/v1/profile/me` | Bearer token | Partially update the authenticated user's profile |
| `GET` | `/api/v1/profile/{profile_id}` | Bearer token | Return a profile by user/profile UUID |

Profile updates use PATCH semantics: omitted fields remain unchanged, nullable
fields can be cleared with `null`, and `first_name` or `last_name` cannot be set
to `null`.

### Companies

| Method | Path | Authentication | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/companies` | Bearer token | Create a company owned by the current user |
| `GET` | `/api/v1/companies` | Bearer token | List companies with limit/offset pagination |
| `GET` | `/api/v1/companies/{company_id}` | Bearer token | Return a company by UUID |
| `PATCH` | `/api/v1/companies/{company_id}` | Owner | Partially update a company |
| `DELETE` | `/api/v1/companies/{company_id}` | Owner | Delete a company and its posts |

Company slugs are normalized to lowercase and must be globally unique.

### Posts

| Method | Path | Authentication | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/posts` | Bearer token | Create a personal or company post |
| `GET` | `/api/v1/posts` | Bearer token | List posts with pagination and optional author/company filters |
| `GET` | `/api/v1/posts/{post_id}` | Bearer token | Return a post by UUID |
| `PATCH` | `/api/v1/posts/{post_id}` | Author | Update post content |
| `DELETE` | `/api/v1/posts/{post_id}` | Author | Delete a post |

Passing `company_id` creates a company post and requires the current user to own
that company. Omitting it creates a personal post.

## Tests

Start the isolated test infrastructure:

```bash
podman-compose -f compose.test.yaml up -d
```

Run the integration suite:

```bash
uv run pytest
```

Tests exercise the complete ASGI application against PostgreSQL and Redis on
ports `5433` and `6380`. The test database schema and Redis state are reset for
each scenario.

## Database migrations

Create a migration after changing SQLAlchemy models:

```bash
uv run alembic revision --autogenerate -m "describe the change"
```

Review the generated migration before applying it:

```bash
uv run alembic upgrade head
```

Rollback one revision:

```bash
uv run alembic downgrade -1
```

## Logging

Every HTTP request receives an `X-Request-ID`. The same identifier is bound to
structured application logs, together with the authenticated user ID whenever
available.

- `DEBUG=true` renders human-readable development logs;
- `DEBUG=false` renders JSON suitable for log aggregation;
- SQL statement logging is controlled separately with `SQL_ECHO`;
- health-check requests are excluded from request logs.

## Roadmap

- professional connections and connection requests;
- reactions, comments, and a personalized feed;
- user and content search;
- work experience, education, and skills;
- avatar and media uploads;
- Prometheus metrics;
- Loki log aggregation and Grafana dashboards.

## Project status

LinkUp is under active development. Authentication, profiles, companies, posts,
and their integration test coverage are implemented.
