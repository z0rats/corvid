import { act, renderHook, waitFor } from '@testing-library/react';
import { useSanctionsSearch } from './useSanctionsSearch';
import { sanctionsSearchApi } from '../../services/api/sanctionsSearchApi';

vi.mock('../../services/api/sanctionsSearchApi');

let prefillCallback;
vi.mock('../../../../core/hooks/usePrefillFromQuery', () => ({
  usePrefillFromQuery: vi.fn((cb) => { prefillCallback = cb; }),
}));

afterEach(() => {
  vi.clearAllMocks();
  prefillCallback = undefined;
});

describe('useSanctionsSearch — schema loading', () => {
  it('loads the available schemas on mount', async () => {
    sanctionsSearchApi.getSchemas.mockResolvedValue(['Person', 'Vessel']);

    const { result } = renderHook(() => useSanctionsSearch());

    await waitFor(() => expect(result.current.schemas).toEqual(['Person', 'Vessel']));
  });

  it('does not throw when schema loading fails', async () => {
    sanctionsSearchApi.getSchemas.mockRejectedValue(new Error('network down'));

    const { result } = renderHook(() => useSanctionsSearch());

    await waitFor(() => expect(result.current.schemas).toEqual([]));
  });
});

describe('useSanctionsSearch — runSearch', () => {
  it('does nothing for a query shorter than the minimum length', async () => {
    sanctionsSearchApi.getSchemas.mockResolvedValue([]);
    const { result } = renderHook(() => useSanctionsSearch());

    await act(async () => result.current.runSearch('ab'));

    expect(sanctionsSearchApi.search).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });

  it('searches with the trimmed query and current schema filter, populating the result', async () => {
    sanctionsSearchApi.getSchemas.mockResolvedValue([]);
    sanctionsSearchApi.search.mockResolvedValue({ matches: [{ opensanctions_id: 'NK-1' }] });
    const { result } = renderHook(() => useSanctionsSearch());
    act(() => result.current.setSchema('Person'));

    await act(async () => result.current.runSearch('  Jane Doe  '));

    expect(sanctionsSearchApi.search).toHaveBeenCalledWith({
      query: 'Jane Doe',
      schema: 'Person',
      limit: 50,
    });
    expect(result.current.result).toEqual({ matches: [{ opensanctions_id: 'NK-1' }] });
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sends undefined schema when no filter is selected', async () => {
    sanctionsSearchApi.getSchemas.mockResolvedValue([]);
    sanctionsSearchApi.search.mockResolvedValue({ matches: [] });
    const { result } = renderHook(() => useSanctionsSearch());

    await act(async () => result.current.runSearch('Jane Doe'));

    expect(sanctionsSearchApi.search).toHaveBeenCalledWith(
      expect.objectContaining({ schema: undefined }),
    );
  });

  it('surfaces the API error message and clears loading', async () => {
    sanctionsSearchApi.getSchemas.mockResolvedValue([]);
    sanctionsSearchApi.search.mockRejectedValue(new Error('Sanctions search failed'));
    const { result } = renderHook(() => useSanctionsSearch());

    await act(async () => result.current.runSearch('Jane Doe'));

    expect(result.current.error).toBe('Sanctions search failed');
    expect(result.current.loading).toBe(false);
    expect(result.current.result).toBeNull();
  });

  it('prefers the response detail message over the generic error message', async () => {
    sanctionsSearchApi.getSchemas.mockResolvedValue([]);
    sanctionsSearchApi.search.mockRejectedValue({ response: { data: { detail: 'List not loaded' } } });
    const { result } = renderHook(() => useSanctionsSearch());

    await act(async () => result.current.runSearch('Jane Doe'));

    expect(result.current.error).toBe('List not loaded');
  });
});

describe('useSanctionsSearch — prefill from query', () => {
  it('sets the query field and immediately runs the search, not just populating the field', async () => {
    sanctionsSearchApi.getSchemas.mockResolvedValue([]);
    sanctionsSearchApi.search.mockResolvedValue({ matches: [] });
    const { result } = renderHook(() => useSanctionsSearch());
    await waitFor(() => expect(prefillCallback).toBeDefined());

    await act(async () => prefillCallback('Jane Doe'));

    expect(result.current.query).toBe('Jane Doe');
    expect(sanctionsSearchApi.search).toHaveBeenCalledWith(
      expect.objectContaining({ query: 'Jane Doe' }),
    );
  });
});
