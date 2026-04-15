import api from '../../../../core/services/baseApi';

export const categoriesApi = {
  async getCategories() {
    const response = await api.get('/api/ai-templates/groups');
    return response.data;
  },

  async createCategory(name) {
    const response = await api.post('/api/ai-templates/groups', { name });
    return response.data;
  },

  async updateCategory(categoryId, name) {
    const response = await api.put(`/api/ai-templates/groups/${categoryId}`, { name });
    return response.data;
  },

  async deleteCategory(categoryId, action) {
    const response = await api.delete(`/api/ai-templates/groups/${categoryId}`, {
      data: { action },
    });
    return response.data;
  },

  async reorderCategories(categoryIds) {
    const response = await api.post('/api/ai-templates/groups/reorder', {
      category_ids: categoryIds,
    });
    return response.data;
  },

  async moveTemplates(templateIds, categoryId) {
    const response = await api.post('/api/ai-templates/groups/move-templates', {
      template_ids: templateIds,
      category_id: categoryId,
    });
    return response.data;
  },
};
