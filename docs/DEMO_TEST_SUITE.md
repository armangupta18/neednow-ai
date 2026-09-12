# NeedNow AI — Demo Test Suite

## System Behavior Reference

- **Product catalog**: 60,288 Health & Personal Care products
- **AI model**: Google Gemini 2.5 Flash (mock fallback when quota exceeded)
- **Max recommendations**: 4 products per request
- **Intent categories**: medical, personal_care, baby, groceries, cleaning, party, other
- **Urgency levels**: LOW (0–39), MEDIUM (40–69), HIGH (70–89), CRITICAL (90–100)
- **Demo user ID**: `550e8400-e29b-41d4-a716-446655440000`

---

## 15 Test Cases

---

### TC-01: First Aid Emergency

| Field | Value |
|-------|-------|
| **User Input** | `"I cut my finger and it's bleeding badly"` |
| **Expected Intent** | `first_aid` |
| **Expected Category** | `medical` |
| **Expected Urgency** | `CRITICAL` (score: 90–100) |
| **Expected Keywords** | bandage, antiseptic, gauze, cotton, first aid |
| **Expected Products** | Bandage packs, antiseptic solutions, gauze rolls, medical tape |
| **Expected Cart** | Auto-populated with top 4 first-aid products |
| **Expected AI Response** | "I understand this is urgent! I found products that can help right away. My top recommendation is **[Bandage Product]** for ₹[price]..." |
| **Cart Action** | User says "Add it" → adds top bandage product without new search |
| **Eco Alternative** | May show biodegradable cotton alternative if available |

---

### TC-02: Baby Care Urgent

| Field | Value |
|-------|-------|
| **User Input** | `"My baby needs diapers and formula urgently"` |
| **Expected Intent** | `baby_care` |
| **Expected Category** | `baby` |
| **Expected Urgency** | `HIGH` (score: 70–89) |
| **Expected Keywords** | baby formula, diapers, baby wipes, baby powder |
| **Expected Products** | Baby formula, diapers, baby wipes |
| **Expected Cart** | 4 baby care products |
| **Expected AI Response** | "I found X products for you. My top recommendation is **[Baby Product]** for ₹[price]. Would you like me to add it to your cart?" |
| **Cart Action** | "Yes, add it" → adds formula to cart |
| **Eco Alternative** | May show organic baby products |

---

### TC-03: Headache / Pain Relief

| Field | Value |
|-------|-------|
| **User Input** | `"I have a severe headache and need pain relief"` |
| **Expected Intent** | `pain_relief` |
| **Expected Category** | `medical` |
| **Expected Urgency** | `MEDIUM` to `HIGH` (score: 50–80) |
| **Expected Keywords** | paracetamol, ibuprofen, pain balm, headache relief |
| **Expected Products** | Pain relief tablets, headache balm, aspirin |
| **Expected Cart** | 4 pain relief products |
| **Expected AI Response** | "I found X products for pain relief. My top recommendation is **[Pain Med]** for ₹[price]..." |
| **Cart Action** | Tap "Add to Cart" on product card |
| **Voice Flow** | Say "Add first one" → adds top product |

---

### TC-04: Cold and Flu Relief

| Field | Value |
|-------|-------|
| **User Input** | `"I have a cold and cough, need something urgently"` |
| **Expected Intent** | `cold_flu_relief` |
| **Expected Category** | `medical` |
| **Expected Urgency** | `HIGH` (score: 70–85) |
| **Expected Keywords** | cough syrup, tissues, steam inhaler, lozenges, vicks |
| **Expected Products** | Cough syrup, tissues, nasal spray, lozenges |
| **Expected Cart** | 4 cold & flu products |
| **Expected AI Response** | "I found products for cold and cough relief..." |
| **Cart Action** | "Add all" → adds all 4 products |
| **Context Test** | Follow up: "Add the cough syrup" → uses stored product list |

---

