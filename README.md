<p align="center">
  <img src="https://img.shields.io/badge/Amazon-HackOn%202026-FF9900?style=for-the-badge&logo=amazon&logoColor=white" alt="Amazon HackOn" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.116-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/AWS-Bedrock-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white" alt="AWS Bedrock" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

<h1 align="center">🛒 NeedNow AI</h1>

<p align="center">
  <strong>Situation-to-Cart AI Shopping Assistant</strong><br/>
  Describe your situation. Get exactly what you need. Instantly.
</p>

<p align="center">
  <em>Built for Amazon HackOn 2025 — Multi-Agent AI Pipeline with Urgency Detection, Sustainability Scoring, and Voice Commerce</em>
</p>

---

## Overview

NeedNow AI is an intelligent shopping assistant that converts real-life situations into product recommendations and cart actions through a multi-agent AI pipeline.

Instead of searching for products by keyword, users describe their situation in natural language — "I cut my finger and it won't stop bleeding" — and NeedNow AI instantly:

1. Detects the **intent** and **urgency** level
2. Retrieves **context-relevant products** from a 60,000+ product catalog
3. Scores each product for **sustainability**
4. Adds the top recommendations to the **cart**
5. Triggers **emergency protocols** if the situation is critical

### Problem Being Solved

Traditional e-commerce search requires users to know *what* they need. In urgent or unfamiliar situations, people don't know the right product names — they know their *problem*. NeedNow AI bridges this gap with AI that understands situations and recommends solutions.

### Why It Matters

- **Speed in emergencies** — Critical situations get escalated with appropriate urgency scoring
- **Accuracy** — Multi-agent architecture ensures relevant products, not keyword matches
- **Sustainability** — Every recommendation includes an eco-score and greener alternatives
- **Accessibility** — Voice input support for hands-free commerce
- **Memory** — Learns user preferences over time for increasingly personalized recommendations

---

## Key Features

| Feature                               | Description                                                                                  |
| ------------------------------------- | -------------------------------------------------------------------------------------------- |
| 🤖**AI Chat Assistant**         | Natural language situation input → intelligent product recommendations via supervisor agent |
| 🚨**Emergency Detection**       | Real-time urgency scoring (low/medium/high/critical) with automatic escalation workflows     |
| 🎯**Smart Product Suggestions** | Context-aware retrieval with symptom→keyword mapping across 60,288 products                 |
| 🛒**Cart Management**           | Automatic cart population from chat, manual add/remove, quantity control                     |
| 🌿**Sustainability Insights**   | Eco-scores for every product with greener alternative recommendations                        |
| 🧠**Memory Engine**             | Long-term user preference, behavior, and purchase history tracking                           |
| 🎙️**Voice Commerce**          | Audio transcription → chat pipeline for hands-free shopping                                 |
| 📜**History & Sessions**        | Full conversation history with session management                                            |

---

## Screenshots

> Replace placeholders with actual screenshots after deployment.

| Page            | Preview                                                |
| --------------- | ------------------------------------------------------ |
| Home            | ![Home Page](docs/screenshots/home.png)                  |
| Chat            | ![Chat Page](docs/screenshots/chat.png)                  |
| Recommendations | ![Recommendations](docs/screenshots/recommendations.png) |
| Cart            | ![Cart](docs/screenshots/cart.png)                       |
| Emergency Mode  | ![Emergency](docs/screenshots/emergency.png)             |
| Sustainability  | ![Sustainability](docs/screenshots/sustainability.png)   |
| History         | ![History](docs/screenshots/history.png)                 |

---

## System Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend (Next.js 16 + React 19)"]
        UI[Chat UI / Voice Input]
        Pages[9 Page Routes]
        Stores[Zustand Stores]
        Hooks[Custom Hooks]
    end

    subgraph API["API Layer (FastAPI)"]
        Chat["/api/v1/chat"]
        Cart["/api/v1/cart"]
        Intent["/api/v1/intent"]
        Emergency["/api/v1/emergency"]
        Sustainability["/api/v1/sustainability"]
        Voice["/api/v1/voice"]
        Memory["/api/v1/memory"]
    end

    subgraph Agents["Multi-Agent Pipeline"]
        Supervisor[Supervisor Agent]
        IntentAgent[Intent Agent]
        ProductAgent[Product Agent]
        UrgencyAgent[Urgency Agent]
        SustainAgent[Sustainability Agent]
        EmergencyAgent[Emergency Agent]
    end

    subgraph Storage["Data Layer"]
        PostgreSQL[(PostgreSQL / Neon)]
        FAISS[(FAISS Vector Store)]
        ChromaDB[(ChromaDB Embeddings)]
        MemoryStore[Long-term Memory]
    end

    subgraph AI["AI / ML"]
        Bedrock[AWS Bedrock<br/>Claude 3.5 Sonnet]
        Embeddings[Sentence Transformers<br/>all-MiniLM-L6-v2]
    end

    UI --> Chat
    UI --> Voice
    Pages --> Cart
    Pages --> Emergency
    Pages --> Sustainability
    Pages --> Memory

    Chat --> Supervisor
    Intent --> Supervisor
    Supervisor --> IntentAgent
    Supervisor --> ProductAgent
    Supervisor --> UrgencyAgent
    Supervisor --> SustainAgent
    Emergency --> EmergencyAgent

    IntentAgent --> Bedrock
    ProductAgent --> FAISS
    ProductAgent --> ChromaDB
    UrgencyAgent --> Bedrock
    SustainAgent --> PostgreSQL

    Supervisor --> PostgreSQL
    Cart --> PostgreSQL
    Memory --> MemoryStore
    MemoryStore --> PostgreSQL
