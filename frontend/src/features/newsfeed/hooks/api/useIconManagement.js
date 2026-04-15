import { useCallback, useRef, useEffect } from 'react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('IconManagement');

function safeEncodeFileName(name) {
  return btoa(unescape(encodeURIComponent(name)));
}

function arrayToFeedsMap(feedsArray) {
  return feedsArray.reduce((acc, feed) => {
    acc[feed.name] = feed;
    return acc;
  }, {});
}

export function useIconManagement(feeds, setFeeds) {
  const refreshTimerRef = useRef(null);

  useEffect(() => {
    return () => clearTimeout(refreshTimerRef.current);
  }, []);

  const deleteIcon = useCallback(async (feedName) => {
    try {
      const encodedName = safeEncodeFileName(feedName);
      const response = await newsfeedSettingsApi.deleteFeedIcon(encodedName);

      setFeeds({
        ...feeds,
        [feedName]: { ...feeds[feedName], icon: 'default.png', icon_id: null },
      });

      clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = setTimeout(async () => {
        try {
          const feedsArray = await newsfeedSettingsApi.getNewsfeeds();
          setFeeds(arrayToFeedsMap(feedsArray));
        } catch (err) {
          logger.error('Error refreshing feeds after icon deletion:', err);
        }
      }, 1000);

      return { success: true, message: response.message };
    } catch (error) {
      return { success: false, error };
    }
  }, [feeds, setFeeds]);

  const refetchIcon = useCallback(async (feedName) => {
    try {
      const encodedName = safeEncodeFileName(feedName);
      const response = await newsfeedSettingsApi.refetchFeedIcon(encodedName);
      if (response.success && response.icon_id) {
        setFeeds(prev => ({
          ...prev,
          [feedName]: {
            ...prev[feedName],
            icon: response.icon_id,
            icon_id: response.icon_id,
          },
        }));
      }
      return { success: response.success, message: response.message, iconId: response.icon_id };
    } catch (error) {
      return { success: false, error };
    }
  }, [setFeeds]);

  const refetchAllMissingIcons = useCallback(async () => {
    try {
      const response = await newsfeedSettingsApi.refetchAllMissingIcons();
      const feedsArray = await newsfeedSettingsApi.getNewsfeeds();
      setFeeds(arrayToFeedsMap(feedsArray));
      return {
        success: true,
        total: response.total,
        succeeded: response.succeeded,
        failed: response.failed,
        results: response.results,
      };
    } catch (error) {
      return { success: false, error };
    }
  }, [setFeeds]);

  const processIconFile = useCallback((file) => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => {
        const img = new Image();
        img.src = reader.result;
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = 150;
          canvas.height = 150;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, 150, 150);

          canvas.toBlob((blob) => {
            const resizedFile = new File([blob], file.name, { type: 'image/png' });
            resolve(resizedFile);
          }, 'image/png');
        };
      };
      reader.readAsDataURL(file);
    });
  }, []);

  return {
    deleteIcon,
    refetchIcon,
    refetchAllMissingIcons,
    processIconFile,
  };
}
