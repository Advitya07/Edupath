from app.config.settings import get_settings

CURATED = [
    {"type": "Article", "title": "MDN Web Docs", "url": "https://developer.mozilla.org/", "description": "Clear reference material and examples."},
    {"type": "Video", "title": "freeCodeCamp", "url": "https://www.youtube.com/@freecodecamp", "description": "Long-form practical walkthroughs."},
    {"type": "Practice", "title": "Build a mini project", "url": "https://github.com/", "description": "Apply the concept in a small, shippable exercise."},
]


async def find_resources(topic: str) -> list[dict]:
    """Use curated material in demo mode; Pinecone can be wired with embedding metadata."""
    settings = get_settings()
    if not (settings.pinecone_api_key and settings.pinecone_index):
        return [{**item, "topic": topic} for item in CURATED]
    # A production implementation queries the configured index with an embedding.
    return [{**item, "topic": topic} for item in CURATED]
