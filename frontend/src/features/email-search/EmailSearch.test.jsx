import { screen } from '@testing-library/react';
import EmailSearch from './EmailSearch';
import { useEmailSearchScan } from './hooks/useEmailSearchScan';
import { emailSearchApi } from './services/api/emailSearchApi';
import { renderFeatureRoute } from '../../core/testUtils/renderFeatureRoute';

vi.mock('./hooks/useEmailSearchScan');
vi.mock('./services/api/emailSearchApi');

function renderEmailSearch(initialEntries) {
  return renderFeatureRoute(EmailSearch, 'email-search', initialEntries);
}

describe('EmailSearch — cross-feature prefill (command palette pivot)', () => {
  let startScan;

  beforeEach(() => {
    startScan = vi.fn();
    useEmailSearchScan.mockReturnValue({ phase: 'idle', startScan, cancelScan: vi.fn(), reset: vi.fn() });
    emailSearchApi.getInfo = vi.fn().mockResolvedValue(null);
  });

  afterEach(() => vi.clearAllMocks());

  it('preserves ?q= through the index -> new redirect and prefills the username field', () => {
    renderEmailSearch(['/email-search?q=john_doe']);

    expect(screen.getByLabelText(/username/i).value).toBe('john_doe');
  });

  it('auto-runs the search with the prefilled value', () => {
    renderEmailSearch(['/email-search?q=john_doe']);

    expect(startScan).toHaveBeenCalledWith('john_doe');
  });

  it('leaves the field empty and does not search with no prefill value', () => {
    renderEmailSearch(['/email-search']);

    expect(screen.getByLabelText(/username/i).value).toBe('');
    expect(startScan).not.toHaveBeenCalled();
  });
});
