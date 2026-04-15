from .default_template_data import DEFAULT_TEMPLATES
from .web_content_fetcher import fetch_web_contexts, format_web_contexts_for_prompt, WebContentFetcher

__all__ = [
    "DEFAULT_TEMPLATES",
    "fetch_web_contexts",
    "format_web_contexts_for_prompt", 
    "WebContentFetcher"
]
