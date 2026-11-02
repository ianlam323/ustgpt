# Green Minibus live ETA integration status

The v2 package includes official static GMB route/fare XML downloads. The existing FastAPI backend does **not yet** expose a GMB ETA endpoint.

Before adding it:
1. Open the official DATA.GOV.HK dataset: https://data.gov.hk/en-data/dataset/hk-td-sm_7-real-time-arrival-data-of-gmb
2. Read the linked `GMB_ETA_API_Specification.pdf`.
3. Confirm current endpoint paths, parameters and response schema from that specification.
4. Implement and test the live GMB API wrapper using official route/stop identifiers.
5. Add the endpoint to `dify/openapi.yaml` and test it with real current IDs.

Do not guess endpoint paths or use third-party undocumented endpoints for a graded demonstration.