### TC-05: Personal Care — Shampoo

| Field | Value |
|-------|-------|
| **User Input** | `"Looking for eco-friendly shampoo for dry hair"` |
| **Expected Intent** | `personal_care` |
| **Expected Category** | `personal_care` |
| **Expected Urgency** | `LOW` (score: 10–40) |
| **Expected Keywords** | shampoo, dry hair, organic, natural, conditioner |
| **Expected Products** | Shampoos with natural/organic ingredients |
| **Expected Cart** | 4 shampoo products |
| **Expected AI Response** | "I found X shampoos for you. My top recommendation is **[Shampoo Name]** for ₹[price]..." |
| **Eco Alternative** | High probability (eco keywords match sustainability score) |
| **Cart Action** | Tap "Buy Now" → adds to cart + goes to checkout |

---

### TC-06: Toothpaste & Oral Care

| Field | Value |
|-------|-------|
| **User Input** | `"I need toothpaste and mouthwash"` |
| **Expected Intent** | `personal_care` |
| **Expected Category** | `personal_care` |
| **Expected Urgency** | `LOW` (score: 10–35) |
| **Expected Keywords** | toothpaste, mouthwash, dental, oral care |
| **Expected Products** | Toothpaste varieties, mouthwash |
| **Expected Cart** | 4 oral care products |
| **Expected AI Response** | "I found X oral care products..." |
| **Cart Action** | "Add it to my cart" → adds top product |
| **Context Test** | Follow up: "Add the second one too" → adds second product from stored list |

---

### TC-07: Fever Treatment (Pediatric)

| Field | Value |
|-------|-------|
| **User Input** | `"Emergency! My child has high fever and needs medicine now"` |
| **Expected Intent** | `fever_treatment` |
| **Expected Category** | `medical` |
| **Expected Urgency** | `CRITICAL` (score: 90–100) |
| **Expected Keywords** | thermometer, paracetamol, ORS, ice pack, fever |
| **Expected Products** | Children's fever medicine, thermometer, ORS |
| **Expected Cart** | 4 fever-related products |
| **Expected AI Response** | "I understand this is urgent!..." (uses urgency-aware opening) |
| **Cart Action** | "Add everything" → all 4 products added |
| **Best Demo** | Demonstrates emergency detection prominently |

---

### TC-08: Grocery Restock

| Field | Value |
|-------|-------|
| **User Input** | `"Need groceries for the week — milk, bread, eggs, rice"` |
| **Expected Intent** | `grocery_restock` |
| **Expected Category** | `groceries` |
| **Expected Urgency** | `LOW` to `MEDIUM` (score: 20–55) |
| **Expected Keywords** | milk, bread, eggs, rice, butter, vegetables |
| **Expected Products** | General grocery / nutrition products |
| **Expected Cart** | 4 grocery-related products |
| **Expected AI Response** | "I found X products for you..." |
| **Cart Action** | "Add first three" → command-based cart add |

---

### TC-09: Skin Rash / Allergy

| Field | Value |
|-------|-------|
| **User Input** | `"I have a skin rash and it's itching badly"` |
| **Expected Intent** | `skin_care` |
| **Expected Category** | `medical` |
| **Expected Urgency** | `MEDIUM` to `HIGH` (score: 45–75) |
| **Expected Keywords** | calamine lotion, antihistamine, cream, ointment, rash |
| **Expected Products** | Calamine lotion, antihistamine, moisturizer |
| **Expected Cart** | 4 skin care / allergy products |
| **Expected AI Response** | "I found products for skin relief..." |
| **Cart Action** | Tap product card "Add to Cart" button |

---

### TC-10: Digestive / Stomach Issue

