<p align="center">
  <img src="https://img.shields.io/badge/Amazon-HackOn%202026-FF9900?style=for-the-badge&logo=amazon&logoColor=white" alt="Amazon HackOn" />
  <img src="https://img.shields.io/badge/Google-Gemini%202.5-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google Gemini" />
  <img src="https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.116-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

<h1 align="center">🛒 NeedNow AI</h1>

<p align="center">
  <strong>AI-Powered Conversational Commerce Platform</strong><br/>
  Discover, compare, and order products through chat and voice — powered by Google Gemini.
</p>

---

## 📋 Overview

**NeedNow AI** is an AI-powered conversational commerce platform that helps users discover, compare, and order products through chat and voice interactions while promoting sustainable alternatives.

Instead of traditional search-and-browse shopping, users simply describe what they need in natural language:

> *"I need eco-friendly shampoo"*

And NeedNow AI responds conversationally:

> *"I found 3 eco-friendly shampoos. My top recommendation is **Himalaya Anti-Hair Fall Shampoo** for ₹249. Would you like me to add it to your cart?"*

The platform handles the entire journey from discovery to checkout through a single conversational interface.

---

## ✨ Features

| Feature                                 | Description                                                                                                   |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 🤖**Gemini AI Integration**       | Google Gemini 2.5 Flash powers intent detection, product recommendations, and conversational responses        |
| 💬**Conversational Commerce**     | Natural language shopping — describe your needs, get recommendations, add to cart, and checkout through chat |
| 🎙️**Voice Commerce**            | Web Speech API for voice input + Speech Synthesis for voice responses — hands-free shopping                  |
| 🎯**Smart Recommendations**       | Context-aware product suggestions with relevance scoring and purchase rationale                               |
| 🧠**Context-Aware Assistant**     | Maintains conversation state — "add it" refers to the last recommended product                               |
| 🛒**Cart Management**             | Full cart with quantity controls, order summary, and real-time updates                                        |
| 💳**Checkout Flow**               | Complete checkout with address form, payment selection (COD/UPI/Card), and UPI demo mode                      |
| 📦**Order Management**            | Persistent orders that survive refresh, order history, and order details                                      |
| 🌿**Sustainability Dashboard**    | Eco-scores for products based on title keyword analysis                                                       |
| ♻️**Eco-Friendly Alternatives** | Genuinely greener product suggestions (only shown when score improvement ≥ 8 points)                         |
| 🌍**Carbon Impact Insights**      | Title-based carbon footprint estimation comparing original vs alternative products                            |
| 🚨**Emergency Detection**         | Urgency scoring for critical situations with priority product selection                                       |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│              (Chat Input / Voice / Microphone)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 16)                          │
│  ┌──────────┐  ┌───────────┐  ┌─────────┐  ┌────────────────┐  │
│  │ Chat UI  │  │ Voice I/O │  │  Cart   │  │ Checkout/Orders│  │
│  └────┬─────┘  └─────┬─────┘  └────┬────┘  └───────┬────────┘  │
│       │               │             │               │            │
│  ┌────┴───────────────┴─────────────┴───────────────┴────────┐  │
│  │          Action Command Detector (useChat)                 │  │
│  │  "add it" → local action  |  "find X" → backend search    │  │
│  └────────────────────────────┬──────────────────────────────┘  │
└───────────────────────────────┼─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              SUPERVISOR AGENT (Orchestrator)               │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │   │
│  │  │  Intent  │  │ Urgency  │  │ Product  │  │  Sustain│ │   │
│  │  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent  │ │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │   │
│  │       │              │             │              │       │   │
│  │       ▼              ▼             ▼              ▼       │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │            Google Gemini 2.5 Flash                   │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │PostgreSQL│  │  FAISS   │  │  Orders  │  │ Cart Service │   │
│  │  (Neon)  │  │  Vector  │  │(Persisted)│  │ (Demo Mode) │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Conversational Flow

