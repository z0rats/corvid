import { act, renderHook, waitFor } from '@testing-library/react';
import { useDorkRunner } from './useDorkRunner';
import { dorkRunnerApi } from '../../services/api/dorkRunnerApi';

vi.mock('../../services/api/dorkRunnerApi');
vi.mock('../../../../core/hooks/usePrefillFromQuery', () => ({
  usePrefillFromQuery: vi.fn(),
}));

afterEach(() => vi.clearAllMocks());

describe('useDorkRunner — template loading', () => {
  it('loads templates on mount and selects all of them by default', async () => {
    dorkRunnerApi.getTemplates.mockResolvedValue([{ key: 'a' }, { key: 'b' }]);

    const { result } = renderHook(() => useDorkRunner());

    await waitFor(() => expect(result.current.templates).toEqual([{ key: 'a' }, { key: 'b' }]));
    expect(result.current.selectedTemplateKeys).toEqual(['a', 'b']);
    expect(dorkRunnerApi.getTemplates).toHaveBeenCalledWith('domain');
  });

  it('re-fetches templates when targetType changes', async () => {
    dorkRunnerApi.getTemplates.mockResolvedValue([]);
    const { result } = renderHook(() => useDorkRunner());
    await waitFor(() => expect(dorkRunnerApi.getTemplates).toHaveBeenCalledTimes(1));

    act(() => result.current.setTargetType('username'));

    await waitFor(() => expect(dorkRunnerApi.getTemplates).toHaveBeenCalledTimes(2));
    expect(dorkRunnerApi.getTemplates).toHaveBeenLastCalledWith('username');
  });

  it('does not throw when template loading fails', async () => {
    dorkRunnerApi.getTemplates.mockRejectedValue(new Error('network down'));

    const { result } = renderHook(() => useDorkRunner());

    await waitFor(() => expect(result.current.templates).toEqual([]));
  });
});

describe('useDorkRunner — toggleTemplate', () => {
  it('deselects a selected key and reselects it back', async () => {
    dorkRunnerApi.getTemplates.mockResolvedValue([{ key: 'a' }, { key: 'b' }]);
    const { result } = renderHook(() => useDorkRunner());
    await waitFor(() => expect(result.current.selectedTemplateKeys).toEqual(['a', 'b']));

    act(() => result.current.toggleTemplate('a'));
    expect(result.current.selectedTemplateKeys).toEqual(['b']);

    act(() => result.current.toggleTemplate('a'));
    expect(result.current.selectedTemplateKeys).toEqual(['b', 'a']);
  });
});

describe('useDorkRunner — runDorks', () => {
  it('does nothing for a blank target', async () => {
    dorkRunnerApi.getTemplates.mockResolvedValue([]);
    const { result } = renderHook(() => useDorkRunner());

    await act(async () => result.current.runDorks('   '));

    expect(dorkRunnerApi.runDorks).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });

  it('runs with the trimmed target and current settings, populating the result', async () => {
    dorkRunnerApi.getTemplates.mockResolvedValue([{ key: 'a' }]);
    dorkRunnerApi.runDorks.mockResolvedValue({ results: [{ url: 'https://x.example' }] });
    const { result } = renderHook(() => useDorkRunner());
    await waitFor(() => expect(result.current.selectedTemplateKeys).toEqual(['a']));
    act(() => result.current.setTarget('  example.com  '));

    await act(async () => result.current.runDorks());

    expect(dorkRunnerApi.runDorks).toHaveBeenCalledWith({
      target: 'example.com',
      targetType: 'domain',
      engine: 'duckduckgo',
      templateKeys: ['a'],
    });
    expect(result.current.result).toEqual({ results: [{ url: 'https://x.example' }] });
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('runs with an explicit target override instead of the target state', async () => {
    dorkRunnerApi.getTemplates.mockResolvedValue([]);
    dorkRunnerApi.runDorks.mockResolvedValue({ results: [] });
    const { result } = renderHook(() => useDorkRunner());
    await waitFor(() => expect(dorkRunnerApi.getTemplates).toHaveBeenCalled());

    await act(async () => result.current.runDorks('override.example'));

    expect(dorkRunnerApi.runDorks).toHaveBeenCalledWith(
      expect.objectContaining({ target: 'override.example' }),
    );
  });

  it('sends undefined templateKeys when none are selected', async () => {
    dorkRunnerApi.getTemplates.mockResolvedValue([]);
    dorkRunnerApi.runDorks.mockResolvedValue({ results: [] });
    const { result } = renderHook(() => useDorkRunner());
    await waitFor(() => expect(dorkRunnerApi.getTemplates).toHaveBeenCalled());

    await act(async () => result.current.runDorks('example.com'));

    expect(dorkRunnerApi.runDorks).toHaveBeenCalledWith(
      expect.objectContaining({ templateKeys: undefined }),
    );
  });

  it('surfaces the API error message and clears loading', async () => {
    dorkRunnerApi.getTemplates.mockResolvedValue([]);
    dorkRunnerApi.runDorks.mockRejectedValue(new Error('Dork run failed'));
    const { result } = renderHook(() => useDorkRunner());
    await waitFor(() => expect(dorkRunnerApi.getTemplates).toHaveBeenCalled());

    await act(async () => result.current.runDorks('example.com'));

    expect(result.current.error).toBe('Dork run failed');
    expect(result.current.loading).toBe(false);
    expect(result.current.result).toBeNull();
  });

  it('prefers the response detail message over the generic error message', async () => {
    dorkRunnerApi.getTemplates.mockResolvedValue([]);
    dorkRunnerApi.runDorks.mockRejectedValue({ response: { data: { detail: 'Engine blocked' } } });
    const { result } = renderHook(() => useDorkRunner());
    await waitFor(() => expect(dorkRunnerApi.getTemplates).toHaveBeenCalled());

    await act(async () => result.current.runDorks('example.com'));

    expect(result.current.error).toBe('Engine blocked');
  });
});
