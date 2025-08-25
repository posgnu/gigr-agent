from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger

from fastapi_langraph.middleware.logging import logging_middleware

app = FastAPI()
app.middleware("http")(logging_middleware)


@app.get("/")
async def read_main():
    return {"msg": "Hello World"}


client = TestClient(app)


def test_logging_middleware():
    log_messages = []

    def sink(message):
        log_messages.append(message)

    logger.remove()
    logger.add(sink)

    response = client.get("/")
    assert response.status_code == 200
    assert len(log_messages) == 1
    log_message = log_messages[0]
    assert "GET / 1.1" in log_message
    assert "200" in log_message
