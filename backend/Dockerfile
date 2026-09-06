# Vision API. One image for every host we target: Hugging Face Spaces, Render
# and Fly all run it unchanged, differing only in which port they hand us.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Hugging Face Spaces runs the container as uid 1000, so the files have to
# belong to that user or nothing in the image is readable at runtime.
RUN useradd --create-home --uid 1000 vision

WORKDIR /app

# Requirements first: this layer is cached until the dependency list itself
# changes, so an ordinary code edit does not reinstall pandas and numpy.
COPY --chown=vision:vision requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=vision:vision app ./app

USER vision

# 7860 is the Hugging Face default. Render and Fly inject their own PORT, which
# the command below prefers when present.
ENV PORT=7860
EXPOSE 7860

# One worker on purpose. The TTL cache is per-process, so a second worker would
# double the upstream calls and halve the hit rate for no throughput we need.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
