import api from '../../../../core/services/baseApi';

export const dorkRunnerApi = {
  async getTemplates(targetType) {
    const response = await api.get('/api/dork-runner/templates', { params: { target_type: targetType } });
    return response.data;
  },

  async runDorks({ target, targetType, engine, templateKeys }) {
    const response = await api.post('/api/dork-runner/run', {
      target,
      target_type: targetType,
      engine,
      template_keys: templateKeys,
    });
    return response.data;
  },
};
