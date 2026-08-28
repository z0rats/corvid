import api from '../../../../core/services/baseApi';
import { categoriesApi } from './categoriesApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('categoriesApi.getCategories', () => {
  it('requests the list of template categories', async () => {
    api.get.mockResolvedValue({ data: [{ id: 1, name: 'Phishing' }] });

    const result = await categoriesApi.getCategories();

    expect(api.get).toHaveBeenCalledWith('/api/ai-templates/groups');
    expect(result).toEqual([{ id: 1, name: 'Phishing' }]);
  });
});

describe('categoriesApi.createCategory', () => {
  it('posts the new category name', async () => {
    api.post.mockResolvedValue({ data: { id: 2, name: 'Malware' } });

    const result = await categoriesApi.createCategory('Malware');

    expect(api.post).toHaveBeenCalledWith('/api/ai-templates/groups', { name: 'Malware' });
    expect(result).toEqual({ id: 2, name: 'Malware' });
  });
});

describe('categoriesApi.updateCategory', () => {
  it('puts the renamed category', async () => {
    api.put.mockResolvedValue({ data: { id: 2, name: 'Ransomware' } });

    const result = await categoriesApi.updateCategory(2, 'Ransomware');

    expect(api.put).toHaveBeenCalledWith('/api/ai-templates/groups/2', { name: 'Ransomware' });
    expect(result).toEqual({ id: 2, name: 'Ransomware' });
  });
});

describe('categoriesApi.deleteCategory', () => {
  it('deletes the category with the chosen action for its templates', async () => {
    api.delete.mockResolvedValue({ data: { success: true } });

    const result = await categoriesApi.deleteCategory(2, 'move_to_uncategorized');

    expect(api.delete).toHaveBeenCalledWith('/api/ai-templates/groups/2', {
      data: { action: 'move_to_uncategorized' },
    });
    expect(result).toEqual({ success: true });
  });
});

describe('categoriesApi.reorderCategories', () => {
  it('posts the new category order', async () => {
    api.post.mockResolvedValue({ data: { success: true } });

    const result = await categoriesApi.reorderCategories([3, 1, 2]);

    expect(api.post).toHaveBeenCalledWith('/api/ai-templates/groups/reorder', {
      category_ids: [3, 1, 2],
    });
    expect(result).toEqual({ success: true });
  });
});

describe('categoriesApi.moveTemplates', () => {
  it('posts the template ids and target category', async () => {
    api.post.mockResolvedValue({ data: { moved: 2 } });

    const result = await categoriesApi.moveTemplates([10, 11], 2);

    expect(api.post).toHaveBeenCalledWith('/api/ai-templates/groups/move-templates', {
      template_ids: [10, 11],
      category_id: 2,
    });
    expect(result).toEqual({ moved: 2 });
  });
});
