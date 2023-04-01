
FROM python:latest
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt

RUN pip install sawtooth-sdk && \ 
    pip install --no-cache-dir -r /code/requirements.txt

COPY ./processor /code/app