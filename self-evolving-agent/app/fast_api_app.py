import os

import google.auth
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging
from pydantic import BaseModel

from app.agent import get_current_model_name, switch_model
from app.app_utils.telemetry import setup_telemetry

setup_telemetry()
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_service_uri = None
artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=True,
)
app.title = "self-evolving-agent"
app.description = "API for interacting with the Self-Evolving Agent"

OLLAMA_BASE = "http://localhost:11434"


class SwitchModelRequest(BaseModel):
    model: str


@app.get("/api/models")
async def list_models():
    models = [
        {"name": "gemini-flash-latest", "provider": "gemini"},
    ]
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            if resp.status_code == 200:
                for m in resp.json().get("models", []):
                    models.append({
                        "name": m.get("name", ""),
                        "provider": "ollama",
                        "size": m.get("size"),
                    })
    except Exception:
        pass
    current = get_current_model_name()
    for m in models:
        m["active"] = m["name"] == current
    return {"models": models, "current": current}


@app.get("/api/models/current")
async def current_model():
    return {"model": get_current_model_name()}


@app.post("/api/models/switch")
async def switch_model_endpoint(body: SwitchModelRequest):
    try:
        result = switch_model(body.model)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))
