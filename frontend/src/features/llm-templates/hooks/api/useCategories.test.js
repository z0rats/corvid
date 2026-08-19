import { act, renderHook, waitFor } from '@testing-library/react';
import { useCategories } from './useCategories';
import { categoriesApi } from '../../services/api/categoriesApi';

vi.mock('../../services/api/categoriesApi');

describe('useCategories', () => {
  afterEach(() => vi.clearAllMocks());

  it('fetches categories on mount', async () => {
    categoriesApi.getCategories.mockResolvedValue([{ id: '1', name: 'Default' }]);

    const { result } = renderHook(() => useCategories());

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.categories).toEqual([{ id: '1', name: 'Default' }]);
  });

  it('surfaces a fetch error and clears the list', async () => {
    categoriesApi.getCategories.mockRejectedValue(new Error('network down'));

    const { result } = renderHook(() => useCategories());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('network down');
    expect(result.current.categories).toEqual([]);
  });

  it('createCategory appends the created category and returns it', async () => {
    categoriesApi.getCategories.mockResolvedValue([]);
    categoriesApi.createCategory.mockResolvedValue({ id: '2', name: 'New' });

    const { result } = renderHook(() => useCategories());
    await waitFor(() => expect(result.current.loading).toBe(false));

    let created;
    await act(async () => {
      created = await result.current.createCategory('New');
    });

    expect(created).toEqual({ id: '2', name: 'New' });
    expect(result.current.categories).toEqual([{ id: '2', name: 'New' }]);
  });

  it('updateCategory replaces the matching category in place', async () => {
    categoriesApi.getCategories.mockResolvedValue([{ id: '1', name: 'Old' }]);
    categoriesApi.updateCategory.mockResolvedValue({ id: '1', name: 'Renamed' });

    const { result } = renderHook(() => useCategories());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.updateCategory('1', 'Renamed');
    });

    expect(result.current.categories).toEqual([{ id: '1', name: 'Renamed' }]);
  });

  it('deleteCategory removes the category from local state', async () => {
    categoriesApi.getCategories.mockResolvedValue([{ id: '1' }, { id: '2' }]);
    categoriesApi.deleteCategory.mockResolvedValue(undefined);

    const { result } = renderHook(() => useCategories());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.deleteCategory('1', 'move_to_default');
    });

    expect(categoriesApi.deleteCategory).toHaveBeenCalledWith('1', 'move_to_default');
    expect(result.current.categories).toEqual([{ id: '2' }]);
  });

  it('reorderCategories reorders optimistically and persists the new order', async () => {
    categoriesApi.getCategories.mockResolvedValue([{ id: 'a' }, { id: 'b' }]);
    categoriesApi.reorderCategories.mockResolvedValue(undefined);

    const { result } = renderHook(() => useCategories());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.reorderCategories(0, 1);
    });

    expect(result.current.categories.map((c) => c.id)).toEqual(['b', 'a']);
    expect(categoriesApi.reorderCategories).toHaveBeenCalledWith(['b', 'a']);
  });

  it('moveTemplates delegates to the API without touching local category state', async () => {
    categoriesApi.getCategories.mockResolvedValue([{ id: '1' }]);
    categoriesApi.moveTemplates.mockResolvedValue(undefined);

    const { result } = renderHook(() => useCategories());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.moveTemplates(['t1', 't2'], 'cat-1');
    });

    expect(categoriesApi.moveTemplates).toHaveBeenCalledWith(['t1', 't2'], 'cat-1');
    expect(result.current.categories).toEqual([{ id: '1' }]);
  });
});