| Field | Value |
|-------|-------|
| **User Input** | `"My stomach is upset and I need antacid immediately"` |
| **Expected Intent** | `digestive_relief` |
| **Expected Category** | `medical` |
| **Expected Urgency** | `HIGH` (score: 70–85) |
| **Expected Keywords** | antacid, ORS, probiotics, electrolyte, digestive |
| **Expected Products** | Antacid tablets, ORS powder, digestive aids |
| **Expected Cart** | 4 digestive health products |
| **Expected AI Response** | "I found products for stomach relief..." |
| **Cart Action** | "Yes" (confirmation) → adds top product |

---

### TC-11: Party Supplies

| Field | Value |
|-------|-------|
| **User Input** | `"Friends coming over in 30 minutes, need snacks and drinks fast"` |
| **Expected Intent** | `party_supplies` |
| **Expected Category** | `party` |
| **Expected Urgency** | `HIGH` (score: 70–85) |
| **Expected Keywords** | chips, snacks, cold drinks, nuts, disposable plates |
| **Expected Products** | Snack products, beverages |
| **Expected Cart** | 4 snack/party items |
| **Expected AI Response** | "I found X products for you. My top recommendation is..." |
| **Cart Action** | "Add all to cart" → bulk add |
| **Context Test** | Follow up: "Add more chips" → searches for chips specifically |

---

### TC-12: Vitamins & Supplements

| Field | Value |
|-------|-------|
| **User Input** | `"I need daily vitamins and supplements for better immunity"` |
| **Expected Intent** | `personal_care` |
| **Expected Category** | `personal_care` |
| **Expected Urgency** | `LOW` (score: 10–35) |
| **Expected Keywords** | vitamin, supplement, multivitamin, omega, immunity |
| **Expected Products** | Vitamin C, multivitamins, omega-3 |
| **Expected Cart** | 4 supplement products |
| **Expected AI Response** | "I found X supplement products..." |
| **Eco Alternative** | May show organic supplement alternatives |
| **Cart Action** | "Buy now" → checkout directly |

---

### TC-13: Context Memory Retention

| Field | Value |
|-------|-------|
| **Turn 1 Input** | `"Order eco-friendly shampoo"` |
| **Turn 1 Expected** | Shows 4 shampoo products with eco alternatives |
| **Turn 2 Input** | `"Add it"` (referring to top recommendation) |
| **Turn 2 Expected** | Adds top shampoo WITHOUT new backend search |
| **Turn 3 Input** | `"Checkout"` |
| **Turn 3 Expected** | Navigates directly to /checkout |
| **What This Tests** | Local action command interception in `useChat.ts` |
| **Key Behavior** | "Add it", "Add first one", "Buy now" all handled locally |

---

### TC-14: Multi-Cart Action Flow

| Field | Value |
|-------|-------|
| **Setup** | Complete a chat that returns 4 products |
| **Action 1** | Tap "+Cart" on Product 2 |
| **Action 2** | Tap "+Cart" on Product 4 |
| **Action 3** | Navigate to /cart |
| **Expected** | Cart shows both items with prices |
| **Action 4** | Remove Product 2 (tap remove) |
| **Expected** | Cart updates to 1 item |
| **Action 5** | Proceed to Checkout |
| **Expected** | /checkout page with order summary |
| **What This Tests** | Full cart CRUD loop |

---

### TC-15: Complete Checkout → Order Flow

| Field | Value |
|-------|-------|
| **Setup** | Have at least 1 item in cart |
| **Step 1** | Navigate to /checkout |
| **Step 2** | Fill form: Name, Phone (10 digits), Address, City, State, Pincode (6 digits) |
| **Step 3** | Select "Cash on Delivery" payment |
| **Step 4** | Click "Place Order" |
| **Expected** | Redirect to /order-success?orderId=NN-XXXXXXXX |
| **Step 5** | Verify: Order ID shown, delivery time shown, items listed |
| **Step 6** | Click "View Orders" → /orders page shows new order |
| **Step 7** | Refresh page → order still visible (persisted to JSON file) |
| **What This Tests** | Full checkout + persistent order storage |

---