```

### Agent Execution Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant S as Supervisor Agent
    participant I as Intent Agent
    participant P as Product Agent
    participant Ur as Urgency Agent
    participant Su as Sustainability Agent
    participant DB as PostgreSQL

    U->>F: "I cut my finger"
    F->>S: POST /api/v1/chat
    S->>I: Classify intent
    I-->>S: intent: first_aid
    S->>Ur: Score urgency
    Ur-->>S: urgency: high (0.8)
    S->>P: Retrieve products (bandage, antiseptic, gauze)
    P->>DB: Vector search + keyword match
    DB-->>P: Top 4 products
    P-->>S: Ranked products
    S->>Su: Score sustainability
    Su-->>S: Eco scores + alternatives
    S-->>F: Complete response
    F-->>U: Product cards + urgency badge + eco info
```

---

## Tech Stack

### Frontend

| Technology   | Version | Purpose                           |
| ------------ | ------- | --------------------------------- |
| Next.js      | 16.2.9  | React framework with App Router   |
| React        | 19.2.4  | UI library                        |
| TypeScript   | 5.x     | Type safety                       |
| Tailwind CSS | 4.x     | Utility-first styling             |
| Zustand      | 5.0.14  | State management with persistence |
| Axios        | 1.17.0  | HTTP client                       |
| Radix UI     | 1.5.0   | Accessible UI primitives          |
| shadcn/ui    | 4.11.0  | Component system                  |
| Lucide React | 1.18.0  | Icons                             |
| CVA          | 0.7.1   | Component variants                |

### Backend

| Technology | Version | Purpose                  |
| ---------- | ------- | ------------------------ |
| FastAPI    | 0.116.1 | Async API framework      |
| Python     | 3.11+   | Runtime                  |
| SQLAlchemy | 2.0.42  | Async ORM                |
| Alembic    | 1.16.4  | Database migrations      |
| Pydantic   | 2.11.7  | Schema validation        |
| FAISS      | 1.11.0  | Vector similarity search |
| Boto3      | 1.40.0  | AWS SDK                  |
| NumPy      | 2.3.1   | Numerical computation    |
| Pandas     | 2.3.1   | Data processing          |
| Uvicorn    | 0.35.0  | ASGI server              |
| Structlog  | 25.4.0  | Structured logging       |
| Tenacity   | 9.1.2   | Retry logic              |

### AI & ML

| Technology                               | Purpose                                                   |
| ---------------------------------------- | --------------------------------------------------------- |
| AWS Bedrock (Claude 3.5 Sonnet)          | LLM for intent classification, reasoning, recommendations |
| FAISS CPU                                | Vector similarity search for product retrieval            |
| Sentence Transformers (all-MiniLM-L6-v2) | Product embedding generation                              |
| ChromaDB                                 | Persistent vector store for embeddings                    |

### Infrastructure

| Technology        | Purpose                   |
| ----------------- | ------------------------- |
| PostgreSQL (Neon) | Primary database with SSL |
|                   |                           |

---

## Project Structure

