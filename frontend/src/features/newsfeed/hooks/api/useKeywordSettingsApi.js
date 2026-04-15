import { useState, useEffect, useCallback } from 'react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('KeywordSettings');

export function useKeywordSettings() {
  const [keywords, setKeywords] = useState([]);
  const [keywordMatchingEnabled, setKeywordMatchingEnabled] = useState(false);
  const [newsfeedConfig, setNewsfeedConfig] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;
    const fetchData = async () => {
      setLoading(true);
      try {
        const [configData, keywordsData] = await Promise.all([
          newsfeedSettingsApi.getConfig(),
          newsfeedSettingsApi.getKeywords(),
        ]);
        if (!ignore) {
          setKeywordMatchingEnabled(configData.keyword_matching_enabled);
          setNewsfeedConfig(configData);
          setKeywords(keywordsData || []);
        }
      } catch (err) {
        if (!ignore) {
          logger.error('Error loading keyword settings:', err);
          setError(err);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };
    fetchData();
    return () => { ignore = true; };
  }, []);

  const toggleKeywordMatching = useCallback(async (enabled) => {
    setKeywordMatchingEnabled(enabled);
    try {
      const updatedConfig = await newsfeedSettingsApi.updateConfig({
        ...newsfeedConfig,
        keyword_matching_enabled: enabled,
      });
      setNewsfeedConfig(updatedConfig);
      return { success: true };
    } catch (err) {
      logger.error('Error toggling keyword matching:', err);
      setKeywordMatchingEnabled(!enabled);
      return { success: false, error: err };
    }
  }, [newsfeedConfig]);

  const addKeyword = useCallback(async (keyword) => {
    if (keywords.some(k => k.keyword.toLowerCase() === keyword.toLowerCase())) {
      return { success: false, duplicate: true };
    }

    try {
      const newKeyword = await newsfeedSettingsApi.addKeyword(keyword);
      setKeywords(prev => [...prev, newKeyword]);
      return { success: true };
    } catch (err) {
      logger.error('Error adding keyword:', err);
      return { success: false, error: err };
    }
  }, [keywords]);

  const deleteKeyword = useCallback(async (keywordId) => {
    try {
      await newsfeedSettingsApi.deleteKeyword(keywordId);
      setKeywords(prev => prev.filter(k => k.id !== keywordId));
      return { success: true };
    } catch (err) {
      logger.error('Error deleting keyword:', err);
      return { success: false, error: err };
    }
  }, []);

  return {
    keywords,
    keywordMatchingEnabled,
    loading,
    error,
    toggleKeywordMatching,
    addKeyword,
    deleteKeyword,
  };
}