## 5 Safe Demo Scenarios (Most Reliable for Live Demo)

These scenarios are the most visually compelling and technically reliable:

### 🥇 Demo 1: Emergency First Aid (Best Opening)
**Input**: `"I cut my finger and it's bleeding badly"`  
**Why safe**: Triggers CRITICAL urgency (visually impactful), returns relevant products, eco alternative may appear, demonstrates the core value proposition instantly.

### 🥈 Demo 2: Context-Aware Shopping (Shows Intelligence)
**Turn 1**: `"Order eco-friendly shampoo"`  
**Turn 2**: `"Add it"` (no backend call — uses context)  
**Turn 3**: `"Checkout"`  
**Why safe**: Shows 3 natural conversational turns, action commands work locally (never fails), demonstrates the "smart assistant" story clearly.

### 🥉 Demo 3: Baby Care Urgent (Emotional Impact)
**Input**: `"My baby needs diapers and formula urgently"`  
**Why safe**: HIGH urgency shown visually, baby category returns clear relevant products, relatable scenario for audience.

### 4️⃣ Demo 4: Sustainability Dashboard (Differentiation)
**Input**: `"I need eco-friendly cleaning products"`  
**Then**: Navigate to /sustainability page  
**Why safe**: Demonstrates the eco-scoring and sustainability features that differentiate NeedNow AI from regular shopping.

### 5️⃣ Demo 5: Complete Checkout Flow (End-to-End)
**Show**: Cart → Checkout form → Place Order → Order Success  
**Why safe**: Cart and orders are fully implemented, persist across refresh, no external API dependency for the order flow itself.

---

## Video Demo Script

### Scene 1: Opening (30 seconds)
```
[Screen: NeedNow AI home page - http://localhost:3000 or Vercel URL]

NARRATOR:
"Imagine shopping without search. Just describe what you need, 
and NeedNow AI understands your situation and finds exactly 
what you're looking for — instantly."

[Pan to chat interface]
"Let's see it in action."
```

### Scene 2: Emergency Product Search (60 seconds)
```
[Chat page open]

NARRATOR: 
"Here's a real scenario. Someone cuts their finger."

[TYPE OR SPEAK]: "I cut my finger and it's bleeding badly"

[Wait for response — 2-3 seconds]

SHOW:
- AI response in natural language (no JSON visible)
- 4 product cards appear inline
- Urgency badge shows CRITICAL
- Highlight the "reason" under each product

NARRATOR:
"NeedNow AI detected this as a CRITICAL urgency situation.
In seconds, it found the most relevant first-aid products —
Bandages, antiseptic, gauze — exactly what you need."

[Pause on product cards]
```

### Scene 3: Voice Input (30 seconds)
```
NARRATOR:
"And you can use your voice."

[Click microphone button — pulsing red animation appears]

SPEAK: "I need cold and cough medicine urgently"

[Microphone auto-submits, response appears]

NARRATOR:
"Voice to cart — completely hands-free."
```

### Scene 4: Context-Aware Cart (45 seconds)
```
NARRATOR:
"Watch how the AI remembers context."

[After shampoo search]
TYPE: "Add it to my cart"

SHOW:
- No new search triggered (response is instant)
- "Added [Shampoo Name] to your cart!" message appears
- Green cart bar appears at bottom: "1 item in cart [View Cart] [Checkout]"

NARRATOR:
"I said 'it' and the AI knew exactly which product I meant —
the one it just recommended. No search. No confusion."
```

### Scene 5: Checkout Flow (60 seconds)
```
[Click "Checkout" from cart bar]

SHOW checkout page:
- Fill delivery form (use sample: Arman Gupta, 9876543210, 123 MG Road, Mumbai, Maharashtra, 400001)
- Select "Cash on Delivery"
- Click "Place Order"

[Order Success page]

NARRATOR:
"Order placed! Order ID, delivery time, items — all confirmed."

[Click "View Orders"]
[Refresh the page]

NARRATOR:
"And it persists. Even after a full page refresh, your order 
history is right here."
```

