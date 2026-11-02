# Data notes

Run `python scripts/download_static_data.py` after pip/network certificate issues are resolved. The downloader fetches TD XML files for franchised buses and Green Minibuses (GMB), plus MTR CSVs and KMB/Citybus reference JSON.

Official TD XML data dictionary:
https://static.data.gov.hk/td/routes-fares-xml/dataspec/ptroutefare_xml_dataspec.pdf

Important:
- `ROUTE_GMB.xml`, `RSTOP_GMB.xml`, `STOP_GMB.xml` and `FARE_GMB.xml` contain Green Minibus route/fare reference data.
- GMB live ETA is a separate DATA.GOV.HK API, not one of the static XML tables.
- TD stop coordinates X/Y use the Hong Kong 1980 Grid, not WGS84 latitude/longitude.
- TD stop IDs and KMB/Citybus live API stop IDs are not interchangeable.
- The generic XML exporter may need adjustment after inspecting the latest raw XML structure. Preserve raw files and verify columns/row counts before importing to Dify.
- Red minibuses are not covered by the GMB dataset and should not be presented as having the same live ETA coverage.
