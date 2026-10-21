import { renderHook, act, waitFor } from '@testing-library/react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import { useKeywordSettings } from './useKeywordSettingsApi';
import { useTrendsBlacklist } from './useTrendsBlacklistApi';
import { useCtiSettings } from './useCtiSettingsApi';

vi.mock('../../services/api/settingsApi', () => ({
  newsfeedSettingsApi: {
    getConfig: vi.fn(), updateConfig: vi.fn(),
    getKeywords: vi.fn(), addKeyword: vi.fn(), deleteKeyword: vi.fn(),
    getBlacklistEntries: vi.fn(), addBlacklistEntry: vi.fn(), deleteBlacklistEntry: vi.fn(),
    getCtiSettings: vi.fn(), updateCtiSettings: vi.fn(),
  },
}));

afterEach(() => vi.clearAllMocks());

async function call(result, fn, ...args) {
  let out;
  await act(async () => { out = await result.current[fn](...args); });
  return out;
}

describe('useKeywordSettings', () => {
  async function setup() {
    newsfeedSettingsApi.getConfig.mockResolvedValue({ keyword_matching_enabled: false, fetch_interval: 30 });
    newsfeedSettingsApi.getKeywords.mockResolvedValue([{ id: 1, keyword: 'LockBit' }]);
    const hook = renderHook(() => useKeywordSettings());
    await waitFor(() => expect(hook.result.current.loading).toBe(false));
    return hook.result;
  }

  it('loads config and keywords together', async () => {
    const result = await setup();
    expect(result.current.keywordMatchingEnabled).toBe(false);
    expect(result.current.keywords).toEqual([{ id: 1, keyword: 'LockBit' }]);
  });

  it('a load failure is exposed as error', async () => {
    newsfeedSettingsApi.getConfig.mockRejectedValue(new Error('500'));
    newsfeedSettingsApi.getKeywords.mockResolvedValue([]);
    const { result } = renderHook(() => useKeywordSettings());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBeInstanceOf(Error);
  });

  it('toggling sends the full config so other fields are not reset', async () => {
    const result = await setup();
    newsfeedSettingsApi.updateConfig.mockResolvedValue({ keyword_matching_enabled: true, fetch_interval: 30 });
    expect(await call(result, 'toggleKeywordMatching', true)).toEqual({ success: true });
    expect(newsfeedSettingsApi.updateConfig).toHaveBeenCalledWith({ keyword_matching_enabled: true, fetch_interval: 30 });
    expect(result.current.keywordMatchingEnabled).toBe(true);
  });

  it('a failed toggle rolls the switch back', async () => {
    const result = await setup();
    newsfeedSettingsApi.updateConfig.mockRejectedValue(new Error('x'));
    expect((await call(result, 'toggleKeywordMatching', true)).success).toBe(false);
    expect(result.current.keywordMatchingEnabled).toBe(false);
  });

  it('rejects case-insensitive duplicates without calling the API', async () => {
    const result = await setup();
    expect(await call(result, 'addKeyword', 'lockbit')).toEqual({ success: false, duplicate: true });
    expect(newsfeedSettingsApi.addKeyword).not.toHaveBeenCalled();
  });

  it('adds and deletes keywords', async () => {
    const result = await setup();
    newsfeedSettingsApi.addKeyword.mockResolvedValue({ id: 2, keyword: 'Akira' });
    await call(result, 'addKeyword', 'Akira');
    expect(result.current.keywords.map((k) => k.keyword)).toEqual(['LockBit', 'Akira']);

    newsfeedSettingsApi.deleteKeyword.mockResolvedValue({});
    await call(result, 'deleteKeyword', 1);
    expect(result.current.keywords.map((k) => k.id)).toEqual([2]);
  });

  it('API errors on add/delete leave the list untouched', async () => {
    const result = await setup();
    newsfeedSettingsApi.addKeyword.mockRejectedValue(new Error('x'));
    newsfeedSettingsApi.deleteKeyword.mockRejectedValue(new Error('x'));
    expect((await call(result, 'addKeyword', 'New')).success).toBe(false);
    expect((await call(result, 'deleteKeyword', 1)).success).toBe(false);
    expect(result.current.keywords).toHaveLength(1);
  });
});

