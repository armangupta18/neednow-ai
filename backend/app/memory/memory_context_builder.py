from app.memory.schemas import UserMemory


class MemoryContextBuilder:

    @staticmethod
    def build(memory: UserMemory) -> str:

        sections = []

        if memory.dietary_preferences:
            sections.append(
                f"Dietary Preferences: {', '.join(memory.dietary_preferences)}"
            )

        if memory.preferred_brands:
            sections.append(
                f"Preferred Brands: {', '.join(memory.preferred_brands)}"
            )

        if memory.budget_level:
            sections.append(
                f"Budget Level: {memory.budget_level}"
            )

        if memory.family_size:
            sections.append(
                f"Family Size: {memory.family_size}"
            )

        if memory.purchase_patterns:
            sections.append(
                f"Purchase Patterns: {', '.join(memory.purchase_patterns)}"
            )

        sections.append(
            f"Sustainability Score: {memory.sustainability_score}"
        )

        return "\n".join(sections)