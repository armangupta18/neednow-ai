# Railway Deployment Guide — NeedNow AI Backend

## Inspection Results

| Item | Value |
|------|-------|
| **Start command** | `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}` |
| **Root directory** | `backend/` |
| **Procfile** | `backend/Procfile` (created) |
| **Runtime version** | Python 3.11.9 |
| **Build command** | `pip install -r requirements/requirements.txt` |
| **Dockerfile** | None (using Nixpacks auto-detection) |
| **Uvicorn module path** | `main:app` (NOT `app.main:app`) |

### Why `main:app` (not `app.main:app`)?

The FastAPI `app` object lives at `backend/main.py`:

```
backend/
├── main.py          ← contains `app = FastAPI(...)`
├── app/
│   ├── __init__.py
│   ├── api/
│   ├── services/
│   └── ...
```

Since Railway's working directory is set to `backend/`, the command is:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Railway Settings (exact values)

### Service Configuration

| Setting | Value |
|---------|-------|
| **Source** | GitHub repo → `neednow-ai` |
| **Root Directory** | `/backend` |
| **Builder** | Nixpacks (auto-detected as Python) |
| **Build Command** | `pip install -r requirements/requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Watch Paths** | `/backend/**` |

### Environment Variables

| Variable | Value | Required |
|----------|-------|----------|
| `SECRET_KEY` | (generate random 32-char string) | ✅ |
| `DATABASE_URL` | `postgresql+asyncpg://neondb_owner:xxx@ep-xxx.neon.tech/neondb?ssl=require` | ✅ |
| `GEMINI_API_KEY` | (your Google AI key) | ✅ |
| `GEMINI_MODEL_ID` | `gemini-2.5-flash` | ❌ (has default) |
| `GEMINI_MAX_TOKENS` | `4096` | ❌ (has default) |
| `USE_MOCK_LLM` | `false` | ✅ (must set to false for live AI) |
| `ENVIRONMENT` | `production` | ❌ |
| `DEBUG` | `false` | ❌ |
| `LOG_LEVEL` | `INFO` | ❌ |
| `ALLOWED_ORIGINS` | `["https://your-frontend.vercel.app"]` | ✅ |
| `PORT` | (Railway auto-injects) | — |

### Networking

| Setting | Value |
|---------|-------|
| **Port** | `$PORT` (Railway auto-assigns, typically 8080) |
| **Public Networking** | Enable → generates `xxx.railway.app` domain |
| **Custom Domain** | Optional |
| **Health Check Path** | `/health` |

---

## Deployment Files Created

### `backend/Procfile`
```
web: uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### `backend/nixpacks.toml`
```toml
# Railway/Nixpacks build configuration for NeedNow AI Backend
# Uses Nix-provided Python 3.11 (no mise, no runtime.txt)

[phases.setup]
nixPkgs = ["python311", "python311Packages.pip"]

[phases.install]
cmds = ["pip install --upgrade pip", "pip install -r requirements/requirements.txt"]

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

> **Note**: No `runtime.txt` file. That file triggers Railway's `mise` installer which can fail with GitHub artifact attestation errors. The `nixpacks.toml` provides Python 3.11 directly from Nix packages.

---

## Step-by-Step Deployment

### 1. Push to GitHub

```bash
cd neednow-ai
git add .
git commit -m "feat: add Railway deployment config"
git push origin main
```

### 2. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose `armangupta18/neednow-ai`

### 3. Configure Root Directory

In the Railway service settings:
- **Settings → Root Directory**: type `/backend`

This tells Railway to only look at the `backend/` folder for build/start.

### 4. Set Environment Variables

Go to **Variables** tab and add:

```
SECRET_KEY=<generate-with: openssl rand -hex 32>
DATABASE_URL=postgresql+asyncpg://neondb_owner:npg_xxx@ep-xxx.neon.tech/neondb?ssl=require
GEMINI_API_KEY=<your-google-ai-key>
USE_MOCK_LLM=false
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=["https://neednow-ai.vercel.app","*"]
```

### 5. Deploy

Railway auto-deploys on push. Check the **Deploy Logs** for:

```
==================================================
  NeedNow AI Backend Started
  LLM: Google Gemini (gemini-2.5-flash)
  Mode: GEMINI LIVE
  API Key: ✓ configured
==================================================
```

### 6. Enable Public URL

- **Settings → Networking → Public Networking** → Generate Domain
- Copy the URL (e.g., `https://neednow-ai-production.up.railway.app`)

### 7. Update Frontend

Set in Vercel (or `.env.local`):
```
NEXT_PUBLIC_API_URL=https://neednow-ai-production.up.railway.app/api/v1
```

---

## Verify Deployment

```bash
# Health check
curl https://YOUR-APP.railway.app/health

# Expected:
# {"status":"healthy","environment":"production"}

# Test chat endpoint
curl -X POST https://YOUR-APP.railway.app/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"550e8400-e29b-41d4-a716-446655440000","message":"I need toothpaste"}'
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'app'` | Root directory not set to `/backend` |
| `ModuleNotFoundError: No module named 'main'` | Root directory not set to `/backend` |
| `ValidationError: SECRET_KEY field required` | Add `SECRET_KEY` env variable |
| `Can't connect to database` | Check `DATABASE_URL` uses `postgresql+asyncpg://` prefix and `?ssl=require` |
| `Gemini API 403/401` | Check `GEMINI_API_KEY` is valid |
| `CORS error from frontend` | Add frontend domain to `ALLOWED_ORIGINS` |
| Port binding error | Don't hardcode port — use `$PORT` (Railway provides it) |

---

## Cost Estimate (Railway)

| Tier | Cost | Included |
|------|------|----------|
| Hobby | $5/month | 512 MB RAM, shared CPU, 5GB disk |
| Pro | $20/month | 8 GB RAM, dedicated CPU, 100GB disk |

For a hackathon demo, the **Hobby tier** is sufficient. The backend uses ~200 MB RAM at idle.
