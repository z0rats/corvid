import { renderHook, act, waitFor } from '@testing-library/react';
import { generateMarkdown, downloadMarkdown } from './reportUtils';
import { formatDate, formatTimeRange, formatNumber, truncateText } from './formatters';
import { parseIOCs, parseAnalysisResult } from './iocParser';
import { useTrendsFetch } from '../hooks/api/useTrendsFetch';
import { useNewsfeedSettings } from '../hooks/api/useSettingsApi';
import { newsfeedSettingsApi } from '../services/api/settingsApi';

vi.mock('../services/api/settingsApi', () => ({
  newsfeedSettingsApi: { getConfig: vi.fn(), updateConfig: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('generateMarkdown', () => {
  it('renders ranking and per-article analysis sections', () => {
    const md = generateMarkdown(
      [{ title: 'Big breach', reason: 'Affects our sector' }],
      [{
        title: 'Big breach',
        analysis: {
          Risk: 'High', Summary: 'S', 'Analysis comment': 'C', 'Action items': ['Patch', 'Rotate keys'], Source: 'https://x',
        },
      }],
    );
    expect(md).toContain('**1. Big breach**');
    expect(md).toContain('- **Reason**: Affects our sector');
    expect(md).toContain('### 1. Big breach');
    expect(md).toContain('- **Risk**: High');
    expect(md).toContain('  - Patch\n  - Rotate keys\n');
    expect(md).toContain('- **Source**: https://x');
  });

  it('handles empty inputs and missing action items', () => {
    const empty = generateMarkdown([], []);
    expect(empty).toContain('_No articles were ranked._');
    expect(empty).toContain('_No detailed analysis yet._');
    const noItems = generateMarkdown([], [{ title: 't', analysis: { Risk: 'Low' } }]);
    expect(noItems).toContain('- **Possible Action Items**:\n- **Source**');
  });

  it('downloadMarkdown creates and revokes a blob link', () => {
    URL.createObjectURL = vi.fn(() => 'blob:x');
    URL.revokeObjectURL = vi.fn();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    downloadMarkdown('# hi', 'r.md');
    expect(click).toHaveBeenCalledTimes(1);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:x');
    expect(document.querySelector('a[download]')).toBeNull();
    click.mockRestore();
  });
});

describe('formatters', () => {
  it('formatDate', () => {
    expect(formatDate('')).toBe('');
    expect(formatDate('2026-10-01T10:00:00Z')).toMatch(/Oct 1, 2026/);
  });

  it('formatTimeRange maps known ranges and passes others through', () => {
    expect(formatTimeRange('7d')).toBe('7 days');
    expect(formatTimeRange('12h')).toBe('12h');
  });

  it('formatNumber', () => {
    expect(formatNumber(999)).toBe('999');
    expect(formatNumber(1500)).toBe('1.5K');
    expect(formatNumber(2_500_000)).toBe('2.5M');
  });

  it('truncateText', () => {
    expect(truncateText('short', 10)).toBe('short');
    expect(truncateText('abcdefghij', 3)).toBe('abc...');
    expect(truncateText(null)).toBe(null);
  });
});

describe('iocParser', () => {
  it('parses JSON strings, passes objects through, and tolerates junk', () => {
    expect(parseIOCs('{"ips":["1.1.1.1"]}')).toEqual({ ips: ['1.1.1.1'] });
    expect(parseIOCs({ a: 1 })).toEqual({ a: 1 });
    expect(parseIOCs('{bad')).toEqual({});
    expect(parseIOCs(null)).toEqual({});
    expect(parseAnalysisResult('{"s":1}')).toEqual({ s: 1 });
    expect(parseAnalysisResult('{bad')).toBe(null);
    expect(parseAnalysisResult(undefined)).toBe(null);
  });
});

describe('useTrendsFetch', () => {
  it('returns array results and coerces anything else to []', async () => {
    const api = vi.fn().mockResolvedValueOnce([{ k: 1 }]).mockResolvedValueOnce({ not: 'array' });
    const { result, rerender } = renderHook(({ d }) => useTrendsFetch(api, ['7d'], [d]), { initialProps: { d: 1 } });
    await waitFor(() => expect(result.current.data).toEqual([{ k: 1 }]));
    expect(api).toHaveBeenCalledWith('7d');
    rerender({ d: 2 });
    await waitFor(() => expect(api).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(result.current.data).toEqual([]));
  });

  it('exposes the error message', async () => {
    const api = vi.fn().mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useTrendsFetch(api, [], []));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('boom');
  });
});

describe('useNewsfeedSettings.updateConfig validation', () => {
  async function setup() {
    newsfeedSettingsApi.getConfig.mockResolvedValue({ retention_days: 30, fetch_interval_minutes: 10 });
    newsfeedSettingsApi.updateConfig.mockImplementation(async (c) => c);
    const hook = renderHook(() => useNewsfeedSettings());
    await waitFor(() => expect(hook.result.current.config.fetch_interval_minutes).toBe(10));
    return hook.result;
  }

  it.each([
    [{ fetch_interval_minutes: 4 }, 'at least 5'],
    [{ fetch_interval_minutes: 721 }, 'at most 720'],
    [{ retention_days: -1 }, 'Retention period'],
  ])('rejects %j without calling the API', async (update, msg) => {
    const result = await setup();
    let out;
    await act(async () => { out = await result.current.updateConfig(update); });
    expect(out.success).toBe(false);
    expect(out.error.message).toContain(msg);
    expect(newsfeedSettingsApi.updateConfig).not.toHaveBeenCalled();
  });

  it('accepts the bounds', async () => {
    const result = await setup();
    await act(async () => { await result.current.updateConfig({ fetch_interval_minutes: 5, retention_days: 0 }); });
    expect(newsfeedSettingsApi.updateConfig).toHaveBeenCalled();
  });
});
