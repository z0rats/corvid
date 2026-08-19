import { act, renderHook, waitFor } from '@testing-library/react';
import { useTemplates } from './useTemplates';
import { templatesApi } from '../../services/api/templatesApi';

vi.mock('../../services/api/templatesApi');

describe('useTemplates', () => {
  afterEach(() => vi.clearAllMocks());

  it('fetches templates on mount', async () => {
    templatesApi.getTemplates.mockResolvedValue([{ id: '1', title: 'A' }]);

    const { result } = renderHook(() => useTemplates());

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.templates).toEqual([{ id: '1', title: 'A' }]);
    expect(result.current.error).toBeNull();
  });

  it('defaults to an empty list when the API returns something non-array', async () => {
    templatesApi.getTemplates.mockResolvedValue(null);

    const { result } = renderHook(() => useTemplates());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.templates).toEqual([]);
  });

  it('surfaces a fetch error and clears the list', async () => {
    templatesApi.getTemplates.mockRejectedValue({ response: { data: { detail: 'boom' } } });

    const { result } = renderHook(() => useTemplates());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('boom');
    expect(result.current.templates).toEqual([]);
  });

  it('deleteTemplate removes the template from local state on success', async () => {
    templatesApi.getTemplates.mockResolvedValue([{ id: '1' }, { id: '2' }]);
    templatesApi.deleteTemplate.mockResolvedValue(undefined);

    const { result } = renderHook(() => useTemplates());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.deleteTemplate('1');
    });

    expect(result.current.templates).toEqual([{ id: '2' }]);
  });

  it('deleteTemplate rethrows on failure without mutating local state', async () => {
    templatesApi.getTemplates.mockResolvedValue([{ id: '1' }]);
    templatesApi.deleteTemplate.mockRejectedValue(new Error('nope'));

    const { result } = renderHook(() => useTemplates());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await expect(
      act(async () => {
        await result.current.deleteTemplate('1');
      }),
    ).rejects.toThrow('nope');

    expect(result.current.templates).toEqual([{ id: '1' }]);
  });

  it('reorderTemplates reorders optimistically and persists the new order', async () => {
    templatesApi.getTemplates.mockResolvedValue([{ id: 'a' }, { id: 'b' }, { id: 'c' }]);
    templatesApi.reorderTemplates.mockResolvedValue(undefined);

    const { result } = renderHook(() => useTemplates());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.reorderTemplates(0, 2);
    });

    expect(result.current.templates.map((t) => t.id)).toEqual(['b', 'c', 'a']);
    expect(templatesApi.reorderTemplates).toHaveBeenCalledWith(['b', 'c', 'a']);
  });

  it('reorderTemplates re-fetches from the server if persisting the order fails', async () => {
    templatesApi.getTemplates
      .mockResolvedValueOnce([{ id: 'a' }, { id: 'b' }])
      .mockResolvedValueOnce([{ id: 'a' }, { id: 'b' }]);
    templatesApi.reorderTemplates.mockRejectedValue(new Error('server rejected order'));

    const { result } = renderHook(() => useTemplates());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.reorderTemplates(0, 1);
    });

    expect(templatesApi.getTemplates).toHaveBeenCalledTimes(2);
  });
});
