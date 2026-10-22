FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app backend ./backend
RUN mkdir -p /data && chown app:app /data \
    && DJANGO_SECRET_KEY=build-only-secret-key-with-more-than-fifty-characters \
       DJANGO_ALLOWED_HOSTS=localhost \
       python backend/manage.py collectstatic --noinput

USER app

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--chdir", "backend", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
