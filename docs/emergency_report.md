# Emergency Mode Report — NeedNow AI Frontend

## Summary

Complete emergency mode UI with 4 components + 1 page. Connected to `POST /api/v1/emergency/analyze` and `POST /api/v1/emergency/escalate` via `useEmergency` hook. Zero TypeScript errors.

---

## Architecture

```
app/emergency/page.tsx
    ├── EmergencyInput       (textarea + analyze button)
    ├── QuickActions         (6 one-click emergency scenarios)
    ├── AnalysisResult       (urgency display + actions)
    └── EscalationResult     (workflow confirmation)
```

---

## Components

| Component | File | Features |
|-----------|------|----------|
| **EmergencyInput** | `EmergencyInput.tsx` | Large textarea, red theme, loading state, pulsing submit button |
| **QuickActions** | `QuickActions.tsx` | 6 pre-built emergency scenarios (medicine, baby, first aid, insulin, elderly, breathing) |
| **AnalysisResult** | `AnalysisResult.tsx` | Urgency badge + score bar + explanation + "Get Products" / "Escalate" buttons |
| **EscalationResult** | `EscalationResult.tsx` | Green success card with workflow ID, message, and triggered actions |

---

## Page Flow

```
1. User arrives → sees disclaimer + input + quick actions
2. Types or clicks scenario → POST /emergency/analyze
3. Analysis appears → shows urgency level, score, explanation
4. If emergency → "Get Products" (routes to chat) or "Escalate"
5. Escalate → POST /emergency/escalate → shows workflow confirmation
```

---

## Features

| Feature | Implementation |
|---------|---------------|
| **Emergency selector** | QuickActions with 6 common scenarios |
| **Quick actions** | One-click to analyze pre-built situations |
| **Situation analysis** | Real-time urgency scoring with animated score bar |
| **One-click recommendations** | "Get Products Now" sends to chat pipeline then routes to /chat |
| **Emergency escalation** | Triggers priority workflow, shows actions taken |
| **Disclaimer** | Safety warning about calling 112 for life-threatening emergencies |
| **Visual urgency** | Color-coded everything (green→yellow→orange→red) from constants |
| **Pulse animation** | Emergency button and badge pulse to draw attention |

---

## Backend Endpoints Used

| Endpoint | Trigger |
|----------|---------|
| `POST /api/v1/emergency/analyze` | When user submits or clicks quick action |
| `POST /api/v1/emergency/escalate` | When user clicks "Escalate Emergency" |
| `POST /api/v1/chat` | When user clicks "Get Products Now" (via useChat) |

---

## Urgency Display Config (from constants)

| Level | Color | Delivery | Time |
|-------|-------|----------|------|
| LOW | Green | Standard | 2-3 days |
| MEDIUM | Amber | Same-Day | 4-8 hours |
| HIGH | Orange | Express | 1-2 hours |
| CRITICAL | Red | Emergency | 30 minutes |

---

## TypeScript Verification

```
$ npx tsc --noEmit
Exit code: 0
```
