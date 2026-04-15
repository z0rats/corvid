import { useState, useEffect, useCallback } from 'react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('TrendsBlacklist');

export function useTrendsBlacklist() {
  const [wordBlacklist, setWordBlacklist] = useState([]);
  const [iocBlacklist, setIocBlacklist] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    const fetchData = async () => {
      setLoading(true);
      try {
        const [words, iocs] = await Promise.all([
          newsfeedSettingsApi.getBlacklistEntries('word'),
          newsfeedSettingsApi.getBlacklistEntries('ioc'),
        ]);
        if (!ignore) {
          setWordBlacklist(words || []);
          setIocBlacklist(iocs || []);
        }
      } catch (err) {
        if (!ignore) {
          logger.error('Error loading blacklist entries:', err);
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

  const addToBlacklist = useCallback(async (value, type) => {
    const list = type === 'word' ? wordBlacklist : iocBlacklist;
    if (list.some(e => e.value.toLowerCase() === value.toLowerCase())) {
      return { success: false, duplicate: true };
    }

    try {
      const newEntry = await newsfeedSettingsApi.addBlacklistEntry(value, type);
      if (type === 'word') {
        setWordBlacklist(prev => [...prev, newEntry]);
      } else {
        setIocBlacklist(prev => [...prev, newEntry]);
      }
      return { success: true };
    } catch (err) {
      logger.error('Error adding blacklist entry:', err);
      return { success: false, error: err };
    }
  }, [wordBlacklist, iocBlacklist]);

  const removeFromBlacklist = useCallback(async (entryId, type) => {
    try {
      await newsfeedSettingsApi.deleteBlacklistEntry(entryId);
      if (type === 'word') {
        setWordBlacklist(prev => prev.filter(e => e.id !== entryId));
      } else {
        setIocBlacklist(prev => prev.filter(e => e.id !== entryId));
      }
      return { success: true };
    } catch (err) {
      logger.error('Error removing blacklist entry:', err);
      return { success: false, error: err };
    }
  }, []);

  return {
    wordBlacklist,
    iocBlacklist,
    loading,
    addToBlacklist,
    removeFromBlacklist,
  };
}
