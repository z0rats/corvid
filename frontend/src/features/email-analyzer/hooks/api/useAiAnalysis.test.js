import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useAiAnalysis } from './useAiAnalysis';
import { apiKeysState } from '../../../../core/state/atoms';
import { aiAssistantApi } from '../../services/api/aiAssistantApi';

vi.mock('../../services/api/aiAssistantApi');

// apiKeysState is module-scoped, so it doesn't reset between tests on its own.
function setApiKeys(keys) {
  const { result } = renderHook(() => useSetAtom(apiKeysState));
  act(() => result.current(keys));
}

beforeEach(() => setApiKeys({}));
afterEach(() => vi.clearAllMocks());

describe('useAiAnalysis', () => {
  it('starts with no result and hasLlmKey false when no LLM key is configured', () => {
    const { result } = renderHook(() => useAiAnalysis());

    expect(result.current).toMatchObject({ result: null, loading: false, hasLlmKey: false });
  });

  it('reflects hasLlmKey true when an LLM key is configured', () => {
    setApiKeys({ openai: 'sk-x' });

    const { result } = renderHook(() => useAiAnalysis());

    expect(result.current.hasLlmKey).toBe(true);
  });

  it('analyzeMailBody sets loading then populates the result', async () => {
    aiAssistantApi.analyzeMailBody.mockResolvedValue('phishing indicators found');
    const { result } = renderHook(() => useAiAnalysis());

    let promise;
    act(() => { promise = result.current.analyzeMailBody('body text'); });
    expect(result.current.loading).toBe(true);
    await act(async () => promise);

    expect(aiAssistantApi.analyzeMailBody).toHaveBeenCalledWith('body text');
    expect(result.current.result).toBe('phishing indicators found');
    expect(result.current.loading).toBe(false);
  });

  it('clears loading without throwing when the API call fails', async () => {
    aiAssistantApi.analyzeMailBody.mockRejectedValue(new Error('down'));
    const { result } = renderHook(() => useAiAnalysis());

    await act(async () => result.current.analyzeMailBody('body text'));

    expect(result.current.loading).toBe(false);
    expect(result.current.result).toBeNull();
  });
});