```
neednow-ai/
├── backend/
│   ├── main.py                          # FastAPI application entry point
│   ├── requirements/
│   │   └── requirements.txt             # Python dependencies
│   ├── migration/
│   │   └── env.py                       # Alembic migration config
│   ├── scripts/
│   │   ├── load_products.py             # Load 60K products from JSONL
│   │   ├── generate_product_embeddings.py
│   │   ├── generate_sustainability_scores.py
│   │   ├── download_dataset.py
│   │   └── verify_datasets.py
│   ├── tests/
│   │   ├── backend/                     # API endpoint tests
│   │   ├── agents/                      # Agent unit tests
│   │   ├── integration/                 # Integration tests
│   │   └── e2e/                         # End-to-end user journeys
│   └── app/
│       ├── agents/
│       │   ├── supervisor/              # Orchestrator agent
│       │   ├── intent/                  # Intent classification
│       │   ├── product/                 # Product retrieval & ranking
│       │   ├── urgency/                 # Urgency scoring
│       │   ├── emergency/               # Emergency escalation
│       │   ├── sustainability/          # Eco scoring
│       │   └── shared/                  # Base agent, tools, memory
│       ├── api/v1/                      # Route handlers
│       ├── core/                        # Config, logging, exceptions, security
│       ├── database/                    # Connection, session, seed
│       ├── dependencies/                # FastAPI dependency injection
│       ├── memory/
│       │   ├── embeddings/              # Memory chunking & retrieval
│       │   ├── long_term/               # Behavior, preference, purchase memory
│       │   └── short_term/              # Session context
│       ├── models/                      # SQLAlchemy ORM models
│       ├── repositories/                # Data access layer
│       ├── schemas/                     # Pydantic request/response schemas
│       ├── services/                    # Business logic services
│       ├── utils/                       # Tokenizer, validators, formatters
│       ├── vectorstore/                 # FAISS manager, index builder, retriever
│       └── workers/                     # Background workers (embedding, sync)
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── app/                         # Next.js App Router pages
│       │   ├── page.tsx                 # Home
│       │   ├── chat/                    # Chat interface
│       │   ├── cart/                    # Shopping cart
│       │   ├── recommendations/         # Product recommendations
│       │   ├── emergency/               # Emergency mode
│       │   ├── sustainability/          # Eco dashboard
│       │   ├── history/                 # Conversation history
│       │   ├── memory/                  # Memory management
│       │   └── profile/                 # User profile
│       ├── components/
│       │   ├── ui/                      # 12 shadcn-patterned components
│       │   ├── chat/                    # ChatWindow, ChatInput, MessageBubble
│       │   ├── cart/                    # ProductCard, CartItemRow, CartSummary
│       │   ├── emergency/               # EmergencyInput, AnalysisResult
│       │   ├── sustainability/          # EcoScoreBadge, EcoAlternativeCard
│       │   ├── voice/                   # VoiceButton, VoicePanel
│       │   ├── shared/                  # EmptyState, LoadingSpinner, Navbar
│       │   └── layout/                  # Header, Footer
│       ├── hooks/                       # useChat, useCart, useVoice, useMemory...
│       ├── stores/                      # Zustand stores (cart, chat, user, memory)
│       ├── services/                    # API service layer
│       ├── features/                    # Feature modules
│       ├── lib/                         # API client, auth, websocket, utils
│       ├── types/                       # TypeScript type definitions
│       ├── constants/                   # App constants, routes, prompts
│       └── styles/                      # Global CSS + animations
│
└── docs/                                # Development reports & documentation
```

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Chat

| Method   | Endpoint                       | Description                                    |
| -------- | ------------------------------ | ---------------------------------------------- |
| `POST` | `/chat`                      | Send message through supervisor agent pipeline |
| `GET`  | `/chat/{session_id}/history` | Retrieve conversation history                  |

### Intent

| Method   | Endpoint    | Description                                        |
| -------- | ----------- | -------------------------------------------------- |
| `POST` | `/intent` | Classify situation and execute full agent pipeline |

### Cart

| Method     | Endpoint            | Description              |
| ---------- | ------------------- | ------------------------ |
| `POST`   | `/cart/add`       | Add product to cart      |
| `POST`   | `/cart/remove`    | Remove product from cart |
| `GET`    | `/cart/{user_id}` | Get user's cart          |
| `DELETE` | `/cart/{user_id}` | Clear entire cart        |

### Memory

| Method     | Endpoint              | Description                               |
| ---------- | --------------------- | ----------------------------------------- |
| `POST`   | `/memory/store`     | Store user memory (preferences, behavior) |
| `GET`    | `/memory/{user_id}` | Retrieve user memory                      |
| `DELETE` | `/memory/{user_id}` | Clear user memory                         |

### Emergency

| Method   | Endpoint                | Description                           |
| -------- | ----------------------- | ------------------------------------- |
| `POST` | `/emergency/analyze`  | Analyze urgency level of a situation  |
| `POST` | `/emergency/escalate` | Trigger emergency escalation workflow |
| `GET`  | `/emergency/health`   | Emergency subsystem health check      |

### Voice

| Method   | Endpoint              | Description                             |
| -------- | --------------------- | --------------------------------------- |
| `POST` | `/voice/transcribe` | Transcribe audio file to text           |
| `POST` | `/voice/chat`       | Audio → transcription → chat pipeline |

