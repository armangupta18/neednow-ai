# Cart Mutation Fix Report — NeedNow AI

## Root Cause

`get_cart()` used the in-memory demo cart as fallback, but `remove_item()`, `clear_cart()`, and `add_item()` all went directly to the database via `CartRepository`. The DB has no User record for the demo user → `CartNotFoundError`.

**The cart mutations and cart retrieval were using DIFFERENT storage backends.**

## Fix

Made all cart operations check `_demo_carts` first (when the demo cart exists for that user), and only fall through to the DB path when no demo cart is present.

## File Modified

`app/services/cart_service.py`

## Changes

| Method | Before | After |
|--------|--------|-------|
| `get_cart()` | DB → demo fallback | DB → demo fallback (unchanged) |
| `add_item()` | DB only → crash | Demo cart check first → append product |
| `remove_item()` | DB only → crash | Demo cart check first → filter product out |
| `clear_cart()` | DB only → crash | Demo cart check first → set to empty |

Added shared helpers:
- `_has_demo_cart(user_id)` — check if demo cart exists
- `_get_demo_cart_response(user_id)` — build CartResponse from demo data

## Verification

```
1. Chat: 200 | Products: 10
2. GET cart: 200 | Items: 10
3. REMOVE item: 200 | Items after: 9
4. GET cart: 200 | Items: 9
5. CLEAR cart: 200 | Cleared: True
6. GET cart: 200 | Items: 0

✅ All cart mutations working!
324 tests pass.
```

## Architecture Note

The demo cart is **in-memory only** (class-level `dict`). It persists across requests within the same server process but resets on restart. For the hackathon demo this is sufficient. For production, this should be backed by Redis or the DB (which requires a real User record).
