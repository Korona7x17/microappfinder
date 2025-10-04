from typing import Protocol, List, Dict, Any, Optional
from pydantic import BaseModel


class RawItem(BaseModel):
    """Raw item fetched from a provider"""
    source: str
    url: str
    title: Optional[str] = None
    text: Optional[str] = None
    meta: Dict[str, Any] = {}


class Provider(Protocol):
    """Base protocol for all data providers"""
    
    def search(self, topics: List[str], limit: int = 30) -> List[str]:
        """
        Search for URLs based on topics
        
        Args:
            topics: List of search topics/keywords
            limit: Maximum number of URLs to return
            
        Returns:
            List of URLs to fetch
        """
        ...
    
    def hydrate(self, url: str) -> RawItem:
        """
        Fetch and parse a single URL
        
        Args:
            url: URL to fetch
            
        Returns:
            RawItem with parsed content
        """
        ...
