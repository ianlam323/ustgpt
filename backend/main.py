from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="HKUST Smart Transport API", version="1.0.0")
HK_TZ = ZoneInfo("Asia/Hong_Kong")
KMB = "https://data.etabus.gov.hk/v1/transport/kmb"
CITYBUS = "https://rt.data.gov.hk/v2/transport/citybus"
MTR = "https://rt.data.gov.hk/v1/transport/mtr/getSchedule.php"

def now_hkt():
    return datetime.now(HK_TZ).isoformat(timespec="seconds")

async def fetch_json(url, params=None):
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            r = await client.get(url, params=params, headers={"User-Agent": "HKUST-Transport-Assistant/1.0"})
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"Upstream transport API HTTP {e.response.status_code}")
    except (httpx.RequestError, ValueError) as e:
        raise HTTPException(502, f"Transport API unavailable/invalid response: {type(e).__name__}")

@app.get("/health")
async def health():
    return {"status": "ok", "time_hkt": now_hkt()}

@app.get("/tools/kmb_eta", operation_id="kmb_eta")
async def kmb_eta(
    stop_id: str = Query(..., description="KMB live API stop ID (16-character identifier from KMB stop/route-stop API; not TD XML STOP_ID)"),
    route: str = Query(..., description="KMB route number"),
    service_type: str = Query("1", description="Service type from KMB route data")
):
    url = f"{KMB}/eta/{stop_id}/{route}/{service_type}"
    payload = await fetch_json(url)
    return {"operator": "KMB/LWB", "stop_id": stop_id, "route": route,
            "arrivals": payload.get("data", []), "source": "Transport Department KMB/LWB ETA API",
            "source_url": url, "retrieved_at_hkt": now_hkt(),
            "feed_refresh_note": "ETA data is updated about once per minute."}


@app.get("/tools/kmb_route_stops", operation_id="kmb_route_stops")
async def kmb_route_stops(
    route: str = Query(..., description="KMB route number"),
    direction: str = Query(..., description="KMB bound, e.g. O or I"),
    service_type: str = Query("1", description="KMB service type")
):
    url = f"{KMB}/route-stop/{route}/{direction}/{service_type}"
    payload = await fetch_json(url)
    return {"operator": "KMB/LWB", "route": route, "direction": direction,
            "service_type": service_type, "stops": payload.get("data", []),
            "source": "Transport Department KMB route-stop API",
            "source_url": url, "retrieved_at_hkt": now_hkt()}

@app.get("/tools/citybus_eta", operation_id="citybus_eta")
async def citybus_eta(
    stop_id: str = Query(..., description="Citybus stop ID"),
    route: str = Query(..., description="Citybus route number")
):
    url = f"{CITYBUS}/eta/ctb/{stop_id}/{route}"
    payload = await fetch_json(url)
    return {"operator": "Citybus", "stop_id": stop_id, "route": route,
            "arrivals": payload.get("data", []), "source": "Citybus / Transport Department Next Bus API",
            "source_url": url, "feed_generated_timestamp": payload.get("generated_timestamp"),
            "retrieved_at_hkt": now_hkt(),
            "feed_refresh_note": "ETA data is updated about once per minute."}


@app.get("/tools/citybus_route_stops", operation_id="citybus_route_stops")
async def citybus_route_stops(
    route: str = Query(..., description="Citybus route number"),
    direction: str = Query(..., description="inbound or outbound")
):
    url = f"{CITYBUS}/route-stop/CTB/{route}/{direction}"
    payload = await fetch_json(url)
    return {"operator": "Citybus", "route": route, "direction": direction,
            "stops": payload.get("data", []),
            "source": "Citybus / Transport Department route-stop API",
            "source_url": url, "retrieved_at_hkt": now_hkt()}

@app.get("/tools/mtr_eta", operation_id="mtr_eta")
async def mtr_eta(
    line: str = Query(..., description="MTR line code, e.g. ISL or TCL"),
    sta: str = Query(..., description="MTR station code, e.g. CEN")
):
    payload = await fetch_json(MTR, {"line": line.upper(), "sta": sta.upper()})
    return {"operator": "MTR", "line": line.upper(), "station": sta.upper(),
            "result": payload, "source": "MTR Real-time Train Information API via DATA.GOV.HK",
            "source_url": MTR, "retrieved_at_hkt": now_hkt(),
            "feed_refresh_note": "MTR feed is updated about every 10 seconds; only published lines are covered."}

class Segment(BaseModel):
    mode: str
    operator: str
    route_or_line: str
    board: str
    alight: str
    fare_hkd: Optional[float] = None
    duration_min: Optional[float] = None
    walking_m: Optional[float] = 0
    source: Optional[str] = None

class CandidateRoute(BaseModel):
    name: str
    segments: list[Segment]
    transfers: int = Field(ge=0)
    total_duration_min: Optional[float] = None
    total_fare_hkd: Optional[float] = None
    total_walking_m: Optional[float] = None

class CompareRequest(BaseModel):
    routes: list[CandidateRoute] = Field(min_length=1, max_length=20)

@app.post("/tools/compare_routes", operation_id="compare_routes")
async def compare_routes(req: CompareRequest):
    routes = []
    for r in req.routes:
        duration = r.total_duration_min
        if duration is None and all(s.duration_min is not None for s in r.segments):
            duration = sum(s.duration_min or 0 for s in r.segments)
        fare = r.total_fare_hkd
        if fare is None and all(s.fare_hkd is not None for s in r.segments):
            fare = sum(s.fare_hkd or 0 for s in r.segments)
        walking = r.total_walking_m
        if walking is None:
            walking = sum(s.walking_m or 0 for s in r.segments)
        routes.append({"name": r.name, "segments": [s.model_dump() for s in r.segments],
                       "transfers": r.transfers, "total_duration_min": duration,
                       "total_fare_hkd": fare, "total_walking_m": walking})
    fastest = min((x for x in routes if x["total_duration_min"] is not None),
                  key=lambda x: x["total_duration_min"], default=None)
    cheapest = min((x for x in routes if x["total_fare_hkd"] is not None),
                   key=lambda x: x["total_fare_hkd"], default=None)
    fewest = min(routes, key=lambda x: (x["transfers"],
                 x["total_duration_min"] if x["total_duration_min"] is not None else 10**9))
    return {"fastest": fastest, "cheapest": cheapest, "fewest_transfers": fewest,
            "note": "Ranks candidate itineraries supplied by caller; does not discover or validate network connections. Unknown fares/times are not guessed.",
            "retrieved_at_hkt": now_hkt()}
