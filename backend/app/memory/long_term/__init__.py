"""Long-term memory package for NeedNow AI.

Provides persistent memory stores that capture and evolve user signals
over time — preferences, purchase history, and behavioral patterns.

Usage:
    from app.memory.long_term import PreferenceMemory, PurchaseMemory, BehaviorMemory
"""

from app.memory.long_term.behavior_memory import BehaviorMemory
from app.memory.long_term.preference_memory import PreferenceMemory
from app.memory.long_term.purchase_memory import PurchaseMemory

__all__: list[str] = [
    "PreferenceMemory",
    "PurchaseMemory",
    "BehaviorMemory",
]
