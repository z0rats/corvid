import api from '../baseApi';

/**
 * Investigations (backend: features/investigations/) - named collections of runs from other
 * features. Lives in core because every feature's history detail can add its run to one.
 */
export const investigationsService = {
  /** Features whose runs can be added, with their display labels. */
  async features() {
    const response = await api.get('/api/investigations/features');
    return response.data;
  },

  async list() {
    const response = await api.get('/api/investigations');
    return response.data;
  },

  async get(id) {
    const response = await api.get(`/api/investigations/${id}`);
    return response.data;
  },

  async create(name, notes = null) {
    const response = await api.post('/api/investigations', { name, notes });
    return response.data;
  },

  async update(id, fields) {
    const response = await api.patch(`/api/investigations/${id}`, fields);
    return response.data;
  },

  async remove(id) {
    await api.delete(`/api/investigations/${id}`);
  },

  async addItem(id, feature, runId, note = null) {
    const response = await api.post(`/api/investigations/${id}/items`, {
      feature,
      run_id: runId,
      note,
    });
    return response.data;
  },

  async updateItem(id, itemId, note) {
    const response = await api.patch(`/api/investigations/${id}/items/${itemId}`, { note });
    return response.data;
  },

  async removeItem(id, itemId) {
    await api.delete(`/api/investigations/${id}/items/${itemId}`);
  },

  /** Investigations that already hold this run. */
  async memberships(feature, runId) {
    const response = await api.get('/api/investigations/memberships', {
      params: { feature, run_id: runId },
    });
    return response.data;
  },

  /** For core's ApiDownloadButtons, which downloads it through the authenticated client. */
  reportRequest(id, format, locale) {
    return {
      path: `/api/investigations/${id}/report`,
      params: { format, locale },
      fallbackName: `investigation-${id}.${format}`,
    };
  },

  async graph(id, types = null) {
    const response = await api.get(`/api/investigations/${id}/graph`, {
      params: types ? { types } : undefined,
      paramsSerializer: { indexes: null },
    });
    return response.data;
  },
};
