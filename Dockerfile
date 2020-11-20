FROM python:3.8

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip3 install pipenv
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN mkdir /app
WORKDIR /app
COPY ./ /app
RUN pipenv install --system --deploy --ignore-pipfile
