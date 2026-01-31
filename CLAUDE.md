# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Exchequer is a full-stack financial management application with YNAB (You Need A Budget) integration. It enables users to manage budgets, envelopes, accounts, and transactions.

## Common Commands

### Development Setup
```bash
bash init-dev.sh          # Initialize dev environment (creates .env, storage, JWT keys)
bash run.sh               # Start Docker containers (PostgreSQL, etc.)
```

### Python API (in python-api/)
```bash
poetry install                              # Install dependencies
poetry run alembic upgrade head             # Apply database migrations
bash dev.sh                                 # Start uvicorn on :8040 with auto-reload
```

### Web App (in web-app/)
```bash
npm install               # Install dependencies
npm run dev               # Start Nuxt dev server on :3040
```

### Testing
```bash
cd python-api
poetry run pytest                           # Run all tests
poetry run pytest tests/test_users.py       # Run specific test file
poetry run pytest -x -v                     # Stop on first failure, verbose
bash run-tests.sh                           # Run tests with coverage report
```

### Linting
```bash
cd python-api
poetry run pyright                          # Type checking
poetry run ruff check python_api/           # Fast linting
```

### Database Migrations
```bash
cd python-api
poetry run alembic revision --autogenerate -m "message"   # Create migration
poetry run alembic upgrade head                           # Apply migrations
poetry run alembic downgrade -1                           # Rollback one version
```

**Important**: When editing `python_api/db/models/models.py`, always create a corresponding Alembic migration.

## Architecture

### Backend (python-api/)

**Layered architecture**:
- `app_routers/` - FastAPI route handlers (user-facing API endpoints)
- `routers/` - Admin-only routes
- `repositories/` - Data access layer with SQLAlchemy queries
- `models/` - Pydantic request/response models
- `db/models/` - SQLAlchemy ORM models
- `integrations/` - External service connectors (YNAB)
- `services/` - Business logic

**Key patterns**:
- All Pydantic models inherit from `CamelModel` (in `models/__init__.py`) for automatic camelCase JSON serialization
- Repository base class in `repositories/__init__.py` provides caching decorators and sorting utilities
- Dependencies are injected via FastAPI's `Depends()` in `dependencies.py`
- Authentication uses RS256 JWT tokens with refresh token rotation

### Frontend (web-app/)

**Nuxt 3 with Vue 3**:
- `pages/` - File-based routing
- `components/ui/` - shadcn-nuxt components (Tailwind CSS based)
- `store/auth.js` - Pinia auth store
- `plugins/api.ts` - API client with Bearer token auth

**API proxy**: Frontend `/api/*` routes proxy to backend on `:8040` (configured in nuxt.config.js)

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, Celery + Redis
- **Frontend**: Nuxt 3, Vue 3, Tailwind CSS, shadcn-nuxt, Pinia
- **Auth**: JWT (RS256), OAuth2 (Apple, Google SSO)
- **Integrations**: YNAB API, Stripe, Sentry
