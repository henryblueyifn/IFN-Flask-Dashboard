FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7

ENV LISTEN_PORT=9000
EXPOSE 9000

COPY /app /app