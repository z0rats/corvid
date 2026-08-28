import api from '../../../../core/services/baseApi';
import { templatesApi } from './templatesApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('templatesApi.createTemplate', () => {
  it('fills in array/number defaults before posting', async () => {
    api.post.mockResolvedValue({ data: { id: 1 } });

    const result = await templatesApi.createTemplate({ title: 'My template' });

    expect(api.post).toHaveBeenCalledWith('/api/ai-templates', {
      title: 'My template',
      payload_fields: [],
      static_contexts: [],
      web_contexts: [],
      temperature: 0.7,
      model: null,
      category_id: null,
    });
    expect(result).toEqual({ id: 1 });
  });

  it('preserves provided arrays, temperature, model, and category', async () => {
    api.post.mockResolvedValue({ data: { id: 1 } });

    await templatesApi.createTemplate({
      title: 'My template',
      payload_fields: ['field_a'],
      static_contexts: ['ctx'],
      web_contexts: ['web'],
      temperature: 0.2,
      model: 'claude-sonnet-5',
      category_id: 5,
    });

    expect(api.post).toHaveBeenCalledWith('/api/ai-templates', {
      title: 'My template',
      payload_fields: ['field_a'],
      static_contexts: ['ctx'],
      web_contexts: ['web'],
      temperature: 0.2,
      model: 'claude-sonnet-5',
      category_id: 5,
    });
  });
});

describe('templatesApi.getTemplates', () => {
  it('requests templates with default pagination', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    const result = await templatesApi.getTemplates();

    expect(api.get).toHaveBeenCalledWith('/api/ai-templates', { params: { skip: 0, limit: 100 } });
    expect(result).toEqual({ items: [] });
  });

  it('passes through custom skip/limit', async () => {
    api.get.mockResolvedValue({ data: { items: [] } });

    await templatesApi.getTemplates({ skip: 20, limit: 10 });

    expect(api.get).toHaveBeenCalledWith('/api/ai-templates', { params: { skip: 20, limit: 10 } });
  });
});

describe('templatesApi.getTemplate', () => {
  it('requests a single template by id', async () => {
    api.get.mockResolvedValue({ data: { id: 1 } });

    const result = await templatesApi.getTemplate(1);

    expect(api.get).toHaveBeenCalledWith('/api/ai-templates/1');
    expect(result).toEqual({ id: 1 });
  });
});

describe('templatesApi.updateTemplate', () => {
  it('puts the transformed template', async () => {
    api.put.mockResolvedValue({ data: { id: 1 } });

    const result = await templatesApi.updateTemplate(1, { title: 'Updated' });

    expect(api.put).toHaveBeenCalledWith('/api/ai-templates/1', {
      title: 'Updated',
      payload_fields: [],
      static_contexts: [],
      web_contexts: [],
      temperature: 0.7,
      model: null,
      category_id: null,
    });
    expect(result).toEqual({ id: 1 });
  });
});

describe('templatesApi.deleteTemplate', () => {
  it('deletes a template by id', async () => {
    api.delete.mockResolvedValue({ data: { success: true } });

    const result = await templatesApi.deleteTemplate(1);

    expect(api.delete).toHaveBeenCalledWith('/api/ai-templates/1');
    expect(result).toEqual({ success: true });
  });
});

describe('templatesApi.executeTemplate', () => {
  it('posts the execution payload for the given template', async () => {
    api.post.mockResolvedValue({ data: { output: 'result text' } });

    const result = await templatesApi.executeTemplate(1, { ioc: '1.2.3.4' });

    expect(api.post).toHaveBeenCalledWith('/api/ai-templates/execute/1', { ioc: '1.2.3.4' });
    expect(result).toEqual({ output: 'result text' });
  });
});

describe('templatesApi.engineerPrompt', () => {
  it('trims title/description and defaults model_id to null', async () => {
    api.post.mockResolvedValue({ data: { prompt: 'engineered' } });

    const result = await templatesApi.engineerPrompt({
      title: '  My Title  ',
      description: '  does a thing  ',
    });

    expect(api.post).toHaveBeenCalledWith('/api/ai-templates/prompt-engineer', {
      title: 'My Title',
      description: 'does a thing',
      model_id: null,
    });
    expect(result).toEqual({ prompt: 'engineered' });
  });

  it('passes through a provided model_id', async () => {
    api.post.mockResolvedValue({ data: { prompt: 'engineered' } });

    await templatesApi.engineerPrompt({
      title: 'Title',
      description: 'Description',
      model_id: 'claude-sonnet-5',
    });

    expect(api.post).toHaveBeenCalledWith('/api/ai-templates/prompt-engineer', {
      title: 'Title',
      description: 'Description',
      model_id: 'claude-sonnet-5',
    });
  });
});

describe('templatesApi.reorderTemplates', () => {
  it('posts the new template order', async () => {
    api.post.mockResolvedValue({ data: { success: true } });

    const result = await templatesApi.reorderTemplates([3, 1, 2]);

    expect(api.post).toHaveBeenCalledWith('/api/ai-templates/reorder', { template_ids: [3, 1, 2] });
    expect(result).toEqual({ success: true });
  });
});
