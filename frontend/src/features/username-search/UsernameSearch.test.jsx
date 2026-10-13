import { screen } from '@testing-library/react';
import UsernameSearch from './UsernameSearch';
import { useUsernameSearchScan } from './hooks/useUsernameSearchScan';
import { usernameSearchApi } from './services/api/usernameSearchApi';
import { renderFeatureRoute } from '../../core/testUtils/renderFeatureRoute';

vi.mock('./hooks/useUsernameSearchScan');
vi.mock('./services/api/usernameSearchApi');

function renderUsernameSearch(initialEntries) {
  return renderFeatureRoute(UsernameSearch, 'username-search', initialEntries);
}

describe('UsernameSearch — cross-feature prefill (command palette pivot)', () => {
  let startScan;

  beforeEach(() => {
    startScan = vi.fn();
    useUsernameSearchScan.mockReturnValue({ phase: 'idle', startScan, cancelScan: vi.fn(), reset: vi.fn() });
    usernameSearchApi.getTags = vi.fn().mockResolvedValue([]);
    usernameSearchApi.getInfo = vi.fn().mockResolvedValue([]);
  });

  afterEach(() => vi.clearAllMocks());

  it('preserves ?q= through the index -> new redirect and prefills the username field', () => {
    renderUsernameSearch(['/username-search?q=john_doe']);

    expect(screen.getByLabelText(/username/i).value).toBe('john_doe');
  });

  it('auto-runs the search with the prefilled value', () => {
    renderUsernameSearch(['/username-search?q=john_doe']);

    expect(startScan).toHaveBeenCalledWith('john_doe', { parentSearchId: undefined, pivotSource: undefined });
  });

  it('keeps the run a history pivot came from (?parent=&src=) on the auto-run search', () => {
    renderUsernameSearch(['/username-search?q=john_doe&parent=7&src=link%20on%20GitHub']);

    expect(startScan).toHaveBeenCalledWith('john_doe', { parentSearchId: 7, pivotSource: 'link on GitHub' });
  });

  it('runs a one-site check instead of a full scan when ?site= comes along', () => {
    renderUsernameSearch(['/username-search?q=john_doe&parent=7&site=Twitter&src=link']);

    expect(startScan).toHaveBeenCalledTimes(1);
    expect(startScan).toHaveBeenCalledWith('john_doe', { siteNames: ['Twitter'], parentSearchId: 7, pivotSource: 'link' });
  });

  it('ignores a malformed ?parent= instead of sending it', () => {
    renderUsernameSearch(['/username-search?q=john_doe&parent=abc']);

    expect(startScan).toHaveBeenCalledWith('john_doe', { parentSearchId: undefined, pivotSource: undefined });
  });

  it('leaves the field empty and does not search with no prefill value', () => {
    renderUsernameSearch(['/username-search']);

    expect(screen.getByLabelText(/username/i).value).toBe('');
    expect(startScan).not.toHaveBeenCalled();
  });
});
