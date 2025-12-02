# B2B Fire Detection Lead Estimator

This repo contains a simple lead value estimator for fire-detection sales forecasting.
Files:
- app.py — FastAPI backend (estimation endpoint)
- ui.py — Streamlit dashboard (uses averages.json)
- averages.json — computed averages from historical orders
- clean_orders.csv — processed dataset used to compute averages
- requirements.txt — Python dependencies

## Deploy to Streamlit Cloud (recommended flow)
1. Create a new GitHub repository and push all files in this repo.
2. In Streamlit Cloud, create a new app that points to your GitHub repo and `ui.py` as the main file.
3. Set a secret `API_URL` in Streamlit Secrets if you deploy the FastAPI backend separately. If you prefer a single-process solution, you can use Streamlit's local fallback (already present).

## Quick local testing (optional)
Run backend:
```
uvicorn app:app --host 0.0.0.0 --port 8000
```
Run UI:
```
streamlit run ui.py
```

