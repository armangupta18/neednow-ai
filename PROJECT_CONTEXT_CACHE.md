# 🧠 NeedNow AI — Project Context Cache & Architecture Reference

> **Generated Context Cache for AI & Developers**  
> **Last Updated:** September 12, 2026  
> **Branch:** `Project-Cleanup-Divyansh`

---

## 📌 1. Project Overview & Value Proposition

**NeedNow AI** is an AI-powered Conversational Commerce Platform created for **Amazon HackOn 2026**. It replaces traditional search-and-filter e-commerce navigation with a unified natural language and voice interface powered by **Google Gemini 2.5 Flash**.

### Key Differentiators & Features
1. **Conversational Product Discovery:** Describe needs in free-form natural language (e.g. *"I need eco-friendly shampoo under ₹300"*).
2. **Context-Aware Intent Resolution:** Client-side & server-side action command detection handles context-dependent phrases like *"Add it"*, *"Checkout"*, or *"Show cart"* without unnecessary LLM roundtrips.
3. **Voice Commerce (Hands-Free):** Built-in Web Speech API integration for speech-to-text input and SpeechSynthesis for text-to-speech AI output.
4. **Multi-Agent Backend Architecture:** Supervisor agent orchestrating specialized sub-agents (Intent, Product Recommendation, Urgency/Emergency, Sustainability).
5. **Sustainability & Carbon Footprint Insights:** Product eco-scoring (0-100), carbon savings calculation, and green alternative recommendations (displayed when eco-score improvement ≥ 8 points).
6. **Emergency / Priority Mode:** Instant urgency analysis for critical user situations (e.g. medical, baby care, emergency repairs) with priority catalog selection.
7. **Full Persistence:** Persistent shopping cart, user memory preferences, order history, and database product catalog (60,288+ Amazon products).

---

## 🏗️ 2. High-Level Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                              USER                                      │
│             (Text Input / Voice Input / Web Speech)                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 16)                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │   Chat Interface │  │  Voice Engine    │  │   Cart & Checkout    │  │
│  │  (/chat route)   │  │ (STT + TTS API)  │  │  (/cart, /checkout)  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘  │
│           │                     │                       │              │
│  ┌────────┴─────────────────────┴───────────────────────┴───────────┐  │
│  │               Action Command Interceptor (useChat)                │  │
│  │  Local Commands ("add it", "checkout") ──► Zustand Stores        │  │
│  │  Search Commands ("find X")          ──► Backend REST API       │  │
│  └──────────────────────────────┬───────────────────────────────────┘  │
└─────────────────────────────────┼──────────────────────────────────────┘
                                  │ POST /api/v1/chat
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                               │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  SUPERVISOR AGENT (Orchestrator)                 │  │
│  │                                                                  │  │
│  │  ┌───────────────┐ ┌───────────────┐ ┌─────────────────────────┐ │  │
│  │  │ Intent Agent  │ │ Urgency Agent │ │ Sustainability Agent    │ │  │
│  │  └───────┬───────┘ └───────┬───────┘ └────────────┬────────────┘ │  │
│  │          │                 │                      │              │  │
│  │          ▼                 ▼                      ▼              │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │            Product Recommendation Agent                    │  │  │
│  │  └─────────────────────────┬──────────────────────────────────┘  │  │
│  │                            │                                     │  │
│  │                            ▼                                     │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │              Google Gemini 2.5 Flash LLM                   │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────────────┐  │
│  │ Neon Postgres  │  │  FAISS Vector  │  │ Order & Cart Services    │  │
│  │ (60k Products) │  │ (all-MiniLM)   │  │  (JSON & Memory Sync)    │  │
│  └────────────────┘  └────────────────┘  └──────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 3. Frontend Architecture (`frontend/`)

- **Framework:** Next.js 16.2.9 (App Router), React 19, TypeScript 5.x
- **Styling & UI:** Tailwind CSS 4, shadcn/ui, Lucide Icons, Framer Motion
- **State Management:** Zustand 5 with `persist` middleware (`localStorage`)

### Key Zustand Stores (`frontend/src/stores/`)
- `cart.store.ts` (`useCartStore`): Manages cart items, quantity adjustments, line totals, and cart ID. Persisted as `neednow-cart`.
- `chat.store.ts` (`useChatStore`): Manages session ID, message history, current recommendations, and typing indicators. Persisted as `neednow-chat`.
- `emergency.store.ts` (`useEmergencyStore`): Manages urgency status, crisis level, and priority recommendation cards.
- `memory.store.ts` (`useMemoryStore`): Stores user preferences (dietary, brand affinity, budget tier, family size).
- `user.store.ts` (`useUserStore`): Manages active user authentication state and profile information.
- `index.ts`: Unified export hub for all stores and atomic selectors.

### Key Custom Hooks (`frontend/src/hooks/`)
- `useChat.ts`: Main chat hook. Intercepts local action keywords ("add it", "checkout", "cart") before sending queries to backend.
- `useCart.ts`: Integrates cart operations with backend API and local store synchronization.
- `useSpeechRecognition.ts`: Interface to Web Speech API for real-time speech-to-text.
- `useVoice.ts`: Manages voice recording, state transitions, and TTS playback.

