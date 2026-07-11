# Container image for the API. Under Option 1 the SQLite database file is committed to
# the repo (data/consensus.db) and copied into the image, so the deployed service serves
# that baked-in snapshot read-only. To refresh the data you run ingestion locally, commit
# the updated database, and redeploy.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements.txt changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application (including data/consensus.db, per .dockerignore).
COPY . .

EXPOSE 8000

# Render (and most hosts) provide $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
