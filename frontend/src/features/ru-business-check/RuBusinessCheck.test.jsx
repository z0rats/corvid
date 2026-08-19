import { screen } from '@testing-library/react';
import RuBusinessCheck from './RuBusinessCheck';
import { useRuBusinessCheck } from './hooks/useRuBusinessCheck';
import { renderFeatureRoute } from '../../core/testUtils/renderFeatureRoute';

vi.mock('./hooks/useRuBusinessCheck');

function renderRuBusinessCheck(initialEntries) {
  return renderFeatureRoute(RuBusinessCheck, 'ru-business-check', initialEntries);
}

describe('RuBusinessCheck — cross-feature prefill (command palette pivot)', () => {
  let scan;

  beforeEach(() => {
    scan = vi.fn();
    useRuBusinessCheck.mockReturnValue({ result: null, loading: false, error: null, scan });
  });

  afterEach(() => vi.clearAllMocks());

  it('preserves ?q= through the index -> new redirect and prefills the query field', () => {
    renderRuBusinessCheck(['/ru-business-check?q=7712345678']);

    expect(screen.getByLabelText(/ИНН или название/i).value).toBe('7712345678');
  });

  it('auto-runs the scan with the prefilled value', () => {
    renderRuBusinessCheck(['/ru-business-check?q=7712345678']);

    expect(scan).toHaveBeenCalledWith({ query: '7712345678', force_refresh: false });
  });

  it('leaves the field empty and does not scan with no prefill value', () => {
    renderRuBusinessCheck(['/ru-business-check']);

    expect(scan).not.toHaveBeenCalled();
  });
});
