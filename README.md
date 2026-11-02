# HKUST Smart Transport Assistant — updated starter package (v2)

**Coverage:** HKUST + Hong Kong-wide KMB, Citybus, MTR and **Green Minibus (GMB / 專線小巴)**.

## Important: what is and is not included
This is a starter project, not a finished journey planner. The CSV files supplied here are templates. The downloader fetches official data when run on a computer with working internet and certificate validation. The package-generation environment could not populate the official datasets, so **do not upload the blank CSV templates to Dify as real transport data**.

This version adds the Transport Department's four GMB XML datasets (route master, route-stop sequence, stop/terminus information and section fares) to the downloader. The GMB live-arrival API is an official separate data source and must be integrated/tested as a live API; it is not a static CSV.

## Mac setup
Open Terminal in this project folder. Use Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Before installing packages, make sure your Mac's Python certificate setup is working. If `pip` reports `SSL: CERTIFICATE_VERIFY_FAILED`, stop with Control-C and fix the Mac/Python certificate or network issue first. **Do not disable SSL verification or use insecure `trusted-host` workarounds.**

Once pip can connect securely:

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python scripts/download_static_data.py
```

The downloader stores original files in `data/raw/` and exports XML tables as CSV in `data/`. Inspect the actual headers and row counts against the official data dictionary before importing them into Dify.

## Official GMB data
- Static GMB routes and fares: `ROUTE_GMB.xml`, `RSTOP_GMB.xml`, `STOP_GMB.xml`, `FARE_GMB.xml` from the Transport Department.
- GMB live ETA and reference APIs: Transport Department's Green Minibus Real-time Arrival Information System, via DATA.GOV.HK. ETA data is refreshed about once per minute.
- GMB static route/fare information is not the same as live ETA. Keep live ETA as a query-time API call.

## Run the API backend
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
Then open `http://localhost:8000/docs`. For Dify Cloud, deploy the backend to a publicly reachable HTTPS host; Dify Cloud cannot call your laptop's localhost.

## Dify
- Upload only populated and checked CSVs to a Knowledge Base.
- Import `dify/openapi.yaml` as a custom tool provider.
- Replace `https://YOUR-PUBLIC-HTTPS-HOST` with your deployed backend URL.
- Follow `dify/CHATFLOW_GUIDE.md` and `dify/SYSTEM_PROMPT.md`.

## Route-planning limitation
The current `compare_routes` endpoint ranks candidate itineraries supplied to it; it does **not** discover every possible route. A genuine network-wide planner needs a verified graph of route-stop edges, transfer/walking links and defensible journey-time estimates. Do not let the LLM invent connections, fares or journey times.

## Red minibuses
This package's minibus scope is **Green Minibus (專線小巴)** because the Transport Department provides structured route/fare and live ETA data for GMBs. Red minibuses (紅Van) do not have the same complete structured route/ETA coverage; do not imply that GMB data or live ETAs apply to red minibuses.
