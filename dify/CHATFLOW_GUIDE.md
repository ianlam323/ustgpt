# Dify Chatflow setup

## 1. Knowledge Base
After running the downloader, inspect and upload populated CSV exports:
- Franchised buses: `ROUTE_BUS.csv`, `RSTOP_BUS.csv`, `STOP_BUS.csv`, `FARE_BUS.csv`
- Green minibuses: `ROUTE_GMB.csv`, `RSTOP_GMB.csv`, `STOP_GMB.csv`, `FARE_GMB.csv`
- MTR: `mtr_lines_and_stations.csv`, `mtr_lines_fares.csv`, `airport_express_fares.csv`, `barrier_free_facilities.csv`, `barrier_free_access_category.csv`

Keep raw XML files for audit. Verify flattened XML columns against the official TD data dictionary before using them in joins. Add metadata only after inspecting real headers: operator, route ID, mode, update date and source URL.

## 2. Live data
- KMB and Citybus ETA: call their live APIs at query time.
- MTR train information: call the MTR real-time API at query time.
- Green Minibus ETA: use the Transport Department's official GMB Real-time Arrival Information System API at query time. Consult its current API specification from DATA.GOV.HK and test with current route/stop IDs. Do not store ETA snapshots as static Knowledge Base facts.
- The starter FastAPI backend currently includes KMB, Citybus and MTR live endpoints. GMB live ETA still needs to be wired into the backend using the official API specification before it can be offered as a working Dify tool.

## 3. Chatflow nodes
1. Start: capture the user's message.
2. Question Classifier: route planning / bus ETA / MTR ETA / GMB ETA / fare / accessibility / other.
3. LLM slot extraction: origin, destination, departure time, transport preference, accessibility need.
4. IF/ELSE: if origin or destination is missing, ask a follow-up and preserve context.
5. Knowledge Retrieval: retrieve relevant bus/GMB route, stop sequence, stop coordinates, fares, MTR stations/fares and accessibility records.
6. LLM parameter resolution: resolve actual stop IDs, route number/service type, MTR line code and station code from retrieved records. Never guess.
7. Tool calls: call the appropriate live API only when the relevant IDs are known.
8. Route generation: use verified route-stop data and verified transfer links. The starter API does not discover itineraries; implement a graph/k-shortest-path service for genuine network-wide routing.
9. Compare Routes tool: pass candidate itineraries to `compare_routes`.
10. LLM final response: present fastest, cheapest and fewest transfers; cite fare sources and ETA source/retrieval time.
11. Answer: return concise response and ask if the user wants another destination.

## 4. Important limitations
TD route-stop data gives ordered stops, not reliable travel duration for every stop-to-stop segment. Build a graph with stop/station nodes, route edges, walking transfer edges and defensible journey-time estimates. GMB licensed headways are not guaranteed vehicle departure times. Do not let the LLM invent connections, fares, live arrivals or travel times.

## 5. Publish and test
Publish the app with reviewer access and keep both Dify app and backend available for the review window. Test API timeouts, no ETA, ambiguous stops, missing origin/destination, incomplete fare and Chinese place names. Test Green Minibus separately, including cases where live ETA is unavailable.