### Sustainability

| Method   | Endpoint                               | Description                                 |
| -------- | -------------------------------------- | ------------------------------------------- |
| `POST` | `/sustainability/analyze`            | Generate sustainability report for products |
| `POST` | `/sustainability/recommend`          | Get eco-friendly alternative suggestions    |
| `GET`  | `/sustainability/score/{product_id}` | Get individual product eco-score            |

### Health

| Method  | Endpoint    | Description  |
| ------- | ----------- | ------------ |
| `GET` | `/`       | Service info |
| `GET` | `/health` | Health check |

---

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (or Neon serverless)
- AWS Account (for Bedrock) — optional, mock mode available

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials (see Environment Variables below)
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
```

### Data Pipeline (Optional — required for product recommendations)

```bash
cd backend

# Load products into PostgreSQL
python scripts/load_products.py

# Generate embeddings
python scripts/generate_product_embeddings.py

# Generate sustainability scores
python scripts/generate_sustainability_scores.py

# Verify data
python scripts/verify_datasets.py
```

---

## Environment Variables

### Backend (`backend/.env`)

```env
# Application
APP_NAME=NeedNow AI
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require

# AWS (leave empty for mock mode)
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_MAX_TOKENS=4096

# Vector Store
FAISS_INDEX_PATH=faiss_indexes
VECTOR_TOP_K=20

# Memory
MEMORY_TOP_K=10
SESSION_TTL_MINUTES=60

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]

# Logging
LOG_LEVEL=INFO

# Mock Mode (set to true to run without AWS credentials)
USE_MOCK_LLM=true
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Running Locally

### Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### Start Frontend

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:3000`.

### Run Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

324 tests across unit, integration, and end-to-end suites.

---

## Demo Workflow

### End-to-End User Flow

```
User: "I cut my finger and it's bleeding badly"
                    │
                    ▼
         ┌─────────────────┐
         │  Intent Agent    │ → Detects: first_aid
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Urgency Agent   │ → Score: 0.85 (HIGH)
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Product Agent   │ → Searches: bandage, antiseptic,
         │                  │   gauze, medical tape, cotton
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Sustainability  │ → Eco-scores each product,
         │  Agent           │   suggests biodegradable alternatives
         └────────┬────────┘
                  │
                  ▼
    ┌──────────────────────────┐
    │  Response to User         │
    │  • 4 relevant products    │
    │  • Urgency: HIGH badge    │
    │  • Eco alternatives shown │
    │  • Added to cart          │
    └──────────────────────────┘
```

### Supported Situation Categories

| Situation             | Intent      | Products Retrieved                            |
| --------------------- | ----------- | --------------------------------------------- |
| "Cut on finger"       | first_aid   | Bandages, antiseptic, gauze, medical tape     |
| "Severe headache"     | pain_relief | Paracetamol, ibuprofen, pain balm             |
| "Cold and cough"      | cold_flu    | Tissues, steam inhaler, lozenges, cough syrup |
| "Fever won't go down" | fever       | Thermometer, ORS, paracetamol, ice packs      |
| "Stomach ache"        | digestive   | Antacid, probiotics, electrolyte powder       |
| "Skin rash"           | skin_care   | Calamine lotion, antihistamine, moisturizer   |

---

## Challenges Solved

1. **Relevance over keyword matching** — All 60,288 products are in a single category ("Health & Personal Care"). We built a symptom→keyword mapping engine with 27 patterns to ensure context-relevant retrieval instead of random category matches.
2. **Graceful degradation without AWS** — Mock LLM mode (`USE_MOCK_LLM=true`) allows full development and testing without Bedrock credentials, with intelligent fallback responses.
3. **Multi-agent coordination** — The Supervisor agent orchestrates 5 specialized sub-agents (Intent, Product, Urgency, Sustainability, Emergency) with graceful fallbacks when any agent fails.
4. **Real-time urgency scoring** — Rule-based + LLM-enhanced urgency detection that can trigger emergency escalation workflows for critical situations.
5. **Sustainability at scale** — Pre-computed eco-scores for all products with real-time alternative recommendations.

---

## Future Improvements

- [ ] Real-time WebSocket for streaming chat responses
- [ ] Multi-language support (Hindi, Tamil, Telugu)
- [ ] Integration with Amazon Pay for checkout
- [ ] Order tracking and delivery estimation
- [ ] Collaborative filtering for recommendations
- [ ] PWA support for mobile
- [ ] Push notifications for emergency situations
- [ ] A/B testing framework for recommendation algorithms

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ for <strong>Amazon HackOn 2026</strong>
</p>
