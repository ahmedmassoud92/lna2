[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new?template=https://github.com/ahmedmassoud92/lna2)

# Libya Political Trends 3D — Railway Single Service

This package serves **frontend + API** from one Flask app (easiest for Railway).

## Run locally
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export MAPBOX_TOKEN="pk.YOUR_MAPBOX_PUBLIC_TOKEN_HERE"
python app.py
```
Open http://127.0.0.1:8000

## Deploy on Railway (single service)
- Create a service from your GitHub repo.
- Set **Start Command**:
```bash
bash -lc "cd backend && pip install -r requirements.txt && python app.py"
```
- Add Variable: `MAPBOX_TOKEN = pk.YOUR_MAPBOX_PUBLIC_TOKEN_HERE`

## API
- `GET /api/config` → returns Mapbox token used by the frontend.
- `GET /api/search?q=...` → aggregates:
  - Twitter via `snscrape` (no API key needed)
  - Google Trends via `pytrends`
  - Facebook: placeholder array (plug your collector when ready)
  - Returns sentiment (VADER) + simple geo city mentions.

## Notes
- To disable Google Trends, remove `gtrends_score()` call inside `/api/search`.
- For Facebook, implement a collector (Playwright/BeautifulSoup or Graph API).
