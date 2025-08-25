FROM python:3.11-slim-buster

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy only pyproject.toml and poetry.lock to leverage Docker cache
COPY pyproject.toml poetry.lock* /app/

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

COPY ./src/fastapi_langraph /app/src/fastapi_langraph

CMD ["uvicorn", "src.fastapi_langraph.main:app", "--host", "0.0.0.0", "--port", "80"]
