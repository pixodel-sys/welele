from typing import List, Dict, Any

class RecommendationService:
    @staticmethod
    def score_stories(stories: List[Dict[str, Any]], user_interests: List[str] = None) -> List[Dict[str, Any]]:
        """
        Rank stories based on engagement velocity, views, likes, and cultural affinity tags.
        """
        def get_score(story):
            views = story.get("total_views", 0)
            likes = story.get("total_likes", 0)
            rating = story.get("rating", 4.5)
            is_trending = 1.5 if story.get("is_trending") else 1.0
            is_original = 1.3 if story.get("is_original") else 1.0
            return (views * 0.4 + likes * 0.6) * rating * is_trending * is_original

        return sorted(stories, key=get_score, reverse=True)

recommendation_service = RecommendationService()
