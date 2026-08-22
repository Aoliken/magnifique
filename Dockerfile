# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the application's declared dependencies plus the production WSGI server.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn==23.0.0

# Copy only runtime sources so local .env files and development artifacts stay out of the image.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini run.py ./

RUN useradd --create-home --uid 10001 appuser \
    && chown --recursive appuser:appuser /app
USER appuser

EXPOSE 5000

# Development override:
# docker run --rm -p 5000:5000 --env-file .env magnifique \
#   flask --app run:app run --host=0.0.0.0 --port=5000 --debug
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
