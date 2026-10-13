"""This file contains the default newsfeeds data.

`reliability` is the Admiralty-system source grade (A completely reliable ... F cannot be
judged) a fresh install starts with; users can re-grade any feed in Settings.
"""

DEFAULT_NEWSFEEDS = [
    {"name": "0dayFans", "url": "https://www.0dayfans.com/feed.rss", "reliability": "F"},
    {
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "reliability": "B",
    },
    {
        "name": "CyberScoop",
        "url": "https://www.cyberscoop.com/news/threats/feed",
        "reliability": "C",
    },
    {
        "name": "Dark Reading",
        "url": "https://www.darkreading.com/rss_simple.asp",
        "reliability": "C",
    },
    {
        "name": "HackerNoon",
        "url": "https://hackernoon.com/tagged/cybersecurity/feed",
        "reliability": "D",
    },
    {
        "name": "Helpnet Security",
        "url": "https://www.helpnetsecurity.com/feed/",
        "reliability": "C",
    },
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/", "reliability": "B"},
    {
        "name": "Schneier on Security",
        "url": "https://www.schneier.com/feed/atom/",
        "reliability": "B",
    },
    {
        "name": "Security Magazine",
        "url": "https://www.securitymagazine.com/rss/topic/2236",
        "reliability": "C",
    },
    {
        "name": "SecurityWeek",
        "url": "https://feeds.feedburner.com/securityweek",
        "reliability": "C",
    },
    {
        "name": "The DFIR Report",
        "url": "https://thedfirreport.com/feed/atom",
        "reliability": "B",
    },
    {
        "name": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "reliability": "C",
    },
    {"name": "The Record", "url": "https://therecord.media/feed", "reliability": "B"},
    {
        "name": "The Register",
        "url": "https://www.theregister.co.uk/security/headlines.atom",
        "reliability": "C",
    },
]
