import { screen } from '@testing-library/react';
import PhoneSearch from './PhoneSearch';
import { usePhoneSearchScan } from './hooks/usePhoneSearchScan';
import { phoneSearchApi } from './services/api/phoneSearchApi';
import { renderFeatureRoute } from '../../core/testUtils/renderFeatureRoute';

vi.mock('./hooks/usePhoneSearchScan');
vi.mock('./services/api/phoneSearchApi');

function renderPhoneSearch(initialEntries) {
  return renderFeatureRoute(PhoneSearch, 'phone-search', initialEntries);
}

describe('PhoneSearch — cross-feature prefill (command palette pivot)', () => {
  let startScan;

  beforeEach(() => {
    startScan = vi.fn();
    usePhoneSearchScan.mockReturnValue({ phase: 'idle', startScan, cancelScan: vi.fn(), reset: vi.fn() });
    phoneSearchApi.getInfo = vi.fn().mockResolvedValue(null);
  });

  afterEach(() => vi.clearAllMocks());

  it('preserves ?q= through the index -> new redirect and prefills the phone number field', () => {
    renderPhoneSearch(['/phone-search?q=%2B15551234567']);

    expect(screen.getByLabelText(/phone number/i).value).toBe('+15551234567');
  });

  it('auto-runs the search with the prefilled value', () => {
    renderPhoneSearch(['/phone-search?q=%2B15551234567']);

    expect(startScan).toHaveBeenCalledWith('+15551234567');
  });

  it('leaves the field empty and does not search with no prefill value', () => {
    renderPhoneSearch(['/phone-search']);

    expect(screen.getByLabelText(/phone number/i).value).toBe('');
    expect(startScan).not.toHaveBeenCalled();
  });
});
