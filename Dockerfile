FROM python:3.12-slim-bookworm

# env
ENV POETRY_HOME=/opt/poetry

# setup poetry
RUN python3 -m venv $POETRY_HOME
RUN $POETRY_HOME/bin/pip install poetry
# add poetry to path
ENV PATH=$POETRY_HOME/bin:$PATH

WORKDIR /app
COPY . /app
RUN poetry install --only=main --no-root
