import { useCallback, useEffect, useRef, useState } from 'react';
import { alertsService } from '../../services/api/alertsService';
import { createLogger } from '../../utils/logger';

const logger = createLogger('useAlerts');

export const ALERTS_POLL_INTERVAL_MS = 30_000;

/**
 * Unread-count polling plus on-demand list loading for the AppBar alerts menu. Polls rather than
 * using the backend's /ws/alerts socket: a single-user tool gains little from push, and polling
 * needs no extra reverse-proxy route. Paused while the tab is hidden, refreshed on focus.
 */
export function useAlerts() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const mounted = useRef(true);

  const refreshCount = useCallback(async () => {
    try {
      const count = await alertsService.getUnreadCount();
      if (mounted.current) setUnreadCount(count);
    } catch (err) {
      logger.warn('Failed to fetch unread alert count:', err);
    }
  }, []);

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const [list, count] = await Promise.all([alertsService.list(), alertsService.getUnreadCount()]);
      if (!mounted.current) return;
      setAlerts(list);
      setUnreadCount(count);
    } catch (err) {
      logger.error('Failed to load alerts:', err);
      if (mounted.current) setError(true);
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    refreshCount();
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') refreshCount();
    }, ALERTS_POLL_INTERVAL_MS);
    const onVisible = () => { if (document.visibilityState === 'visible') refreshCount(); };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      mounted.current = false;
      clearInterval(id);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [refreshCount]);

  const markRead = useCallback(async (alert) => {
    if (alert.read) return;
    setAlerts((prev) => prev.map((a) => (a.id === alert.id ? { ...a, read: true } : a)));
    setUnreadCount((prev) => Math.max(0, prev - 1));
    try {
      await alertsService.markRead(alert.id);
    } catch (err) {
      logger.error('Failed to mark alert read:', err);
      refreshCount();
    }
  }, [refreshCount]);

  const markAllRead = useCallback(async () => {
    setAlerts((prev) => prev.map((a) => ({ ...a, read: true })));
    setUnreadCount(0);
    try {
      await alertsService.markAllRead();
    } catch (err) {
      logger.error('Failed to mark all alerts read:', err);
      loadAlerts();
    }
  }, [loadAlerts]);

  const clearAll = useCallback(async () => {
    try {
      await alertsService.deleteAll();
      setAlerts([]);
      setUnreadCount(0);
    } catch (err) {
      logger.error('Failed to delete alerts:', err);
      setError(true);
    }
  }, []);

  return { unreadCount, alerts, loading, error, loadAlerts, markRead, markAllRead, clearAll };
}
