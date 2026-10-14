import api from '../baseApi';

/** In-app alerts inbox (backend: core/alerts/) - scan outcomes, job failures, security events. */
export const alertsService = {
  async getUnreadCount() {
    const response = await api.get('/api/alerts/count/unread');
    return response.data.unread_count;
  },

  async list(limit = 50) {
    const response = await api.get('/api/alerts', { params: { limit } });
    return response.data;
  },

  async markRead(id, read = true) {
    const response = await api.patch(`/api/alerts/${id}`, { read });
    return response.data;
  },

  async markAllRead() {
    await api.patch('/api/alerts');
  },

  async deleteAll() {
    await api.delete('/api/alerts');
  },
};
