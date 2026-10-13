import { useState, useEffect, useCallback } from 'react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('FeedManagement');

function arrayToFeedsMap(feedsArray) {
  return feedsArray.reduce((acc, feed) => {
    acc[feed.name] = feed;
    return acc;
  }, {});
}

export function useFeedManagement() {
  const [feeds, setFeeds] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;

    const fetchFeeds = async () => {
      setLoading(true);
      try {
        const feedsArray = await newsfeedSettingsApi.getNewsfeeds();
        if (!ignore) {
          setFeeds(arrayToFeedsMap(feedsArray));
        }
      } catch (error) {
        if (!ignore) {
          logger.error('Error fetching newsfeeds:', error);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    fetchFeeds();
    return () => { ignore = true; };
  }, []);

  // Optimistic edits go through functional updates of just the one field: a slower request
  // must not roll back (or overwrite) other edits made while it was in flight - another feed,
  // or another field of the same feed.
  const patchFeed = useCallback((feedName, patch) => {
    setFeeds((prev) => (prev[feedName] ? { ...prev, [feedName]: { ...prev[feedName], ...patch } } : prev));
  }, []);

  const toggleFeed = useCallback(async (feedName) => {
    const currentFeed = feeds[feedName];
    if (!currentFeed) return { success: false };

    const isCurrentlyEnabled = currentFeed.enabled;
    patchFeed(feedName, { enabled: !isCurrentlyEnabled });

    try {
      if (isCurrentlyEnabled) {
        await newsfeedSettingsApi.disableNewsfeed(feedName);
      } else {
        await newsfeedSettingsApi.enableNewsfeed(feedName);
      }
      return { success: true, enabled: !isCurrentlyEnabled };
    } catch (error) {
      patchFeed(feedName, { enabled: isCurrentlyEnabled });
      return { success: false, error };
    }
  }, [feeds, patchFeed]);

  const setReliability = useCallback(async (feedName, reliability) => {
    const previous = feeds[feedName]?.reliability;
    if (!feeds[feedName]) return { success: false };

    const apply = (value) => patchFeed(feedName, { reliability: value });
    apply(reliability);
    try {
      await newsfeedSettingsApi.setNewsfeedReliability(feedName, reliability);
      return { success: true, reliability };
    } catch (error) {
      apply(previous);
      return { success: false, error };
    }
  }, [feeds, patchFeed]);

  const addFeed = useCallback(async (newFeed, iconFile) => {
    try {
      const validationResult = await newsfeedSettingsApi.validateFeed({
        name: newFeed.name,
        url: newFeed.url,
        enabled: true,
      });

      if (!validationResult.valid) {
        return { success: false, error: { response: { data: { detail: 'Feed validation failed' } } } };
      }

      let feedData = await newsfeedSettingsApi.addNewsfeed(newFeed);

      if (iconFile) {
        const formData = new FormData();
        formData.append('file', iconFile);
        const encodedName = btoa(unescape(encodeURIComponent(newFeed.name)));
        const iconResponse = await newsfeedSettingsApi.uploadFeedIcon(encodedName, formData);
        feedData = { ...feedData, icon: iconResponse.icon_id, icon_id: iconResponse.icon_id };
      }

      const updatedFeeds = { ...feeds, [newFeed.name]: feedData };
      setFeeds(updatedFeeds);
      return { success: true };
    } catch (error) {
      return { success: false, error };
    }
  }, [feeds]);

  const deleteFeed = useCallback(async (name) => {
    try {
      await newsfeedSettingsApi.deleteNewsfeed(name);
      const updatedFeeds = { ...feeds };
      delete updatedFeeds[name];
      setFeeds(updatedFeeds);
      return { success: true };
    } catch (error) {
      return { success: false, error };
    }
  }, [feeds]);

  return {
    feeds,
    setFeeds,
    loading,
    toggleFeed,
    setReliability,
    addFeed,
    deleteFeed,
  };
}
