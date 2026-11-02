from pathlib import Path
import csv
import urllib.request
import xml.etree.ElementTree as ET
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
RAW.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "ROUTE_BUS.xml": "https://static.data.gov.hk/td/routes-fares-xml/ROUTE_BUS.xml",
    "RSTOP_BUS.xml": "https://static.data.gov.hk/td/routes-fares-xml/RSTOP_BUS.xml",
    "STOP_BUS.xml": "https://static.data.gov.hk/td/routes-fares-xml/STOP_BUS.xml",
    "FARE_BUS.xml": "https://static.data.gov.hk/td/routes-fares-xml/FARE_BUS.xml",
    # Green Minibus (GMB) static route, stop sequence, terminus and fare datasets.
    "ROUTE_GMB.xml": "https://static.data.gov.hk/td/routes-fares-xml/ROUTE_GMB.xml",
    "STOP_GMB.xml": "https://static.data.gov.hk/td/routes-fares-xml/STOP_GMB.xml",
    "FARE_GMB.xml": "https://static.data.gov.hk/td/routes-fares-xml/FARE_GMB.xml",
    "mtr_lines_and_stations.csv": "https://opendata.mtr.com.hk/data/mtr_lines_and_stations.csv",
    "mtr_lines_fares.csv": "https://opendata.mtr.com.hk/data/mtr_lines_fares.csv",
    "airport_express_fares.csv": "https://opendata.mtr.com.hk/data/airport_express_fares.csv",
    "barrier_free_facilities.csv": "https://opendata.mtr.com.hk/data/barrier_free_facilities.csv",
    "kmb_routes.json": "https://data.etabus.gov.hk/v1/transport/kmb/route/",
    "kmb_stops.json": "https://data.etabus.gov.hk/v1/transport/kmb/stop",
    "kmb_route_stop.json": "https://data.etabus.gov.hk/v1/transport/kmb/route-stop",
    "citybus_routes.json": "https://rt.data.gov.hk/v2/transport/citybus/route/CTB",
}

def fetch(url, dest):
    print(f'NOW DOWNLOADING: {dest.name} | {url}', flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "HKUST-Transport-Project/1.0"})
    print(f"Requesting URL: {url}", flush=True)
    with urllib.request.urlopen(req, timeout=60) as response:
        blob = response.read()
    dest.write_bytes(blob)
    print(f"Downloaded {dest.name}: {len(blob):,} bytes")

def lname(tag):
    return tag.split("}")[-1]

def flatten(el, prefix=""):
    row = {}
    for child in list(el):
        key = f"{prefix}.{lname(child.tag)}" if prefix else lname(child.tag)
        if list(child):
            row.update(flatten(child, key))
        else:
            value = (child.text or "").strip()
            if key in row:
                key += "_duplicate"
            row[key] = value
    return row

def export_xml(xml_file, csv_file):
    root = ET.parse(xml_file).getroot()
    # Export leaf-record elements. Verify fields against the official data dictionary.
    rows = []
    for el in root.iter():
        children = list(el)
        if children and all(not list(c) for c in children):
            row = flatten(el)
            if row:
                rows.append(row)
    if not rows:
        rows = [flatten(el) for el in list(root) if list(el)]
    if not rows:
        raise RuntimeError(f"No rows detected in {xml_file}")
    widest = max(len(r) for r in rows)
    rows = [r for r in rows if len(r) >= max(1, widest - 2)]
    headers = sorted({k for r in rows for k in r})
    with csv.DictWriter(csv_file.open("w", newline="", encoding="utf-8-sig"), fieldnames=headers) as w:
        w.writeheader()
        w.writerows(rows)
    print(f"Exported {len(rows):,} records to {csv_file.name}")

def main():
    for name, url in SOURCES.items():
        target = RAW / name
        if not target.exists() or target.stat().st_size == 0:
            print(f"Downloading {name}: {url}", flush=True)
            fetch(url, target)
    for name in [
        "ROUTE_BUS.xml", "RSTOP_BUS.xml", "STOP_BUS.xml", "FARE_BUS.xml",
        "ROUTE_GMB.xml", "STOP_GMB.xml", "FARE_GMB.xml"
    ]:
        export_xml(RAW / name, DATA / (name[:-4] + ".csv"))
    for name in SOURCES:
        if name.endswith(".csv"):
            text = (RAW / name).read_text(encoding="utf-8-sig")
            (DATA / name).write_text(text, encoding="utf-8-sig")
            print(f"Prepared {name}")
        elif name.endswith(".json"):
            print(f"Saved live-ID lookup reference: {name}")
    print("Done. Review exported headers against:")
    print("https://static.data.gov.hk/td/routes-fares-xml/dataspec/ptroutefare_xml_dataspec.pdf")
    print("https://opendata.mtr.com.hk/doc/DataDictionary.zip")
    print("KMB live stop IDs are 16-character IDs; do not substitute TD XML numeric STOP_ID values.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Download/export failed: {e}", file=sys.stderr)
        print("Check internet access and retry. Existing raw downloads are retained.", file=sys.stderr)
        raise
