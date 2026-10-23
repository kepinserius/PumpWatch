from fastapi import FastAPI

from pumpwatch.logging_config import setup_logging

setup_logging()

app = FastAPI(title="PumpWatch API", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready"}
