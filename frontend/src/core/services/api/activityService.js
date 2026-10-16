import api from '../baseApi';

/** Cross-feature feed of the newest saved runs/lookups (backend: features/activity/). */
export const activityService = {
  async listRecent(limit = 8) {
    const response = await api.get('/api/activity', { params: { limit } });
    return response.data;
  },

  /** Every scan still running or queued for a heavy-scan slot, across all features. */
  async listActive() {
    const response = await api.get('/api/activity/active');
    return response.data;
  },
};
