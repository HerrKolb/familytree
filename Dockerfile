FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Statische Dateien einsammeln (WhiteNoise liefert sie aus)
RUN DJANGO_SECRET_KEY=build-only DB_ENGINE=sqlite python manage.py collectstatic --noinput

# Eigener Benutzer mit UID 1000 (= rainer auf dem Server), damit der
# eingebundene Fotoordner beschreibbar ist
RUN useradd --uid 1000 --create-home app \
    && mkdir -p /app/media \
    && chown -R app:app /app/media \
    && chmod +x /app/docker-entrypoint.sh
USER app

EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "familytree.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-"]
