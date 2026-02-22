from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import statistics
import math
import os

app = FastAPI()

# Proper CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
file_path = os.path.join(BASE_DIR, "..", "telemetry.json")

with open(file_path) as f:
    telemetry = json.load(f)

class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.options("/")
def preflight():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

@app.post("/")
def compute_metrics(body: RequestBody, response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"

    result = {}

    for region in body.regions:
        records = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        if not latencies:
            continue

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[math.ceil(0.95 * len(latencies)) - 1]
        avg_uptime = statistics.mean(uptimes)
        breaches = sum(1 for l in latencies if l > body.threshold_ms)

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return result
