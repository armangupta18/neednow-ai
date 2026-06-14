"""Alternative product service.

Finds genuinely greener alternatives — only returns an eco alternative
if it scores meaningfully higher than the original product.
"""

from app.agents.sustainability.scoring_service import SustainabilityScoringService

# Minimum score improvement to qualify as a "greener" alternative
MIN_SCORE_IMPROVEMENT = 8.0


class AlternativeService:
    """Finds eco-friendly alternatives that are genuinely greener."""

    @staticmethod
    def find_best(original_product, alternatives):
        """Find the best eco-friendly alternative to the original product.

        Returns None if no alternative scores significantly higher
        on sustainability than the original product.
        """
        if not alternatives:
            return None

        original_score = SustainabilityScoringService.calculate_score(original_product)

        best_product = None
        best_improvement = 0.0

        for product in alternatives:
            alt_score = SustainabilityScoringService.calculate_score(product)
            improvement = alt_score - original_score

            if improvement > best_improvement and improvement >= MIN_SCORE_IMPROVEMENT:
                best_product = product
                best_improvement = improvement

        return best_product
