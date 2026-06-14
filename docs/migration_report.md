# AWS Bedrock Dependency — Migration Report

## Audit Date: June 14, 2026

## Summary

The NeedNow AI codebase uses **AWS Bedrock** for two AI capabilities:
1. **LLM inference** (Claude 3.5 Sonnet) — intent classification, urgency scoring, reasoning
2. **Text embeddings** (Amazon Titan Embed v2) — product vector search

Additionally, **AWS Transcribe** + **S3** are used for voice transcription.

All three services have a **mock mode** (`USE_MOCK_LLM=true`) that allows full operation without AWS credentials.

---

## Python Dependencies

| Package | Version | Purpose | File |
|---------|---------|---------|------|
| `boto3` | 1.40.0 | AWS SDK (Bedrock, S3, Transcribe) | `backend/requirements/requirements.txt` |
| `botocore` | 1.40.0 | boto3 core dependency | `backend/requirements/requirements.txt` |

---

## AWS Services Used

| Service | API Call | Model ID | Purpose |
|---------|----------|----------|---------|
| Bedrock Runtime | `invoke_model()` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | LLM inference |
| Bedrock Runtime | `invoke_model()` | `amazon.titan-embed-text-v2:0` | Text embeddings |
| Transcribe | `start_transcription_job()` | — | Voice-to-text |
| S3 | `put_object()` | — | Audio file storage for Transcribe |

---

## Backend Files with AWS Bedrock Dependencies

### 1. Core LLM Service

| File | Class/Function | Current Model | Usage | Replacement Required |
|------|----------------|---------------|-------|---------------------|
| `backend/app/services/bedrock_service.py` | `BedrockService.__init__()` | — | Creates `boto3.client("bedrock-runtime")` | Yes — replace with new LLM provider client |
| `backend/app/services/bedrock_service.py` | `BedrockService._invoke_bedrock()` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Calls `invoke_model()` with Claude Messages API format (`anthropic_version: bedrock-2023-05-31`) | Yes — replace with new LLM API call |
| `backend/app/services/bedrock_service.py` | `BedrockService._mock_response()` | — | Mock fallback (no AWS dependency) | No change needed |

### 2. Product Embedding Service

| File | Class/Function | Current Model | Usage | Replacement Required |
|------|----------------|---------------|-------|---------------------|
| `backend/app/agents/product/embedding_service.py` | `EmbeddingService.__init__()` | — | Creates `boto3.client("bedrock-runtime")` | Yes — replace with new embedding provider |
| `backend/app/agents/product/embedding_service.py` | `EmbeddingService.generate_embedding()` | `amazon.titan-embed-text-v2:0` | Calls `invoke_model()` with `{"inputText": text}` body | Yes — replace with new embedding API |
| `backend/app/agents/product/embedding_service.py` | `EmbeddingService._mock_embedding()` | — | Deterministic hash-based mock (no AWS) | No change needed |

### 3. Voice Service (AWS Transcribe + S3)

| File | Class/Function | Current Model | Usage | Replacement Required |
|------|----------------|---------------|-------|---------------------|
| `backend/app/services/voice_service.py` | `VoiceService.__init__()` | — | Creates `boto3.client("transcribe")` + `boto3.client("s3")` | Yes — replace with new STT provider |
| `backend/app/services/voice_service.py` | `VoiceService._transcribe_audio_content()` | — | Uploads audio to S3, starts Transcribe job | Yes — replace with new transcription API |
| `backend/app/services/voice_service.py` | `VoiceService._poll_transcription_job()` | — | Polls Transcribe job status | Yes — replace with synchronous STT API |

### 4. Agent Consumers (import BedrockService)

These files **instantiate** or **receive** `BedrockService` — they don't call AWS directly, but depend on its interface (`invoke(system_prompt, user_prompt) → str`).

