"""
Newsfeed CRUD operations - Main entry point
This module provides a unified interface to all newsfeed CRUD operations
by importing and re-exporting functions from specialized modules.
"""

# Import all functions from specialized CRUD modules
from app.features.newsfeed.crud.newsfeed_settings_crud import (
    get_all_newsfeed_settings as get_newsfeed_settings,
    create_newsfeed_setting as create_newsfeed_settings,
    update_newsfeed_setting as update_newsfeed_settings,
    delete_newsfeed_setting as delete_newsfeed_settings,
    toggle_feed_status as disable_feed,
    create_custom_feed,
    create_custom_feed_with_favicon,
    delete_custom_feed,
    get_feed_by_name,
    update_feed_icon,
)

from app.features.newsfeed.crud.news_articles_crud import (
    get_all_news_articles as get_news_articles,
    get_news_articles_by_retention,
    create_news_article,
    update_news_article,
    delete_old_news_articles,
    check_article_exists as news_article_exists,
    get_news_article_by_id,
    get_news_articles_by_ids,
    get_recent_news_articles,
    get_paginated_articles as fetch_paginated_articles
)

from app.features.newsfeed.crud.newsfeed_config_crud import (
    get_newsfeed_config,
    update_newsfeed_config,
    get_retention_days as get_newsfeed_retention_days,
    set_retention_days,
    update_last_fetch_timestamp,
    is_background_fetch_enabled,
    is_keyword_matching_enabled,
    get_fetch_interval_minutes
)

from app.features.newsfeed.crud.analytics_crud import (
    get_title_word_frequency,
    get_top_iocs,
    get_top_cves,
    get_ioc_type_distribution,
    parse_time_range
)

from app.features.newsfeed.crud.newsfeed_settings_crud import toggle_feed_status
