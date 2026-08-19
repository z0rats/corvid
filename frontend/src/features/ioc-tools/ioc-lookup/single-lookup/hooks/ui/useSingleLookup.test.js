import { act, renderHook } from '@testing-library/react';
import { useSingleLookup } from './useSingleLookup';
import { determineIocType } from '../../../shared/utils/iocDefinitions';
import { lookupHistoryApi } from '../../services/api/lookupHistoryApi';

vi.mock('../../../shared/utils/iocDefinitions');
vi.mock('../../services/api/lookupHistoryApi');
vi.mock('../../../../../../core/hooks/usePrefillFromQuery', () => ({
  usePrefillFromQuery: vi.fn(),
}));

afterEach(() => vi.clearAllMocks());

// handleValidation is internal - every public entry point (handleSubmitSearch,
// handleKeyPress's Enter branch) funnels through it via the input ref, so
// that's how these tests drive it.
function submit(result, value) {
  result.current.inputRef.current = { value };
  act(() => result.current.handleSubmitSearch());
}

describe('useSingleLookup — validation via handleSubmitSearch', () => {
  it('accepts a recognized IOC, trims it, and shows the results table', () => {
    determineIocType.mockReturnValue('ip');
    const { result } = renderHook(() => useSingleLookup());

    submit(result, '  1.2.3.4  ');

    expect(result.current.searchValue).toBe('1.2.3.4');
    expect(result.current.currentIocType).toBe('ip');
    expect(result.current.shouldShowTable).toBe(true);
    expect(result.current.snackbarOpen).toBe(false);
  });

  it('rejects an unrecognized value and opens the error snackbar', () => {
    determineIocType.mockReturnValue('unknown');
    const { result } = renderHook(() => useSingleLookup());

    submit(result, 'not an ioc');

    expect(result.current.shouldShowTable).toBe(false);
    expect(result.current.snackbarOpen).toBe(true);
  });

  it('resets everything for blank input without opening the error snackbar', () => {
    determineIocType.mockReturnValue('ip');
    const { result } = renderHook(() => useSingleLookup());
    submit(result, '1.2.3.4');

    submit(result, '   ');

    expect(result.current.searchValue).toBe('');
    expect(result.current.currentIocType).toBe('');
    expect(result.current.shouldShowTable).toBe(false);
    expect(result.current.snackbarOpen).toBe(false);
  });

  it('handleSubmitSearch tolerates a null input ref', () => {
    determineIocType.mockReturnValue('ip');
    const { result } = renderHook(() => useSingleLookup());
    result.current.inputRef.current = null;

    expect(() => act(() => result.current.handleSubmitSearch())).not.toThrow();
  });
});

describe('useSingleLookup — handleKeyPress', () => {
  it('submits only on Enter', () => {
    determineIocType.mockReturnValue('domain');
    const { result } = renderHook(() => useSingleLookup());
    result.current.inputRef.current = { value: 'example.com' };

    act(() => result.current.handleKeyPress({ key: 'Tab' }));
    expect(result.current.searchValue).toBe('');

    act(() => result.current.handleKeyPress({ key: 'Enter' }));
    expect(result.current.searchValue).toBe('example.com');
  });
});

describe('useSingleLookup — handleCloseError', () => {
  it('closes the error snackbar', () => {
    determineIocType.mockReturnValue('unknown');
    const { result } = renderHook(() => useSingleLookup());
    submit(result, 'bad input');
    expect(result.current.snackbarOpen).toBe(true);

    act(() => result.current.handleCloseError());

    expect(result.current.snackbarOpen).toBe(false);
  });
});

describe('useSingleLookup — handleSearchComplete', () => {
  it('saves the search to history', () => {
    lookupHistoryApi.saveSearch.mockResolvedValue({});
    const { result } = renderHook(() => useSingleLookup());

    act(() => {
      result.current.handleSearchComplete({ ioc: '1.2.3.4', iocType: 'ip', results: {} });
    });

    expect(lookupHistoryApi.saveSearch).toHaveBeenCalledWith('1.2.3.4', 'ip', {});
  });

  it('does not throw when saving to history fails', () => {
    lookupHistoryApi.saveSearch.mockRejectedValue(new Error('save failed'));
    const { result } = renderHook(() => useSingleLookup());

    expect(() => {
      act(() => {
        result.current.handleSearchComplete({ ioc: '1.2.3.4', iocType: 'ip', results: {} });
      });
    }).not.toThrow();
  });
});