| File | Class/Function | Usage | Replacement Required |
|------|----------------|-------|---------------------|
| `backend/app/agents/intent/agent.py` | `IntentAgent.__init__(bedrock_service)` | Stores reference, calls `self.bedrock.invoke()` | Interface-compatible — no change if new service keeps same `invoke()` signature |
| `backend/app/agents/urgency/agent.py` | `UrgencyAgent.__init__(bedrock_service)` | Stores reference, calls `self.bedrock.invoke()` | Same as above |
| `backend/app/agents/shared/base_agent.py` | `BaseAgent.__init__(bedrock_service)` | Optional injection, calls `self._bedrock.invoke()` via `invoke_bedrock()` helper | Same as above |
| `backend/app/services/recommendation_service.py` | `RecommendationService.__init__(bedrock_service)` | Stores reference for future use | Same as above |
| `backend/app/dependencies/supervisor.py` | `get_supervisor()` | Creates `BedrockService()`, passes to IntentAgent + UrgencyAgent | Change constructor call |
| `backend/app/dependencies/emergency.py` | `get_emergency_service()` | Creates `BedrockService()`, passes to UrgencyAgent | Change constructor call |

### 5. Configuration / Settings

| File | Variable | Current Value | Replacement Required |
|------|----------|---------------|---------------------|
| `backend/app/core/settings.py` | `BEDROCK_MODEL_ID` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Yes — update to new model ID |
| `backend/app/core/settings.py` | `BEDROCK_MAX_TOKENS` | `4096` | Update to new model's token limit |
| `backend/app/core/settings.py` | `AWS_REGION` | `ap-south-1` | Remove or repurpose |
| `backend/app/core/config.py` | `AWS_ACCESS_KEY_ID` | `None` | Remove or repurpose |
| `backend/app/core/config.py` | `AWS_SECRET_ACCESS_KEY` | `None` | Remove or repurpose |
| `backend/app/core/config.py` | `AWS_REGION` | `us-east-1` | Remove or repurpose |
| `backend/app/core/config.py` | `OPENAI_API_KEY` | `None` | May need if switching to OpenAI |
| `backend/.env` | `BEDROCK_MODEL_ID` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Update |
| `backend/.env` | `AWS_REGION` | `ap-south-1` | Update or remove |
| `backend/.env` | `AWS_ACCESS_KEY_ID` | (empty) | Update or remove |
| `backend/.env` | `AWS_SECRET_ACCESS_KEY` | (empty) | Update or remove |
| `backend/.env.example` | Same as above | Placeholder values | Update |

### 6. Tokenizer / Context Window Management

| File | Variable/Function | Current Value | Replacement Required |
|------|-------------------|---------------|---------------------|
| `backend/app/utils/tokenizer.py` | `MODEL_CONTEXT_WINDOWS` dict | Contains Claude model context windows (`anthropic.claude-3-sonnet: 200_000`, etc.) + Titan models | Yes — update context window values for new model |
| `backend/app/utils/tokenizer.py` | `TextTokenizer.__init__()` | Default `model_id="anthropic.claude-3-sonnet"` | Yes — update default model ID |
| `backend/app/utils/tokenizer.py` | `DEFAULT_CHARS_PER_TOKEN` | `3.8` (calibrated for Claude) | May need adjustment for new model |

### 7. Memory Embeddings Module

| File | Class/Function | Current Model | Replacement Required |
|------|----------------|---------------|---------------------|
| `backend/app/memory/embeddings/embedder.py` | `Embedder.__init__()` | Default `model_id="amazon.titan-embed-text-v2:0"` | Yes — update default model ID |
| `backend/app/memory/embeddings/embedder.py` | `Embedder.embed()` | Uses pluggable `embedding_fn` (no direct AWS call) | No — if `embedding_fn` is swapped |
| `backend/app/memory/embeddings/embedder.py` | `Embedder._fallback_embed()` | Hash-based mock (no AWS) | No change needed |

---

## Frontend Files with Bedrock References

