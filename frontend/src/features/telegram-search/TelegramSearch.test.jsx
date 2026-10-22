import { screen } from '@testing-library/react';
import TelegramSearch from './TelegramSearch';
import { useTelegramScan } from './hooks/useTelegramScan';
import { renderFeatureRoute } from '../../core/testUtils/renderFeatureRoute';

vi.mock('./hooks/useTelegramScan');
vi.mock('./services/api/telegramSearchApi', () => ({
  telegramSearchApi: { listSearches: vi.fn().mockResolvedValue([]), getSearch: vi.fn(), deleteSearch: vi.fn() },
}));

function renderTelegramSearch(initialEntries) {
  return renderFeatureRoute(TelegramSearch, 'telegram-search', initialEntries);
}

describe('TelegramSearch — cross-feature prefill (command palette pivot)', () => {
  let startScan;
  let scanState;

  beforeEach(() => {
    startScan = vi.fn();
    scanState = {
      phase: 'idle',
      target: '',
      stage: '',
      sampled: 0,
      sampleTarget: 0,
      title: '',
      result: null,
      error: '',
      startScan,
      cancelScan: vi.fn(),
    };
    useTelegramScan.mockImplementation(() => scanState);
  });

  afterEach(() => vi.clearAllMocks());

  it('redirects the index route to the New Scan tab, preserving ?q=', () => {
    renderTelegramSearch(['/telegram-search?q=durov']);

    expect(screen.getByLabelText(/channel or group/i).value).toBe('durov');
  });

  it('auto-starts the scan with the prefilled value and the default sample size', () => {
    renderTelegramSearch(['/telegram-search?q=https%3A%2F%2Ft.me%2Fs%2Fdurov']);

    expect(startScan).toHaveBeenCalledWith('https://t.me/s/durov', { maxPosts: 100 });
  });

  it('leaves the field empty and does not start a scan with no prefill value', () => {
    renderTelegramSearch(['/telegram-search']);

    expect(startScan).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/channel or group/i).value).toBe('');
  });

  it('shows the scanned target in the field once a scan is running', () => {
    scanState = { ...scanState, phase: 'running', target: '@tginfo', stage: 'profile' };
    renderTelegramSearch(['/telegram-search/new']);

    expect(screen.getByLabelText(/channel or group/i).value).toBe('@tginfo');
    expect(screen.getByText(/reading the channel card/i)).toBeInTheDocument();
  });

  it('routes to the history tab', async () => {
    renderTelegramSearch(['/telegram-search/history']);

    expect(await screen.findByText(/no channel scans yet/i)).toBeInTheDocument();
  });
});
