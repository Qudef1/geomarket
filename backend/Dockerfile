FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY backend/app ./backend/app
RUN pip install --no-cache-dir .
COPY backend/alembic.ini ./backend/alembic.ini
COPY backend/migrations ./backend/migrations
CMD ["sh", "-c", "alembic -c backend/alembic.ini upgrade head && exec uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000"]
