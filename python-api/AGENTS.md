# I've sold my soul to OpenAI

## Dev environment tips
- Use `poetry install` to install dependencies.
- Modify `python_api/db/models/*` when editing database schema, and `poetry run alembic revision --autogenerate -m "message"` to create migration files.
- Use `poetry run alembic upgrade head` to apply migrations.
