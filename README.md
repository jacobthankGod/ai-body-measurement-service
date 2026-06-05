# AI Body Scan SaaS

AI-powered body measurement extraction API.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m uvicorn api.main:app --reload --port 5001

# Test
curl http://localhost:5001/api/v2/health
```

## Deploy to Vercel

```bash
vercel deploy --prod
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/health` | GET | Health check |
| `/api/v2/measurements/extract` | POST | Extract measurements |
| `/api/v2/measurements/estimate` | POST | Estimate from height |
| `/api/v2/subscriptions/status` | GET | Subscription status |

## Authentication

All endpoints require `X-API-Key` header.

## License

Proprietary - Desby App Team
