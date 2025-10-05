"""
T032: Pain point extractor
Extract and summarize pain points from Reddit posts
"""
from typing import Dict, Any, List, Optional
import re


class PainPointExtractor:
    """
    Pain point extraction from Reddit posts

    Strategies:
    1. Regex pattern matching for common pain point expressions
    2. Text summarization (max 500 chars)
    3. Deduplication based on similarity

    Note: For MVP, using rule-based extraction.
    Future: Can upgrade to LLM-based extraction for better quality.
    """

    # Pain point indicator patterns
    PAIN_PATTERNS = [
        r"i\s+(?:need|want|wish|looking for)\s+(.+?)(?:\.|$)",
        r"(?:can't|cannot|unable to)\s+(.+?)(?:\.|$)",
        r"(?:struggling|struggle|difficult|hard)\s+(?:with|to)\s+(.+?)(?:\.|$)",
        r"(?:frustrated|annoyed|annoying)\s+(?:with|by|that)\s+(.+?)(?:\.|$)",
        r"(?:problem|issue|challenge)\s+(?:with|is)\s+(.+?)(?:\.|$)",
        r"(?:there should be|wish there was|would be nice if)\s+(.+?)(?:\.|$)",
        r"(?:does anyone|anyone know|is there)\s+(?:a|an)?\s*(.+?)(?:\?|$)",
        r"(?:how do i|how can i|how to)\s+(.+?)(?:\?|$)",
    ]

    @classmethod
    def extract_from_text(cls, text: str, max_length: int = 500) -> Optional[str]:
        """
        Extract pain point from text using pattern matching

        Args:
            text: Text to analyze (title + body)
            max_length: Maximum extracted text length

        Returns:
            str: Extracted pain point or None if no patterns match
        """
        if not text or len(text.strip()) == 0:
            return None

        # Clean text
        text_cleaned = text.strip()

        # Try each pattern
        for pattern in cls.PAIN_PATTERNS:
            matches = re.finditer(pattern, text_cleaned, re.IGNORECASE)

            for match in matches:
                # Extract the captured group
                extracted = match.group(1).strip()

                # Skip very short extracts
                if len(extracted) < 10:
                    continue

                # Truncate to max length
                if len(extracted) > max_length:
                    extracted = extracted[:max_length-3] + "..."

                return extracted

        # If no patterns match, try to extract first meaningful sentence
        sentences = re.split(r'[.!?]', text_cleaned)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= 20:  # Minimum meaningful length
                if len(sentence) > max_length:
                    sentence = sentence[:max_length-3] + "..."
                return sentence

        return None

    @classmethod
    def extract_from_post(cls, post_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract pain point from Reddit post

        Args:
            post_data: Post dictionary with 'title' and 'text' keys

        Returns:
            str: Extracted pain point or None
        """
        title = post_data.get("title", "")
        text = post_data.get("text", "")

        # Combine title and body
        combined = f"{title}. {text}"

        return cls.extract_from_text(combined, max_length=500)

    @classmethod
    def extract_multiple(cls, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract pain points from multiple posts

        Args:
            posts: List of post dictionaries

        Returns:
            List[dict]: List of extracted pain points with metadata
                Each dict contains:
                - extracted_text: The pain point text
                - source_posts: List of source Reddit post IDs
                - original_post: Original post data
        """
        extracted = []

        for post in posts:
            pain_point = cls.extract_from_post(post)

            if pain_point:
                extracted.append({
                    "extracted_text": pain_point,
                    "source_posts": [post.get("reddit_id")],
                    "original_post": post
                })

        return extracted

    @classmethod
    def deduplicate_similar(cls, pain_points: List[str], similarity_threshold: float = 0.8) -> List[str]:
        """
        Deduplicate similar pain points

        Args:
            pain_points: List of extracted pain point texts
            similarity_threshold: Similarity threshold for deduplication (0-1)

        Returns:
            List[str]: Deduplicated pain points

        Note: Simple implementation using word overlap.
        Can be improved with embedding-based similarity.
        """
        if len(pain_points) == 0:
            return []

        deduplicated = [pain_points[0]]

        for i in range(1, len(pain_points)):
            current = pain_points[i]
            is_duplicate = False

            # Compare with all previously added pain points
            for existing in deduplicated:
                similarity = cls._calculate_word_overlap(current, existing)

                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduplicated.append(current)

        return deduplicated

    @classmethod
    def _calculate_word_overlap(cls, text1: str, text2: str) -> float:
        """
        Calculate word overlap similarity (Jaccard)

        Args:
            text1: First text
            text2: Second text

        Returns:
            float: Similarity score (0-1)
        """
        # Tokenize into words
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))

        # Avoid division by zero
        if len(words1) == 0 or len(words2) == 0:
            return 0.0

        # Jaccard similarity: intersection / union
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    @classmethod
    def create_summary(cls, text: str, max_length: int = 200) -> str:
        """
        Create a short summary of text

        Args:
            text: Text to summarize
            max_length: Maximum summary length

        Returns:
            str: Summary text
        """
        if not text:
            return ""

        # Clean text
        text = text.strip()

        # If already short, return as-is
        if len(text) <= max_length:
            return text

        # Take first N chars and find last complete word
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')

        if last_space > 0:
            return truncated[:last_space] + "..."

        return truncated + "..."
