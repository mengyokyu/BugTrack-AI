FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn
COPY app app
COPY migrations migrations
COPY templates templates
COPY static static
COPY run.py .
COPY scripts/entrypoint.sh /usr/local/bin/bugtrack-entrypoint
RUN chmod 0555 /usr/local/bin/bugtrack-entrypoint && chown -R app:app /app
USER app
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health/live')"
ENTRYPOINT ["bugtrack-entrypoint"]
