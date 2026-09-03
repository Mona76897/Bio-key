# --- BioKey V2 backend_service ---
# Build from the backend_service/ directory:
#   docker build -t biokey-backend .
# Run:
#   docker run -p 8000:8000 biokey-backend

FROM python:3.11-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr less
# (useful so `docker logs` shows output immediately, not batched)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first, separately from app code, so Docker's layer
# cache only re-installs packages when requirements.txt actually changes —
# not on every code edit. This matters once you're rebuilding often in CI.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual application code
COPY app ./app

# Run as a non-root user — a small but real security improvement over the
# container's default root user, worth having even in a student project.
RUN useradd --create-home biokey && chown -R biokey:biokey /app
USER biokey

EXPOSE 8000

# Basic container-level health check: fails the container health status if
# /health stops responding, without needing curl/wget in the slim image.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

# No --reload here (that's a dev-only flag) — this runs the way a deployed
# container actually should.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
