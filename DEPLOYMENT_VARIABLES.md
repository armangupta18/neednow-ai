# Deployment Variables — NeedNow AI

## Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ Yes | `http://localhost:8000/api/v1` | Backend API base URL (must include `/api/v1` suffix) |
| `NEXT_PUBLIC_WS_URL` | ❌ No | `ws://localhost:8000/ws` | WebSocket URL (for future real-time features) |
| `NEXT_PUBLIC_APP_NAME` | ❌ No | `NeedNow AI` | Application display name (hardcoded in next.config.ts) |

### Source Files
- `frontend/src/constants/api.ts` → `NEXT_PUBLIC_API_URL`
- `frontend/src/lib/api.ts` → `NEXT_PUBLIC_API_URL`
- `frontend/src/services/api.ts` → `NEXT_PUBLIC_API_URL`
- `frontend/src/lib/websocket.ts` → `NEXT_PUBLIC_WS_URL`
- `frontend/next.config.ts` → `NEXT_PUBLIC_APP_NAME`

---

## Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ Yes | — | Application secret for signing (no default — app crashes without it) |
| `DATABASE_URL` | ✅ Yes | — | PostgreSQL connection string (no default — app crashes without it) |
| `GEMINI_API_KEY` | ✅ Yes* | `""` | Google Gemini API key. *Required for live AI; mock mode works without it |
| `GEMINI_MODEL_ID` | ❌ No | `gemini-2.5-flash` | Gemini model identifier |
| `GEMINI_MAX_TOKENS` | ❌ No | `4096` | Maximum output tokens for Gemini |
| `USE_MOCK_LLM` | ❌ No | `true` | Set to `false` to use live Gemini API |
| `APP_NAME` | ❌ No | `NeedNow AI` | Application name (display only) |
| `APP_VERSION` | ❌ No | `1.0.0` | Application version |
| `ENVIRONMENT` | ❌ No | `development` | Environment identifier (`development`/`production`) |
| `DEBUG` | ❌ No | `true` | Enable debug logging |
| `API_PREFIX` | ❌ No | `/api/v1` | API route prefix |
| `ALLOWED_ORIGINS` | ❌ No | `["http://localhost:3000", ...]` | CORS allowed origins (JSON array) |
| `FAISS_INDEX_PATH` | ❌ No | `faiss_indexes` | Path to FAISS vector index directory |
| `LOG_LEVEL` | ❌ No | `INFO` | Log level (`DEBUG`/`INFO`/`WARNING`/`ERROR`) |
| `MEMORY_TOP_K` | ❌ No | `10` | Number of memory items to retrieve |
| `VECTOR_TOP_K` | ❌ No | `20` | Number of vector search results |
| `SESSION_TTL_MINUTES` | ❌ No | `60` | Session time-to-live in minutes |

### Source Files
- `backend/app/core/settings.py` — Primary settings (used by main app)
- `backend/app/core/config.py` — Secondary settings (legacy, also loads from `.env`)

---

## Mandatory Variables Summary

### Absolutely Required (app won't start without these)

| Variable | Where | Why |
|----------|-------|-----|
| `SECRET_KEY` | Backend | Pydantic BaseSettings has no default — ValidationError on startup |
| `DATABASE_URL` | Backend | Same — no default, crashes without it |
| `NEXT_PUBLIC_API_URL` | Frontend | Without it, defaults to `localhost:8000` which won't work in production |

### Required for AI Features (app starts but AI won't work)

| Variable | Where | Why |
|----------|-------|-----|
| `GEMINI_API_KEY` | Backend | Empty default means mock mode unless `USE_MOCK_LLM=false` is also set |
| `USE_MOCK_LLM` | Backend | Must be `false` to use live Gemini |

---

## Example Values for Local Development

### Backend (`backend/.env`)

```env
SECRET_KEY=local-dev-secret-key-change-in-production
DATABASE_URL=postgresql+asyncpg://neondb_owner:password@ep-example.us-east-1.aws.neon.tech/neondb?ssl=require
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX
GEMINI_MODEL_ID=gemini-2.5-flash
GEMINI_MAX_TOKENS=4096
USE_MOCK_LLM=false
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Vercel Configuration (Frontend)

Set these in Vercel Project → Settings → Environment Variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.railway.app/api/v1` | Must point to deployed backend URL |

No secrets needed on Vercel — all frontend vars are `NEXT_PUBLIC_` (public by design).

---

## Railway Configuration (Backend)

Set these in Railway Service → Variables:

| Variable | Secret? | Value |
|----------|---------|-------|
| `SECRET_KEY` | 🔒 Yes | Generate a random 32+ character string |
| `DATABASE_URL` | 🔒 Yes | Your Neon/PostgreSQL connection string with `?sslmode=require` |
| `GEMINI_API_KEY` | 🔒 Yes | Your Google AI API key from https://aistudio.google.com/apikey |
| `GEMINI_MODEL_ID` | No | `gemini-2.5-flash` |
| `GEMINI_MAX_TOKENS` | No | `4096` |
| `USE_MOCK_LLM` | No | `false` |
| `ENVIRONMENT` | No | `production` |
| `DEBUG` | No | `false` |
| `LOG_LEVEL` | No | `INFO` |
| `ALLOWED_ORIGINS` | No | `["https://your-frontend.vercel.app"]` |

### Secrets That Must NEVER Be Committed

| Secret | Where It's Used |
|--------|----------------|
| `SECRET_KEY` | JWT/session signing |
| `DATABASE_URL` | Contains DB password |
| `GEMINI_API_KEY` | Google AI billing-linked key |

These are in `.gitignore` via the `.env` exclusion rule.

---

## Quick Deployment Checklist

```
□ Backend (Railway)
  □ Set SECRET_KEY (random string)
  □ Set DATABASE_URL (Neon connection string)
  □ Set GEMINI_API_KEY (Google AI key)
  □ Set USE_MOCK_LLM=false
  □ Set ENVIRONMENT=production
  □ Set ALLOWED_ORIGINS=["https://your-app.vercel.app"]
  □ Deploy with: uvicorn main:app --host 0.0.0.0 --port $PORT

□ Frontend (Vercel)
  □ Set NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
  □ Deploy (auto-detected as Next.js)

□ Database (Neon)
  □ Create database
  □ Copy connection string to DATABASE_URL
  □ Run: python scripts/load_products.py (one-time data load)
```
