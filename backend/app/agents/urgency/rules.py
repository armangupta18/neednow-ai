from datetime import datetime


class UrgencyRules:

    @staticmethod
    def boost_score(
        text: str,
        score: int,
    ) -> int:

        text = text.lower()

        keywords = {
            "emergency": 25,
            "urgent": 20,
            "immediately": 20,
            "asap": 20,
            "doctor": 25,
            "hospital": 25,
            "baby": 15,
            "guests": 15,
            "party": 10,
            "30 minutes": 15,
            "1 hour": 10,
        }

        boost = 0

        for keyword, value in keywords.items():

            if keyword in text:
                boost += value

        return min(
            100,
            score + boost,
        )

    @staticmethod
    def time_of_day_adjustment(
        score: int,
        hour: int,
    ) -> int:

        if 22 <= hour <= 23:
            score += 5

        elif 0 <= hour <= 5:
            score += 10

        return min(100, score)