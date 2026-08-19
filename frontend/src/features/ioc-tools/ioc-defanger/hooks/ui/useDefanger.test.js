import { act, renderHook } from '@testing-library/react';
import { useDefanger } from './useDefanger';
import { defangApi } from '../../../shared/services/api/defangApi';

vi.mock('../../../shared/services/api/defangApi');

beforeEach(() => {
  Object.assign(navigator, { clipboard: { writeText: vi.fn().mockResolvedValue(undefined) } });
});

afterEach(() => vi.clearAllMocks());

describe('useDefanger — handleProcess', () => {
  it('processes non-blank input through the API and stores the results', async () => {
    defangApi.batchProcessIOCs.mockResolvedValue([
      { original: '1.2.3.4', processed: '1[.]2[.]3[.]4', types: ['IP Address'], changed: true },
    ]);
    const { result } = renderHook(() => useDefanger());
    act(() => result.current.handleInputChange('1.2.3.4'));

    await act(async () => {
      await result.current.handleProcess();
    });

    expect(defangApi.batchProcessIOCs).toHaveBeenCalledWith('1.2.3.4', 'defang');
    expect(result.current.results).toHaveLength(1);
    expect(result.current.changedCount).toBe(1);
  });

  it('clears the results without calling the API for blank input', async () => {
    const { result } = renderHook(() => useDefanger());

    await act(async () => {
      await result.current.handleProcess();
    });

    expect(defangApi.batchProcessIOCs).not.toHaveBeenCalled();
    expect(result.current.results).toEqual([]);
  });

  it('falls back to unprocessed results when the API call fails', async () => {
    defangApi.batchProcessIOCs.mockRejectedValue(new Error('network down'));
    const { result } = renderHook(() => useDefanger());
    act(() => result.current.handleInputChange('1.2.3.4'));

    await act(async () => {
      await result.current.handleProcess();
    });

    expect(result.current.results).toEqual([
      { original: '1.2.3.4', processed: '1.2.3.4', types: ['Unknown'], changed: false },
    ]);
  });
});

describe('useDefanger — filteredResults', () => {
  it('shows only changed rows when showOnlyChanged is toggled on', async () => {
    defangApi.batchProcessIOCs.mockResolvedValue([
      { original: 'a', processed: 'a[.]', types: ['Domain'], changed: true },
      { original: 'b', processed: 'b', types: ['Domain'], changed: false },
    ]);
    const { result } = renderHook(() => useDefanger());
    act(() => result.current.handleInputChange('a\nb'));
    await act(async () => {
      await result.current.handleProcess();
    });

    act(() => result.current.handleToggleShowOnlyChanged(true));

    expect(result.current.filteredResults).toHaveLength(1);
    expect(result.current.filteredResults[0].original).toBe('a');
  });
});

describe('useDefanger — handleSetOperation', () => {
  it('does nothing when re-selecting the same operation', async () => {
    const { result } = renderHook(() => useDefanger());

    await act(async () => {
      await result.current.handleSetOperation('defang');
    });

    expect(defangApi.batchProcessIOCs).not.toHaveBeenCalled();
  });

  it('re-processes existing results under the new operation', async () => {
    defangApi.batchProcessIOCs
      .mockResolvedValueOnce([{ original: 'a', processed: 'a[.]', types: ['Domain'], changed: true }])
      .mockResolvedValueOnce([{ original: 'a', processed: 'a', types: ['Domain'], changed: false }]);
    const { result } = renderHook(() => useDefanger());
    act(() => result.current.handleInputChange('a'));
    await act(async () => {
      await result.current.handleProcess();
    });

    await act(async () => {
      await result.current.handleSetOperation('fang');
    });

    expect(defangApi.batchProcessIOCs).toHaveBeenLastCalledWith('a', 'fang');
    expect(result.current.operation).toBe('fang');
  });

  it('switches the operation without re-processing when there are no results yet', async () => {
    const { result } = renderHook(() => useDefanger());

    await act(async () => {
      await result.current.handleSetOperation('fang');
    });

    expect(result.current.operation).toBe('fang');
    expect(defangApi.batchProcessIOCs).not.toHaveBeenCalled();
  });
});

describe('useDefanger — handleCopy', () => {
  it('copies text and shows a success snackbar', async () => {
    const { result } = renderHook(() => useDefanger());

    await act(async () => {
      result.current.handleCopy('1[.]2[.]3[.]4', 'Result');
    });

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('1[.]2[.]3[.]4');
    expect(result.current.snackbar).toMatchObject({ open: true, severity: 'success' });
  });

  it('shows an error snackbar when the clipboard write fails', async () => {
    navigator.clipboard.writeText.mockRejectedValueOnce(new Error('denied'));
    const { result } = renderHook(() => useDefanger());

    await act(async () => {
      result.current.handleCopy('x');
    });

    expect(result.current.snackbar).toMatchObject({ open: true, severity: 'error' });
  });
});

describe('useDefanger — handleClear', () => {
  it('resets the input text and results', async () => {
    defangApi.batchProcessIOCs.mockResolvedValue([
      { original: 'a', processed: 'a', types: ['Domain'], changed: false },
    ]);
    const { result } = renderHook(() => useDefanger());
    act(() => result.current.handleInputChange('a'));
    await act(async () => {
      await result.current.handleProcess();
    });

    act(() => result.current.handleClear());

    expect(result.current.inputText).toBe('');
    expect(result.current.results).toEqual([]);
    expect(result.current.hasResults).toBe(false);
  });
});
