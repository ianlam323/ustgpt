from pathlib import Path
import csv
from fastapi import APIRouter, Query

router = APIRouter(prefix="/tools", tags=["Local transport database"])
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

def read_csv(filename: str):
    path = DATA_DIR / filename
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except (OSError, UnicodeError, csv.Error):
        return []

def field(row: dict, *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""

@router.get("/data_status", operation_id="local_data_status")
def data_status():
    filenames = ["bus_routes.csv", "bus_route_stops.csv", "bus_route_stop_details.csv",
                 "bus_stops.csv", "bus_section_fares.csv", "gmb_routes.csv",
                 "gmb_route_stops.csv", "gmb_section_fares.csv",
                 "mtr_lines_and_stations.csv", "mtr_lines_fares.csv"]
    return {"data_directory": "data/",
            "datasets": {name: {"rows": len(read_csv(name)), "has_data": len(read_csv(name)) > 0}
                         for name in filenames},
            "note": "This reports local repository CSV files. A zero row count means the file is absent, empty, or could not be read."}

@router.get("/search_bus_routes", operation_id="local_search_bus_routes")
def search_bus_routes(q: str = Query(..., min_length=1, description="Route number, origin or destination; English or Chinese")):
    query = q.casefold().strip()
    matches = []
    for row in read_csv("bus_routes.csv"):
        if query not in " ".join(str(v or "") for v in row.values()).casefold():
            continue
        matches.append({
            "route_id": field(row, "ROUTE_ID"),
            "operator": field(row, "COMPANY_CODE"),
            "route": field(row, "ROUTE_NAMEE", "ROUTE_NAMEC", "ROUTE_NAME"),
            "origin": field(row, "LOC_START_NAMEE", "LOC_START_NAMEC"),
            "destination": field(row, "LOC_END_NAMEE", "LOC_END_NAMEC"),
            "scheduled_journey_minutes": field(row, "JOURNEY_TIME"),
            "full_fare_hkd": field(row, "FULL_FARE"),
            "last_updated": field(row, "LAST_UPDATE_DATE"),
            "source": field(row, "HYPERLINK_E", "HYPERLINK_C", "HYPERLINK_S")})
        if len(matches) >= 30:
            break
    return {"query": q, "count": len(matches), "routes": matches,
            "note": "Static route search only; not a complete origin-to-destination planner and has no live ETA."}

@router.get("/bus_route_stops", operation_id="local_bus_route_stops")
def bus_route_stops(route_id: str = Query(..., description="ROUTE_ID from bus_routes.csv"),
                    route_seq: str | None = Query(None, description="Optional direction/route sequence")):
    selected = [row for row in read_csv("bus_route_stops.csv")
                if field(row, "ROUTE_ID") == route_id
                and (route_seq is None or field(row, "ROUTE_SEQ") == route_seq)]
    selected.sort(key=lambda row: int(field(row, "STOP_SEQ") or 0))
    stops = [{"sequence": field(row, "STOP_SEQ"), "stop_id": field(row, "STOP_ID"),
              "name_en": field(row, "STOP_NAMEE"), "name_zh_hant": field(row, "STOP_NAMEC"),
              "name_zh_hans": field(row, "STOP_NAMES"), "pick_drop": field(row, "STOP_PICK_DROP"),
              "last_updated": field(row, "LAST_UPDATE_DATE")} for row in selected]
    return {"route_id": route_id, "route_seq": route_seq, "count": len(stops), "stops": stops,
            "note": "Ordered static stop sequence only; it does not establish route transfers or live arrival times."}
