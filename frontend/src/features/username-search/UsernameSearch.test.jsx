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

    expect(startScan).toHaveBeenCalledWith('john_doe');
  });

  it('leaves the field empty and does not search with no prefill value', () => {
    renderUsernameSearch(['/username-search']);

    expect(screen.getByLabelText(/username/i).value).toBe('');
    expect(startScan).not.toHaveBeenCalled();
  });
});
