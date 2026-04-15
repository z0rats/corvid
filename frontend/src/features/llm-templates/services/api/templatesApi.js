import api from '../../../../core/services/baseApi';

function transformTemplateForAPI(template) {
  return {
    ...template,
    payload_fields: Array.isArray(template.payload_fields) ? template.payload_fields : [],
    static_contexts: Array.isArray(template.static_contexts) ? template.static_contexts : [],
    web_contexts: Array.isArray(template.web_contexts) ? template.web_contexts : [],
    temperature: template.temperature || 0.7,
    model: template.model || null,
    category_id: template.category_id || null,
  };
}

export const templatesApi = {
  async createTemplate(data) {
    const response = await api.post('/api/ai-templates', transformTemplateForAPI(data));
    return response.data;
  },

  async getTemplates({ skip = 0, limit = 100, user_id = null } = {}) {
    const params = { skip, limit };
    if (user_id) params.user_id = user_id;
    const response = await api.get('/api/ai-templates', { params });
    return response.data;
  },

  async getTemplate(templateId) {
    const response = await api.get(`/api/ai-templates/${templateId}`);
    return response.data;
  },

  async updateTemplate(templateId, data) {
    const response = await api.put(`/api/ai-templates/${templateId}`, transformTemplateForAPI(data));
    return response.data;
  },

  async deleteTemplate(templateId) {
    const response = await api.delete(`/api/ai-templates/${templateId}`);
    return response.data;
  },

  async executeTemplate(templateId, executionData) {
    const response = await api.post(`/api/ai-templates/execute/${templateId}`, executionData);
    return response.data;
  },

  async engineerPrompt(payload) {
    const requestData = {
      title: payload.title.trim(),
      description: payload.description.trim(),
      model_id: payload.model_id || null,
    };
    const response = await api.post('/api/ai-templates/prompt-engineer', requestData);
    return response.data;
  },

  async reorderTemplates(templateIds) {
    const response = await api.post('/api/ai-templates/reorder', { template_ids: templateIds });
    return response.data;
  },
};
