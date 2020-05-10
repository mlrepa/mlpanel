FROM python:3.7-slim

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

CMD gunicorn --bind 0.0.0.0:1234 --workers $AUTH_SERVER_GUNICORN_WORKERS home.auth.src.app:app