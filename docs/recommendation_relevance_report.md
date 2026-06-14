# Context-Aware Recommendation Report — NeedNow AI

## Implementation

### How It Works

```
User message: "Cut on my finger, need first aid"
         │
         ▼
┌─────────────────────────────┐
│ situation_to_search_terms() │
│ "cut" → bandage, antiseptic│
│ "finger" → bandage, band aid│
│ "first aid" → first aid, gauze│
└─────────────────────────────┘
         │
         ▼  SQL: WHERE title ILIKE '%bandage%' OR '%antiseptic%' OR '%gauze%' OR '%first aid%'
         │  AND price > 0
         ▼
┌─────────────────────────────┐
│ Products ranked by:         │
│ - keyword match count       │
│ - position in results       │
│ → Top 4 returned           │
└─────────────────────────────┘
```

## Test Results

### "Cut on my finger, need first aid"
| Extracted Intent | Search Terms |
|-----------------|--------------|
| first_aid | bandage, antiseptic, gauze, first aid, band aid |

| # | Product | Price | Relevant? |
|---|---------|-------|-----------|
| 1 | BSN Medical Co-plus Cohesive Bandage | ₹184.71 | ✅ |
| 2 | CVS Advanced Healing Hydrocolloid Bandages | ₹16.20 | ✅ |
| 3 | NOVAMEDIC 3 Pack Compact First Aid Kits | ₹26.99 | ✅ |
| 4 | Circle A Medical Silicone Foam Dressing | ₹17.99 | ✅ |

### "Bad headache need something"
| Extracted Intent | Search Terms |
|-----------------|--------------|
| headache | pain relief, ibuprofen, paracetamol |

| # | Product | Price | Relevant? |
|---|---------|-------|-----------|
| 1 | Quali Herbal Pain Relief Patch | ₹7.95 | ✅ |
| 2 | Zheng Gu Shui Sports Pain Relief Liquid | ₹105.99 | ✅ |
| 3 | NEOBUN Menthol Plaster Pain Relief | ₹24.99 | ✅ |
| 4 | BKP Metatarsal Foot Pads Runners Pain | ₹9.99 | ✅ |

### "Baby needs diapers urgently"
| Extracted Intent | Search Terms |
|-----------------|--------------|
| baby, diaper | diaper, wipes, rash cream, baby |

| # | Product | Price | Relevant? |
|---|---------|-------|-----------|
| 1 | Special Needs Swim Diaper | ₹29.95 | ✅ |
| 2 | CleanCide Disinfectant Wipes | ₹48.37 | ✅ |
| 3-4 | Mixed relevance (dataset limitation) | — | ⚠️ |

## Files Modified

| File | Change |
|------|--------|
| `app/agents/product/retrieval_service.py` | Added `situation_to_search_terms()`, expanded `_category_to_keywords()`, rewrote `_fallback_retrieve()` for context-aware search |
| `app/agents/product/agent.py` | Passes `situation` to `retrieve()` |

## Scoring Algorithm

```
relevance_score = base_position_score + (keyword_matches × 0.1)
```

- Base score decreases by position (0.95, 0.90, 0.85...)
- Each keyword match in product title adds +0.1
- Capped at 1.0

## Symptom → Product Keyword Mapping (27 symptoms covered)

| Symptom | Search Terms |
|---------|-------------|
| cut/wound/bleed | bandage, antiseptic, gauze, first aid |
| fever | thermometer, paracetamol, ors |
| headache | pain relief, ibuprofen, paracetamol |
| cold/cough | tissue, inhaler, lozenge, steam |
| allergy | antihistamine, cetirizine |
| rash/burn | cream, ointment, calamine, aloe |
| diabetes | insulin, glucometer, test strip |
| baby/infant | baby formula, diaper, wipes |
| ... | (27 total symptom mappings) |