```
User: "Order eco shampoo"
  → Gemini: Intent Detection (category, urgency, keywords)
  → Gemini: Product Recommendation (top 4 from 60K+ catalog)
  → Gemini: Conversational Response Generation
  → Frontend: Display products + action buttons

User: "Add it" (no backend call — uses stored context)
  → Frontend: Adds top product to cart locally
  → Shows: ✅ Added to cart + [View Cart] [Checkout]

User: "Checkout"
  → Frontend: Navigates to /checkout (no backend call)
  → User fills address → selects payment → places order
```

---

## 🛠️ Tech Stack

### Frontend

| Technology       | Version | Purpose                                        |
| ---------------- | ------- | ---------------------------------------------- |
| Next.js          | 16.2.9  | React framework with App Router                |
| React            | 19.2.4  | UI library                                     |
| TypeScript       | 5.x     | Type safety                                    |
| Tailwind CSS     | 4.x     | Utility-first styling                          |
| Zustand          | 5.0.14  | State management with localStorage persistence |
| shadcn/ui        | 4.11.0  | Component system (CVA + Radix)                 |
| Axios            | 1.17.0  | HTTP client                                    |
| Web Speech API   | —      | Voice input (SpeechRecognition)                |
| Speech Synthesis | —      | Voice output (TTS)                             |

### Backend

| Technology          | Version | Purpose                  |
| ------------------- | ------- | ------------------------ |
| FastAPI             | 0.116.1 | Async API framework      |
| Python              | 3.11+   | Runtime                  |
| SQLAlchemy          | 2.0.42  | Async ORM                |
| Pydantic            | 2.11.7  | Schema validation        |
| FAISS               | 1.11.0  | Vector similarity search |
| google-generativeai | 0.8.5   | Gemini SDK               |

### AI / ML

| Technology              | Purpose                                                                  |
| ----------------------- | ------------------------------------------------------------------------ |
| Google Gemini 2.5 Flash | Intent classification, product recommendations, conversational responses |
| FAISS CPU               | Vector similarity search for product retrieval                           |
| Sentence Transformers   | Product embedding generation (all-MiniLM-L6-v2)                          |

### Database

| Technology        | Purpose                                 |
| ----------------- | --------------------------------------- |
| PostgreSQL (Neon) | Primary database (60,288 products)      |
| JSON file storage | Order persistence (survives restart)    |
| localStorage      | Frontend state persistence (cart, chat) |

---

## 📂 Project Structure

```
neednow-ai/
├── backend/
│   ├── main.py                         # FastAPI entry point
│   ├── app/
│   │   ├── agents/
│   │   │   ├── supervisor/             # Orchestrator + conversation builder
│   │   │   ├── intent/                 # Gemini intent classification
│   │   │   ├── product/                # Gemini product recommendations
│   │   │   ├── urgency/                # Gemini urgency scoring
│   │   │   ├── sustainability/         # Eco scoring + alternatives
│   │   │   └── shared/                 # Base agent, tools
│   │   ├── api/v1/                     # REST endpoints
│   │   ├── services/                   # Business logic (Gemini, Cart, Order)
│   │   ├── models/                     # SQLAlchemy ORM
│   │   ├── schemas/                    # Pydantic request/response
│   │   └── core/                       # Config, logging, security
│   ├── tests/                          # 324 tests (unit + integration + e2e)
│   └── scripts/                        # Data pipeline scripts
│
├── frontend/
│   └── src/
│       ├── app/                        # 15 pages (Next.js App Router)
│       │   ├── chat/                   # AI chat interface
│       │   ├── cart/                   # Shopping cart
│       │   ├── checkout/              # Checkout flow
│       │   ├── order-success/         # Order confirmation
│       │   ├── orders/                # Order history
│       │   ├── recommendations/       # Product recommendations
│       │   └── sustainability/        # Eco dashboard
│       ├── components/
│       │   ├── chat/                   # ChatWindow, ChatInput, ProductCards
│       │   ├── cart/                   # ProductCard, CartSummary
│       │   └── ui/                    # 12 shadcn components
│       ├── hooks/                      # useChat, useCart, useSpeechRecognition
│       ├── stores/                     # Zustand (cart, chat, user)
│       └── services/                   # API layer
│
└── docs/                               # Development reports
```

---

## 🔌 API Endpoints

