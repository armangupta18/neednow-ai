# Local Development Setup — NeedNow AI

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL connection (Neon serverless works)
- Git

---

## Backend Setup

### 1. Navigate to backend directory

```bash
cd neednow-ai/backend
```

### 2. Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set these required values:

```env
SECRET_KEY=any-random-string-for-local-dev
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname?ssl=require
GEMINI_API_KEY=your_gemini_api_key_here
USE_MOCK_LLM=false
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

> **Mock mode**: Set `USE_MOCK_LLM=true` to run without a real Gemini API key.

### 5. Start the backend

```bash
# From inside the backend/ directory:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> **Important**: The entrypoint is `main:app` (not `app.main:app`).
> `main.py` lives at `backend/main.py`, so run from `backend/`.

### 6. Verify backend is running

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","environment":"development"}

curl http://localhost:8000/
# Expected: {"service":"NeedNow AI","version":"1.0.0","status":"running"}
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Frontend Setup

### 1. Navigate to frontend directory

```bash
cd neednow-ai/frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

`.env.local` should already exist. If not, create it:

```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

> **Note**: Do NOT include `/api/v1` in the URL — the API route constants add it automatically.

### 4. Start the frontend

```bash
npm run dev
```

### 5. Verify frontend is running

Open: [http://localhost:3000](http://localhost:3000)

---

## Running Both Together

Open two terminal windows:

**Terminal 1 — Backend:**
```bash
cd neednow-ai/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd neednow-ai/frontend
npm run dev
```

---

## Verification Checklist

| URL | Expected |
|-----|----------|
| `http://localhost:3000` | NeedNow AI home page |
| `http://localhost:8000` | `{"service":"NeedNow AI","status":"running"}` |
| `http://localhost:8000/health` | `{"status":"healthy"}` |
| `http://localhost:8000/docs` | Swagger UI |

---

## Common Issues

### Backend won't start: `ModuleNotFoundError`

Make sure you're running from inside `backend/` and your venv is activated:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### Frontend shows "Failed to connect"

Check `.env.local` contains:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```
Then restart the dev server: `npm run dev`

### CORS errors in browser

The backend `.env` must include `http://localhost:3000` in `ALLOWED_ORIGINS`:
```
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```
Restart the backend after changing `.env`.

### Database connection fails

The `DATABASE_URL` must use `postgresql+asyncpg://` (not `postgresql://`). The backend auto-converts it, but verify the Neon connection string is correct.

---

## Environment Variables Summary

### Backend (`backend/.env`)

| Variable | Required | Local Value |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | `any-string` |
| `DATABASE_URL` | Yes | Neon connection string |
| `GEMINI_API_KEY` | Yes* | Your Google AI key |
| `USE_MOCK_LLM` | No | `true` (skip Gemini) |
| `ALLOWED_ORIGINS` | No | `["http://localhost:3000"]` |

### Frontend (`frontend/.env.local`)

| Variable | Required | Local Value |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000` |
