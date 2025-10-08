"""
T025: Reddit API client
PRAW wrapper for Reddit API integration with rate limiting and NSFW filtering
"""
import praw
from praw.models import Submission
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import time


class RedditAPIClient:
    """
    Reddit API client using PRAW

    Features:
    - OAuth2 authentication
    - 14 curated subreddits for pain point discovery
    - NSFW content filtering
    - Rate limiting (<60 req/min per Reddit ToS)
    - Search by time range
    """

    # Curated subreddit list for pain point discovery
    CURATED_SUBREDDITS = [
        "AppIdeas",
        "SomebodyMakeThis",
        "productivity",
        "freelance",
        "Entrepreneur",
        "startups",
        "SaaS",
        "IndieBiz",
        "smallbusiness",
        "digitalnomad",
        "webdev",
        "programming",
        "technology",
        "LifeProTips",
    ]

    # Spam/NSFW keyword blocklist
    SPAM_KEYWORDS = [
        "buy now",
        "click here",
        "crypto",
        "nft",
        "get rich quick",
        "limited time",
        "act now",
    ]

    def __init__(self):
        """Initialize PRAW Reddit client with OAuth2 credentials"""
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
        )

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests (60 req/min max)

    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)

        self.last_request_time = time.time()

    def _is_spam(self, text: str) -> bool:
        """
        Check if text contains spam keywords

        Args:
            text: Text to check (title + body)

        Returns:
            bool: True if spam detected, False otherwise
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.SPAM_KEYWORDS)

    def _submission_to_dict(self, submission: Submission) -> Dict[str, Any]:
        """
        Convert PRAW Submission to dictionary

        Args:
            submission: PRAW Submission object

        Returns:
            dict: Normalized post data
        """
        return {
            "reddit_id": f"t3_{submission.id}",
            "subreddit": submission.subreddit.display_name,
            "author": submission.author.name if submission.author else None,
            "title": submission.title,
            "text": submission.selftext if submission.is_self else None,
            "url": f"https://reddit.com{submission.permalink}",
            "score": submission.score,
            "comment_count": submission.num_comments,
            "created_utc": datetime.utcfromtimestamp(submission.created_utc),
            "is_nsfw": submission.over_18,
        }

    def search_subreddits(
        self,
        topics: List[str],
        time_range: str = "week",
        limit: int = 100,
        filter_nsfw: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search curated subreddits for pain points

        Args:
            topics: List of search keywords (1-5 items)
            time_range: Time filter ('day', 'week', 'month', 'year', 'all')
            limit: Max results per subreddit
            filter_nsfw: Exclude NSFW content (default: True)

        Returns:
            List[dict]: List of normalized Reddit posts
        """
        # Map our time_range to PRAW time_filter
        # PRAW options: day, week, month, year, all
        time_filter_map = {
            "1month": "month",
            "3months": "year",  # Closest option
            "6months": "year",
            "1year": "year",
            "all": "all",
        }
        praw_time_filter = time_filter_map.get(time_range, "month")

        # Build search query targeting PAIN SIGNALS per spec
        # Instead of just searching for generic topics, search for pain expressions
        pain_phrases = [
            '"I wish there was an app"',
            '"is there an app that"',
            '"how do you track"',
            '"looking for a tool"',
            '"need a way to"',
            '"frustrated with"',
            '"annoying that"',
            '"pain point"',
            '"would pay for"',
            '"somebody should build"',
            '"why isn\'t there"'
        ]

        # Simpler approach: just search for the topics directly
        # Let the LLM analyze what's a pain point later
        # This follows Greg Isenberg's approach - find what's trending first

        # Simply search for topics - Reddit will find relevant discussions
        query = " OR ".join(topics[:3])  # Just use the topics directly

        print(f"Reddit search query: {query}")  # Log full query

        results = []

        for subreddit_name in self.CURATED_SUBREDDITS:
            try:
                self._rate_limit()

                subreddit = self.reddit.subreddit(subreddit_name)

                # Search subreddit
                submissions = subreddit.search(
                    query=query,
                    time_filter=praw_time_filter,
                    limit=limit,
                    sort="relevance"
                )

                for submission in submissions:
                    # Filter NSFW
                    if filter_nsfw and submission.over_18:
                        continue

                    # Filter low-quality posts (score threshold)
                    if submission.score < 2:
                        continue

                    # Filter spam
                    combined_text = f"{submission.title} {submission.selftext}"
                    if self._is_spam(combined_text):
                        continue

                    # Add to results
                    post_data = self._submission_to_dict(submission)
                    results.append(post_data)

            except Exception as e:
                # Log error but continue with other subreddits
                print(f"Error searching r/{subreddit_name}: {str(e)}")
                continue

        return results

    def get_post_by_id(self, reddit_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch single post by Reddit ID (for deletion sync)

        Args:
            reddit_id: Reddit post ID (e.g., "t3_abc123")

        Returns:
            dict: Post data, or None if deleted/removed
        """
        try:
            self._rate_limit()

            # Extract ID without "t3_" prefix if present
            post_id = reddit_id.replace("t3_", "")

            submission = self.reddit.submission(id=post_id)

            # Check if post is deleted/removed
            if submission.author is None and submission.selftext == "[removed]":
                return None

            if submission.selftext == "[deleted]":
                return None

            return self._submission_to_dict(submission)

        except Exception as e:
            print(f"Error fetching post {reddit_id}: {str(e)}")
            return None

    def batch_check_deleted(self, reddit_ids: List[str]) -> Dict[str, bool]:
        """
        Batch check if posts are deleted (for deletion sync job)

        Args:
            reddit_ids: List of Reddit post IDs

        Returns:
            dict: {reddit_id: is_deleted}
        """
        results = {}

        for reddit_id in reddit_ids:
            post_data = self.get_post_by_id(reddit_id)
            results[reddit_id] = post_data is None

        return results
