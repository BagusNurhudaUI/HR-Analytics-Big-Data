FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2
RUN pip install -r requirements.txt

COPY . .

