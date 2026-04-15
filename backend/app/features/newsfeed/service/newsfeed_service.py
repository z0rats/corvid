"""
Main newsfeed service - Entry point for all newsfeed operations
This module provides a unified interface by importing and re-exporting
functions from specialized service modules.
"""

from app.features.newsfeed.service.feed_processing_service import (
    fetch_and_store_news
)

from app.features.newsfeed.service.article_retrieval_service import (
    fetch_paginated_articles,
    get_news_from_db,
    get_recent_articles,
    get_total_articles_count,
    build_articles_response
)

from app.features.newsfeed.service.icon_management_service import (
    save_icon,
    validate_icon_file,
    remove_existing_icon,
    get_icon_path,
    icon_exists,
    get_default_icon_path,
    ensure_icons_directory
)
