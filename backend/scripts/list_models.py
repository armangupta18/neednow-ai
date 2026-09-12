"""
list_models.py -- List all available Gemini models for every API key in .env

Usage:
    python scripts/list_models.py

Reads GEMINI_API_KEY from backend/.env (comma-separated keys),
queries the Gemini API for each key, and prints which models are available.
"""

import sys
import io
from pathlib import Path

# Force UTF-8 output so Windows cp1252 does not choke on special chars
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Load .env from the backend directory (one level up from scripts/)
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


def load_env(path: Path) -> dict:
    env: dict = {}
    if not path.exists():
        print(f"[ERROR]  .env not found at {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


env = load_env(ENV_FILE)

raw_keys = env.get("GEMINI_API_KEY", "")
api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

if not api_keys:
    print("[ERROR]  No GEMINI_API_KEY entries found in .env")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Import Gemini SDK
# ---------------------------------------------------------------------------
try:
    import google.generativeai as genai  # noqa: E402
except ImportError:
    print("[ERROR]  google-generativeai not installed.")
    print("         Run:  pip install google-generativeai")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Query models for each key
# ---------------------------------------------------------------------------
SEP = "=" * 65
print(f"\n{SEP}")
print(f"  Gemini Model Discovery  |  {len(api_keys)} API key(s) found in .env")
print(f"{SEP}\n")

all_results: dict[int, list[str]] = {}

for idx, key in enumerate(api_keys, start=1):
    preview = f"{key[:6]}...{key[-4:]}" if len(key) >= 10 else key
    print(f"[KEY #{idx}]  {preview}")
    print(f"    {'-'*56}")

    try:
        genai.configure(api_key=key, transport="rest")
        models = list(genai.list_models())

        # Keep only models that support generateContent
        generative = [
            m for m in models
            if "generateContent" in (m.supported_generation_methods or [])
        ]

        if not generative:
            print("    [WARN]  No generateContent-capable models found.")
        else:
            print(f"    [OK]    {len(generative)} model(s) available:\n")
            for m in generative:
                name = m.name.replace("models/", "")
                display = m.display_name or name
                print(f"            * {name:<42}  {display}")

        all_results[idx] = [m.name.replace("models/", "") for m in generative]

    except Exception as exc:
        short = str(exc)[:200]
        print(f"    [ERROR]  {short}")
        all_results[idx] = []

    print()

# ---------------------------------------------------------------------------
# Summary: models available on every working key
# ---------------------------------------------------------------------------
working_keys = {k: v for k, v in all_results.items() if v}

print(SEP)
print(f"  SUMMARY  |  Working keys: {len(working_keys)}/{len(api_keys)}")
print(SEP)

if working_keys:
    sets = [set(v) for v in working_keys.values()]
    common = sets[0].intersection(*sets[1:]) if len(sets) > 1 else sets[0]

    if common:
        ranked = sorted(
            common,
            key=lambda n: (0 if "flash" in n else (1 if "pro" in n else 2), n),
        )
        print("  Models available on ALL working keys:\n")
        for name in ranked:
            print(f"    [OK]  {name}")
    else:
        print("  [WARN]  No model common to all working keys.")

    # Recommend the fastest/newest flash
    flash_models = [n for n in (common if common else []) if "flash" in n]
    if flash_models:
        best = sorted(flash_models, reverse=True)[0]
        print(f"\n  [TIP]  Recommended fastest model  : {best}")
        print(f"         Update .env               : GEMINI_MODEL_ID={best}")
else:
    print("  [ERROR]  No working API keys found.")

print(f"\n{SEP}\n")