### Scene 6: Sustainability (30 seconds)
```
[Navigate to /sustainability page or show eco alternative in chat]

NARRATOR:
"NeedNow AI also cares about the planet. Every recommendation 
comes with an eco-score, and when a greener alternative exists, 
we show it — with the exact carbon savings."

[Highlight eco score badge and carbon savings]
```

### Scene 7: Closing (20 seconds)
```
[Show split screen: Chat → Recommendations → Cart → Orders]

NARRATOR:
"NeedNow AI. From situation to cart in seconds.
Powered by Google Gemini. Built for Amazon HackOn 2025."

[Logo fade]
```

---

## Sample Conversation Transcripts

### Transcript 1: Emergency Medical
```
You: I cut my finger and it's bleeding badly

🤖 NeedNow AI:
I understand this is urgent! I found 4 products that can help right away. 
My top recommendation is **Clear Strip Waterproof Sterile Bandage** for ₹9. 
Stops bleeding and protects the wound. Would you like me to add it to your cart?

[Product Cards]
1. Clear Strip Waterproof Sterile Bandage — ₹9      [+ Cart]
2. Antiseptic Liquid 100ml — ₹80                    [+ Cart]
3. Sterile Gauze Pads Pack — ₹45                    [+ Cart]
4. First Aid Kit Compact — ₹299                     [+ Cart]
[🛒 Add Top Pick to Cart] [⚡ Buy Now]

You: Add it

🤖 NeedNow AI:
✅ Added **Clear Strip Waterproof Sterile Bandage** to your cart! 
You can view your cart or continue shopping.

[🛒 1 item in cart]  [View Cart] [Checkout]
```

### Transcript 2: Context Awareness Demo
```
You: Order eco-friendly shampoo

🤖 NeedNow AI:
I found 4 products for you. My top recommendation is 
**Khadi Natural Herbal Shampoo** for ₹275. Best eco-friendly option 
for hair care. I also found a greener alternative: Mamaearth Onion Shampoo.
Would you like me to add it to your cart?

[Product Cards shown]

You: Yes add it

🤖 NeedNow AI:
✅ Added **Khadi Natural Herbal Shampoo** to your cart! 
You can view your cart or continue shopping.

You: Checkout

🤖 NeedNow AI:
Let's proceed to checkout!

[Navigates to /checkout — no new search triggered]
```

### Transcript 3: Multi-Turn Shopping
```
You: I need vitamins for daily health

🤖 NeedNow AI:
I found 4 products for you. My top recommendation is 
**Multivitamin Daily Pack** for ₹399. Essential daily nutrition.
Would you like me to add it to your cart?

You: Add all of them

🤖 NeedNow AI:
✅ Added all 4 products to your cart! Ready to checkout?

[🛒 4 items in cart]  [View Cart] [Checkout]

You: View cart

🤖 NeedNow AI:
Opening your cart!

[Navigates to /cart]
```

---

## Pre-Demo Checklist

```
□ Backend running: http://localhost:8000/health → {"status":"healthy"}
□ Frontend running: http://localhost:3000
□ NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local
□ USE_MOCK_LLM=true (if Gemini quota is exhausted)
□ Test TC-01 before going live
□ Clear chat history before demo (click "Clear" button)
□ Have a fresh browser tab open
□ Disable browser notifications
□ Full-screen browser for recording
```

## Known Limitations During Demo

| Limitation | Workaround |
|-----------|-----------|
| Gemini quota exhausted (429) | Set `USE_MOCK_LLM=true` — all features still work |
| Products may not be relevant | System uses mock product retrieval from DB — products shown are real but may not match query perfectly |
| Voice input requires Chrome | Use Chrome/Chromium for Web Speech API |
| FAISS not loaded | System uses DB fallback automatically — no impact on demo |