describe('useTrendsBlacklist', () => {
  async function setup() {
    newsfeedSettingsApi.getBlacklistEntries.mockImplementation(async (type) => (
      type === 'word' ? [{ id: 1, value: 'Microsoft' }] : [{ id: 2, value: '8.8.8.8' }]
    ));
    const hook = renderHook(() => useTrendsBlacklist());
    await waitFor(() => expect(hook.result.current.loading).toBe(false));
    return hook.result;
  }

  it('loads both lists', async () => {
    const result = await setup();
    expect(result.current.wordBlacklist).toEqual([{ id: 1, value: 'Microsoft' }]);
    expect(result.current.iocBlacklist).toEqual([{ id: 2, value: '8.8.8.8' }]);
  });

  it('checks duplicates only within the same list', async () => {
    const result = await setup();
    expect(await call(result, 'addToBlacklist', 'microsoft', 'word')).toEqual({ success: false, duplicate: true });

    newsfeedSettingsApi.addBlacklistEntry.mockResolvedValue({ id: 3, value: 'microsoft' });
    expect(await call(result, 'addToBlacklist', 'microsoft', 'ioc')).toEqual({ success: true });
    expect(result.current.iocBlacklist.map((e) => e.id)).toEqual([2, 3]);
    expect(result.current.wordBlacklist).toHaveLength(1);
  });

  it('removes from the right list', async () => {
    const result = await setup();
    newsfeedSettingsApi.deleteBlacklistEntry.mockResolvedValue({});
    await call(result, 'removeFromBlacklist', 1, 'word');
    await call(result, 'removeFromBlacklist', 2, 'ioc');
    expect(result.current.wordBlacklist).toEqual([]);
    expect(result.current.iocBlacklist).toEqual([]);
  });

  it('errors are reported and lists stay as they were', async () => {
    const result = await setup();
    newsfeedSettingsApi.addBlacklistEntry.mockRejectedValue(new Error('x'));
    newsfeedSettingsApi.deleteBlacklistEntry.mockRejectedValue(new Error('x'));
    expect((await call(result, 'addToBlacklist', 'new', 'word')).success).toBe(false);
    expect((await call(result, 'removeFromBlacklist', 1, 'word')).success).toBe(false);
    expect(result.current.wordBlacklist).toHaveLength(1);
  });

  it('a load failure leaves both lists empty', async () => {
    newsfeedSettingsApi.getBlacklistEntries.mockRejectedValue(new Error('x'));
    const { result } = renderHook(() => useTrendsBlacklist());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.wordBlacklist).toEqual([]);
  });
});

describe('useCtiSettings', () => {
  async function setup(settings = { org: { name: 'ACME' } }) {
    newsfeedSettingsApi.getCtiSettings.mockResolvedValue({ settings });
    const hook = renderHook(() => useCtiSettings());
    await waitFor(() => expect(hook.result.current.loading).toBe(false));
    return hook.result;
  }

  it('edits a field without dropping its siblings, and saves the result', async () => {
    const result = await setup({ org: { name: 'ACME', sector: 'finance' } });
    act(() => result.current.handleInputChange('org', 'name', 'Initech'));
    expect(result.current.ctiSettings.org).toEqual({ name: 'Initech', sector: 'finance' });

    newsfeedSettingsApi.updateCtiSettings.mockResolvedValue({});
    expect(await call(result, 'saveSettings')).toEqual({ success: true });
    expect(newsfeedSettingsApi.updateCtiSettings).toHaveBeenCalledWith({ org: { name: 'Initech', sector: 'finance' } });
  });

  it('attack-type priorities merge into a possibly missing section', async () => {
    const result = await setup({});
    act(() => result.current.handleAttackTypePriorityChange('ransomware', 'high'));
    act(() => result.current.handleAttackTypePriorityChange('phishing', 'low'));
    expect(result.current.ctiSettings.threat_actor_and_attack_type.attack_type_priorities).toEqual({
      ransomware: 'high', phishing: 'low',
    });
  });

  it('load and save failures are surfaced', async () => {
    newsfeedSettingsApi.getCtiSettings.mockRejectedValue(new Error('x'));
    const { result } = renderHook(() => useCtiSettings());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.ctiSettings).toEqual({});

    newsfeedSettingsApi.updateCtiSettings.mockRejectedValue(new Error('x'));
    expect((await call(result, 'saveSettings')).success).toBe(false);
  });

  it('missing settings payload defaults to empty', async () => {
    newsfeedSettingsApi.getCtiSettings.mockResolvedValue({});
    const { result } = renderHook(() => useCtiSettings());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.ctiSettings).toEqual({});
  });
});
