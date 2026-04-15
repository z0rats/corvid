import api from '../baseApi';

/**
 * Health check service for backend connectivity
 */
export const healthService = {
  async checkBackendHealth() {
    const response = await api.get('/api/healthcheck');
    return response.data;
  }
};
