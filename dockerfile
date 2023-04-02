
FROM python:3.9.6
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt

RUN apt update -y && \
    pip install sawtooth-sdk && \ 
    pip install --no-cache-dir -r /code/requirements.txt

ENV PATH=$PATH:/code

COPY ./processor /code/app
COPY ./packaging /code/packaging
COPY ./setup.py  /code/setup.py

RUN python3 setup.py clean --all \
    && python3 setup.py build \
    && python3 setup.py install --old-and-unmanageable