FROM python:3.9-alpine
ENV PYTHONUNBUFFERED 1

WORKDIR /code
RUN apk add --no-cache build-base

COPY .. .

RUN pip install -r requirements.txt
RUN pip cache purge

CMD /bin/sh /code/start.sh