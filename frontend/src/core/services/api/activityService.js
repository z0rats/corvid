import api from '../baseApi';

/** Cross-feature feed of the newest saved runs/lookups (backend: features/activity/). */
export const activityService = {
  async listRecent(limit = 8) {
    const response = await api.get('/api/activity', { params: { limit } });
    return response.data;
  },
};