| File | Variable/Constant | Current Value | Replacement Required |
|------|-------------------|---------------|---------------------|
| `frontend/src/lib/bedrock.ts` | `BEDROCK_MODELS.CLAUDE_SONNET` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Yes — update model ID |
| `frontend/src/lib/bedrock.ts` | `BEDROCK_MODELS.TITAN_EMBED` | `amazon.titan-embed-text-v2:0` | Yes — update model ID |
| `frontend/src/lib/bedrock.ts` | `BEDROCK_MAX_TOKENS` | `4096` | Update if new model differs |
| `frontend/src/lib/bedrock.ts` | `consumeBedrockStream()` | SSE streaming consumer | Rename function (logic is provider-agnostic) |
| `frontend/src/constants/agent-config.ts` | `MODEL_CONFIG.LLM.provider` | `"Amazon Bedrock"` | Yes — update display text |
| `frontend/src/constants/agent-config.ts` | `MODEL_CONFIG.LLM.model` | `"Claude 3.5 Sonnet"` | Yes — update display text |
| `frontend/src/constants/agent-config.ts` | `MODEL_CONFIG.LLM.modelId` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Yes — update model ID |
| `frontend/src/app/layout.tsx` | Metadata description | `"...powered by Amazon Bedrock."` | Yes — update text |
| `frontend/src/components/shared/Footer.tsx` | Attribution text | `"Powered by Amazon Bedrock • HackOn 6.0"` | Yes — update text |
| `frontend/src/components/layout/Footer.tsx` | Attribution text | `"Powered by Amazon Bedrock • HackOn 6.0"` | Yes — update text |

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    Environment Variables                      │
│  BEDROCK_MODEL_ID, AWS_REGION, AWS_ACCESS_KEY_ID, etc.      │
└───────────┬─────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────┐
│  app/core/settings.py │ ← Loads from .env
└───────────┬───────────┘
            │
            ▼
┌───────────────────────────────────┐
│  app/services/bedrock_service.py  │ ← boto3.client("bedrock-runtime")
│  BedrockService.invoke()          │     invoke_model(modelId=..., body=...)
└───────┬───────────────────────────┘
        │
        ├──────────────────────┬────────────────────────┐
        ▼                      ▼                        ▼
┌───────────────┐    ┌─────────────────┐    ┌───────────────────────┐
│  IntentAgent  │    │  UrgencyAgent   │    │ RecommendationService │
│  .invoke()    │    │  .invoke()      │    │ (stores reference)    │
└───────────────┘    └─────────────────┘    └───────────────────────┘

┌───────────────────────────────────────────┐
│  app/agents/product/embedding_service.py  │ ← boto3.client("bedrock-runtime")
│  EmbeddingService.generate_embedding()    │     invoke_model("amazon.titan-embed-text-v2:0")
└───────────────────────────────────────────┘

┌───────────────────────────────────┐
│  app/services/voice_service.py    │ ← boto3.client("transcribe") + boto3.client("s3")
│  VoiceService._transcribe_audio() │     start_transcription_job() / put_object()
└───────────────────────────────────┘
```

---

## Migration Scope Summary

| Category | Files | Direct boto3 Calls | Interface-Only Consumers |
|----------|-------|-------------------|------------------------|
| LLM (Claude) | 1 | 1 (`bedrock_service.py`) | 6 (agents, dependencies, recommendation) |
| Embeddings (Titan) | 1 | 1 (`embedding_service.py`) | 1 (`embedder.py`) |
| Voice (Transcribe+S3) | 1 | 1 (`voice_service.py`) | 0 |
| Configuration | 4 | — | — |
| Frontend (display only) | 4 | — | — |
| **Total** | **12** | **3** | **7** |

### Minimum files to modify for full migration: **3 core + 4 config + 4 frontend display = 11 files**

The architecture is well-isolated: only 3 files make actual `boto3` API calls. The rest consume a `BedrockService.invoke(system_prompt, user_prompt) → str` interface. If the replacement maintains the same `invoke()` signature, only the 3 core service files and config need modification.

---

## Recommended Migration Strategy

1. **Replace `BedrockService`** — Swap the boto3 `invoke_model()` call with the new LLM provider's API. Keep the same public interface: `invoke(system_prompt: str, user_prompt: str) → str`.

2. **Replace `EmbeddingService`** — Swap Titan Embed call with new embedding provider (OpenAI, Cohere, or local model like all-MiniLM-L6-v2 which is already used for ChromaDB).

3. **Replace `VoiceService` transcription** — Swap AWS Transcribe with a synchronous STT service (Whisper API, Deepgram, or local Whisper).

4. **Update settings/config** — Remove or rename `BEDROCK_*` variables, add new provider variables.

5. **Update frontend constants** — Change model display names and IDs in `agent-config.ts`, `bedrock.ts`, and footer text.

6. **Remove boto3** from `requirements.txt` (unless other AWS services are retained).
