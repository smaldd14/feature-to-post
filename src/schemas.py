from typing_extensions import TypedDict
from typing import List

class Chapter(TypedDict):
    start_time: float
    end_time: float
    title: str
    description: str

class ChapterBreakdown(TypedDict):
    chapters: List[Chapter]

class Tweet(TypedDict):
    number: int
    content: str
    character_count: int

class TweetThread(TypedDict):
    tweets: List[Tweet]