All endpoints prefixed with `/api/v1`.

### Chat

| Method   | Path                           | Description                          |
| -------- | ------------------------------ | ------------------------------------ |
| `POST` | `/chat`                      | Send message through Gemini pipeline |
| `GET`  | `/chat/{session_id}/history` | Get conversation history             |

### Cart

| Method     | Path                | Description              |
| ---------- | ------------------- | ------------------------ |
| `POST`   | `/cart/add`       | Add product to cart      |
| `POST`   | `/cart/remove`    | Remove product from cart |
| `GET`    | `/cart/{user_id}` | Get cart contents        |
| `DELETE` | `/cart/{user_id}` | Clear cart               |

### Orders

| Method   | Path                             | Description       |
| -------- | -------------------------------- | ----------------- |
| `POST` | `/orders`                      | Place a new order |
| `GET`  | `/orders/{user_id}`            | Get order history |
| `GET`  | `/orders/{user_id}/{order_id}` | Get order details |

### Other

| Method   | Path                           | Description              |
| -------- | ------------------------------ | ------------------------ |
| `POST` | `/intent`                    | Full supervisor pipeline |
| `POST` | `/emergency/analyze`         | Urgency analysis         |
| `POST` | `/sustainability/analyze`    | Eco report               |
| `GET`  | `/sustainability/score/{id}` | Product eco score        |
| `POST` | `/voice/transcribe`          | Audio transcription      |
| `POST` | `/memory/store`              | Store user memory        |

---

## 🚀 Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (or Neon serverless)
- Google AI API Key ([get one here](https://aistudio.google.com/apikey))

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements/requirements.txt
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

---

## 🔐 Environment Variables

### Backend (`backend/.env`)

```env
# Application
APP_NAME=NeedNow AI
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_ID=gemini-2.5-flash
GEMINI_MAX_TOKENS=4096

# Mode
USE_MOCK_LLM=false

# Other
FAISS_INDEX_PATH=faiss_indexes
LOG_LEVEL=INFO
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 📱 Screens & Features

| Screen                      | Description                                                                            |
| --------------------------- | -------------------------------------------------------------------------------------- |
| 💬**AI Chat**         | Conversational interface with inline product cards, voice input/output, action buttons |
| 🎙️**Voice Search**  | Microphone button with listening animation, auto-submit, TTS responses                 |
| 🎯**Recommendations** | Top 4 products with relevance scores, reasons, eco badges                              |
| 🛒**Cart**            | Quantity +/-, order summary (subtotal + delivery + tax), proceed to checkout           |
| 💳**Checkout**        | Address form, payment methods (COD/UPI/Card), UPI QR demo                              |
| 📦**Orders**          | Order history with status, persistent across refresh                                   |
| 🌿**Sustainability**  | Eco-score dashboard, carbon savings, greener alternatives                              |

---

## 🔮 Future Improvements

- [ ] Real payment gateway integration (Razorpay/Stripe)
- [ ] Delivery tracking with live updates
- [ ] User authentication (Google/Phone OTP)
- [ ] Personalized recommendations from purchase history
- [ ] Advanced sustainability metrics (lifecycle analysis)
- [ ] Multi-language support (Hindi, Tamil, Telugu)
- [ ] PWA for mobile with push notifications
- [ ] Product image search via camera

---

## 🏆 Hackathon Highlights

| Feature                    | Status                       |
| -------------------------- | ---------------------------- |
| ✅ Google Gemini 2.5 Flash | Live AI integration          |
| ✅ Voice Commerce          | Web Speech API + TTS         |
| ✅ Conversational Shopping | Context-aware commands       |
| ✅ Sustainability Focus    | Eco-scores + carbon insights |
| ✅ Smart Recommendations   | Gemini-powered with reasons  |
| ✅ Order Management        | Persistent + full flow       |
| ✅ 324 Backend Tests       | Unit + Integration + E2E     |
| ✅ 15 Frontend Pages       | TypeScript strict, 0 errors  |
| ✅ 60,288 Products         | Real Amazon dataset          |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.

---

<p align="center">
  Built with ❤️ for <strong>Amazon HackOn 2026</strong>
</p>