### Main App Routes (`frontend/src/app/`)
- `/` - Landing Hero Page with feature badges and quick launcher.
- `/chat` - Conversational shopping UI with message stream, voice button, inline product cards, and recommendation list.
- `/cart` - Interactive shopping cart with subtotal calculation and checkout trigger.
- `/checkout` - Order placement with shipping address form and payment selection (UPI demo, COD, Card).
- `/orders` & `/order-success` - Order history listing and confirmation details.
- `/sustainability` - Environmental impact dashboard with eco-scores and carbon metrics.
- `/recommendations` - Standalone product discovery cards view.

---

## 🐍 4. Backend Architecture (`backend/`)

- **Framework:** FastAPI 0.116.1
- **Runtime:** Python 3.11+
- **ORM & DB:** SQLAlchemy 2.0 (Async) with PostgreSQL (Neon Serverless)
- **Vector Search:** FAISS CPU + `sentence-transformers` (`all-MiniLM-L6-v2`)
- **LLM Integration:** `google-generativeai` SDK (`gemini-2.5-flash`)

### Multi-Agent Pipeline (`backend/app/agents/`)
1. **Supervisor Agent (`supervisor/`):** Coordinates request processing pipeline. Aggregates results from sub-agents and constructs final structured JSON response + conversational message.
2. **Intent Agent (`intent/`):** Classifies user message into categories (product query, cart command, order status, emergency, sustainability, general chat).
3. **Product Agent (`product/`):** Performs semantic search against FAISS index & PostgreSQL database, passes candidates to Gemini for context-aware ranking, rationale generation, and top 4 recommendations.
4. **Urgency Agent (`urgency/`):** Detects emergency or priority needs, calculates urgency score (0-100), and flags immediate needs.
5. **Sustainability Agent (`sustainability/`):** Evaluates product eco-impact, calculates eco-scores based on materials/keywords, and suggests greener alternatives.

### REST API Endpoints Map (`backend/app/api/v1/`)
- `POST /api/v1/chat` — Core chat endpoint running full Supervisor Agent pipeline.
- `GET /api/v1/chat/{session_id}/history` — Retrieves conversation history.
- `POST /api/v1/intent` — Intent classification testing endpoint.
- `POST /api/v1/cart/add`, `/remove`, `GET /cart/{user_id}`, `DELETE /cart/{user_id}` — Cart management.
- `POST /api/v1/orders`, `GET /orders/{user_id}`, `GET /orders/{user_id}/{order_id}` — Order placement and persistence.
- `POST /api/v1/sustainability/analyze`, `GET /sustainability/score/{id}` — Eco report and scoring.
- `POST /api/v1/emergency/analyze` — Crisis/urgency evaluation.
- `POST /api/v1/voice/transcribe` — Audio transcription processing.
- `POST /api/v1/memory/store` — User memory preference storage.

---

## 🧹 5. Cleaned Useless / Legacy Files Log

During codebase audit on branch `Project-Cleanup-Divyansh`, the following redundant/junk files were safely removed:

1. **System Metadata Junk (`.DS_Store`):** Removed from root, `backend/`, `backend/datasets/`, `backend/datasets/products/`, and `frontend/`.
2. **Leftover Backup File (`backend/Procfile.bak`):** Removed stale backup artifact.
3. **Unused Stub File (`frontend/CLAUDE.md`):** Removed 11-byte empty reference file.
4. **Legacy Orphan Store (`frontend/src/store/useRecommendationStore.ts`):** Removed unused store file and empty `frontend/src/store/` directory (all active stores reside in `frontend/src/stores/`).
5. **Duplicate Unpersisted Store Stubs (`frontend/src/stores/useCartStore.ts`, `useChatStore.ts`, `useUserStore.ts`):** Removed leftover pre-refactor stubs that were superseded by `cart.store.ts`, `chat.store.ts`, `user.store.ts`.
6. **Redundant Root Lockfile & Config Fix:** Removed accidental root `package.json`/`package-lock.json` and explicitly configured `turbopack.root` in `frontend/next.config.ts` to silence workspace root warnings.

---

## 🚀 6. Local Quickstart Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Google Gemini API Key

### Backend Setup
```bash
cd backend
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements/requirements.txt
cp .env.example .env
# Set GEMINI_API_KEY in .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
```

### Frontend Setup
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

---

## 🧪 7. Gemini API Key Rotation & Static Counter

### Round-Robin Key Rotation & Fallback:
1. **Static Counter (`_key_counter`):** `GeminiService` maintains a static class-level integer counter (`_key_counter`).
2. **Modulo Arithmetic Indexing:** For each API call attempt (fail or success), the active key index is computed as:
   $$\text{selected\_index} = \text{\_key\_counter} \pmod{N}$$
   where $N$ is the number of available fallback API keys.
3. **Counter Increment:** `_key_counter` is incremented on **every single request attempt** (both success and failure).
4. **Failure Rotation:** If Key $i$ fails (e.g. HTTP 429 rate limit or quota exceeded), `GeminiService` immediately advances `_key_counter` and retries with Key $(i + 1) \pmod N$ in the pool.
5. **Full Fallback:** If all $N$ API keys in the pool fail, `GeminiService` gracefully falls back to mock responses.
6. **Detailed Key Logging:** Emits explicit terminal logs for prompt dispatch and output receipt with the active API Key # number:
   - `📤 PROMPT SENT | API Key #1 of 3 (AIza...1234) | prompt_preview=...`
   - `📥 RESPONSE RECEIVED | API Key #1 of 3 (AIza...1234) | status=SUCCESS | response_chars=340 | preview=...`

### Configuration (`backend/.env`):
Supply multiple API keys as a comma-separated string or list:
```env
GEMINI_API_KEY=key_1_here,key_2_here,key_3_here
```

