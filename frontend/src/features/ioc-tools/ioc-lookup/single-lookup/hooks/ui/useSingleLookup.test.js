import { act, renderHook } from '@testing-library/react';
import { createElement } from 'react';
import { MemoryRouter, useLocation } from 'react-router';
import { useSingleLookup } from './useSingleLookup';
import { determineIocType } from '../../../shared/utils/iocDefinitions';
import { lookupHistoryApi } from '../../services/api/lookupHistoryApi';

vi.mock('../../../shared/utils/iocDefinitions');
vi.mock('../../services/api/lookupHistoryApi');

afterEach(() => vi.clearAllMocks());

// Renders the hook inside a router, exposing the live location next to the hook's own result.
function renderLookup(initialEntry = '/ioc-tools/lookup') {
  const wrapper = ({ children }) => createElement(MemoryRouter, { initialEntries: [initialEntry] }, children);
  return renderHook(() => ({ hook: useSingleLookup(), location: useLocation() }), { wrapper });
}

// handleValidation is internal - every public entry point (handleSubmitSearch,
// handleKeyPress's Enter branch) funnels through it via the input ref, so
// that's how these tests drive it.
function submit(result, value) {
  result.current.hook.inputRef.current = { value };
  act(() => result.current.hook.handleSubmitSearch());
}

describe('useSingleLookup — validation via handleSubmitSearch', () => {
  it('accepts a recognized IOC, trims it, puts it in the URL and shows the results table', () => {
    determineIocType.mockReturnValue('ip');
    const { result } = renderLookup();

    submit(result, '  1.2.3.4  ');

    expect(result.current.hook.searchValue).toBe('1.2.3.4');
    expect(result.current.hook.currentIocType).toBe('ip');
    expect(result.current.hook.shouldShowTable).toBe(true);
    expect(result.current.hook.snackbarOpen).toBe(false);
    expect(result.current.location.search).toBe('?q=1.2.3.4');
  });

  it('refangs a defanged IOC before detecting its type, and writes it back to the field', () => {
    determineIocType.mockReturnValue('ip');
    const { result } = renderLookup();

    submit(result, '185.220.101[.]7');

    expect(determineIocType).toHaveBeenCalledWith('185.220.101.7');
    expect(result.current.hook.searchValue).toBe('185.220.101.7');
    expect(result.current.hook.inputRef.current.value).toBe('185.220.101.7');
  });

  it('rejects an unrecognized value, opens the error snackbar and leaves the URL alone', () => {
    determineIocType.mockReturnValue('unknown');
    const { result } = renderLookup();

    submit(result, 'not an ioc');

    expect(result.current.hook.shouldShowTable).toBe(false);
    expect(result.current.hook.snackbarOpen).toBe(true);
    expect(result.current.location.search).toBe('');
  });

  it('resets everything for blank input without opening the error snackbar', () => {
    determineIocType.mockReturnValue('ip');
    const { result } = renderLookup();
    submit(result, '1.2.3.4');

    submit(result, '   ');

    expect(result.current.hook.searchValue).toBe('');
    expect(result.current.hook.currentIocType).toBe('');
    expect(result.current.hook.shouldShowTable).toBe(false);
    expect(result.current.hook.snackbarOpen).toBe(false);
    expect(result.current.location.search).toBe('');
  });

  it('handleSubmitSearch tolerates a null input ref', () => {
    determineIocType.mockReturnValue('ip');
    const { result } = renderLookup();
    result.current.hook.inputRef.current = null;

    expect(() => act(() => result.current.hook.handleSubmitSearch())).not.toThrow();
  });
});

describe('useSingleLookup — URL-driven lookups', () => {
  it('runs the lookup already in the URL (pivot, reload, bookmark) from the cache', () => {
    determineIocType.mockReturnValue('domain');
    const { result } = renderLookup('/ioc-tools/lookup?q=example.com');

    expect(result.current.hook.searchValue).toBe('example.com');
    expect(result.current.hook.shouldShowTable).toBe(true);
    expect(result.current.hook.bypassCache).toBe(false);
  });

  it('flags an unrecognized value arriving via the URL', () => {
    determineIocType.mockReturnValue('unknown');
    const { result } = renderLookup('/ioc-tools/lookup?q=garbage');

    expect(result.current.hook.shouldShowTable).toBe(false);
    expect(result.current.hook.snackbarOpen).toBe(true);
  });

  it('treats re-submitting the current value as a refresh that bypasses the cache', () => {
    determineIocType.mockReturnValue('ip');
    const { result } = renderLookup('/ioc-tools/lookup?q=1.2.3.4');
    const firstKey = result.current.hook.refreshKey;

    submit(result, '1.2.3.4');

    expect(result.current.hook.bypassCache).toBe(true);
    expect(result.current.hook.refreshKey).not.toBe(firstKey);
  });

  it('does not carry a refresh over to the next value', () => {
    determineIocType.mockReturnValue('ip');
    const { result } = renderLookup('/ioc-tools/lookup?q=1.2.3.4');
    submit(result, '1.2.3.4');

    submit(result, '5.6.7.8');

    expect(result.current.hook.bypassCache).toBe(false);
  });
});

describe('useSingleLookup — handleKeyPress', () => {
  it('submits only on Enter', () => {
    determineIocType.mockReturnValue('domain');
    const { result } = renderLookup();
    result.current.hook.inputRef.current = { value: 'example.com' };

    act(() => result.current.hook.handleKeyPress({ key: 'Tab' }));
    expect(result.current.hook.searchValue).toBe('');

    act(() => result.current.hook.handleKeyPress({ key: 'Enter' }));
    expect(result.current.hook.searchValue).toBe('example.com');
  });
});

describe('useSingleLookup — handleCloseError', () => {
  it('closes the error snackbar', () => {
    determineIocType.mockReturnValue('unknown');
    const { result } = renderLookup();
    submit(result, 'bad input');
    expect(result.current.hook.snackbarOpen).toBe(true);

    act(() => result.current.hook.handleCloseError());

    expect(result.current.hook.snackbarOpen).toBe(false);
  });
});

describe('useSingleLookup — handleSearchComplete', () => {
  it('saves the search to history', () => {
    lookupHistoryApi.saveSearch.mockResolvedValue({});
    const { result } = renderLookup();

    act(() => {
      result.current.hook.handleSearchComplete({ ioc: '1.2.3.4', iocType: 'ip', results: {} });
    });

    expect(lookupHistoryApi.saveSearch).toHaveBeenCalledWith('1.2.3.4', 'ip', {});
  });

  it('does not throw when saving to history fails', () => {
    lookupHistoryApi.saveSearch.mockRejectedValue(new Error('save failed'));
    const { result } = renderLookup();

    expect(() => {
      act(() => {
        result.current.hook.handleSearchComplete({ ioc: '1.2.3.4', iocType: 'ip', results: {} });
      });
    }).not.toThrow();
  });
});
