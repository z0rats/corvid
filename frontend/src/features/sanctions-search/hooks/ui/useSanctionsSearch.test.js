import { act, renderHook as rtlRenderHook, waitFor } from '@testing-library/react';
import { createElement } from 'react';
import { MemoryRouter, useLocation } from 'react-router';
import { Provider, createStore } from 'jotai';
import { useSanctionsSearch } from './useSanctionsSearch';
import { sanctionsSearchApi } from '../../services/api/sanctionsSearchApi';

vi.mock('../../services/api/sanctionsSearchApi');

afterEach(() => vi.clearAllMocks());

// Fresh router + jotai store per test: the query lives in the URL and the result in an atom.
let location;
function renderHook(callback, { initialEntry = '/sanctions-search' } = {}) {
  const store = createStore();
  const LocationProbe = () => { location = useLocation(); return null; };
  const wrapper = ({ children }) => createElement(
    Provider, { store },
    createElement(MemoryRouter, { initialEntries: [initialEntry] }, children, createElement(LocationProbe)),
  );
  return rtlRenderHook(callback, { wrapper });
}

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

describe('useSanctionsSearch — URL-driven query', () => {
  it('runs the query already in the URL (pivot, reload, bookmark) and fills the field', async () => {
    sanctionsSearchApi.getSchemas.mockResolvedValue([]);
    sanctionsSearchApi.search.mockResolvedValue({ matches: [] });
    const { result } = renderHook(() => useSanctionsSearch(), { initialEntry: '/sanctions-search?q=Jane+Doe' });

    await waitFor(() => expect(sanctionsSearchApi.search).toHaveBeenCalledWith(
      expect.objectContaining({ query: 'Jane Doe' }),
    ));
    expect(result.current.query).toBe('Jane Doe');
  });

  it('puts a submitted query into the URL', async () => {
    sanctionsSearchApi.getSchemas.mockResolvedValue([]);
    sanctionsSearchApi.search.mockResolvedValue({ matches: [] });
    const { result } = renderHook(() => useSanctionsSearch());

    await act(async () => result.current.runSearch('Jane Doe'));

    expect(location.search).toBe('?q=Jane+Doe');
  });

  it('re-runs when the same query is submitted again', async () => {
    sanctionsSearchApi.getSchemas.mockResolvedValue([]);
    sanctionsSearchApi.search.mockResolvedValue({ matches: [] });
    const { result } = renderHook(() => useSanctionsSearch(), { initialEntry: '/sanctions-search?q=Jane+Doe' });
    await waitFor(() => expect(sanctionsSearchApi.search).toHaveBeenCalledTimes(1));

    await act(async () => result.current.runSearch());

    expect(sanctionsSearchApi.search).toHaveBeenCalledTimes(2);
  });
});
