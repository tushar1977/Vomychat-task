FROM python:3.8-slim-buster

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt && \
  rm -f core/store.sqlite3 && \
  FLASK_APP=myapp flask db upgrade -d core/migrations

CMD ["bash", "run.sh"]
