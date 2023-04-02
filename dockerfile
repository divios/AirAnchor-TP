
FROM python:3.6.9
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt

RUN apt update -y

RUN mkdir -p /var/log/sawtooth

COPY ./processor /code/processor
COPY ./packaging /code/packaging
COPY ./setup.py  /code/setup.py

RUN python3 setup.py clean --all \
    && python3 setup.py build \
    && python3 setup.py install \
    && cp -r ./processor /usr/local/lib/python3.6/site-packages/sawtooth_location_key