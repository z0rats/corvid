import { screen } from '@testing-library/react';
import SteamRecon from './SteamRecon';
import { useSteamReconScan } from './hooks/useSteamReconScan';
import { renderFeatureRoute } from '../../core/testUtils/renderFeatureRoute';

vi.mock('./hooks/useSteamReconScan');

function renderSteamRecon(initialEntries) {
  return renderFeatureRoute(SteamRecon, 'steam-recon', initialEntries);
}

describe('SteamRecon — cross-feature prefill (command palette pivot)', () => {
  let startScan;

  beforeEach(() => {
    startScan = vi.fn();
    useSteamReconScan.mockReturnValue({
      phase: 'idle',
      target: '',
      stage: '',
      friendsTotal: 0,
      analyzed: 0,
      candidatesSelected: 0,
      result: null,
      error: '',
      startScan,
      cancelScan: vi.fn(),
    });
  });

  afterEach(() => vi.clearAllMocks());

  it('redirects the index route to the New Scan tab, preserving ?q=', () => {
    renderSteamRecon(['/steam-recon?q=76561197960435530']);

    expect(screen.getByLabelText(/steam id, profile url/i).value).toBe('76561197960435530');
  });

  it('auto-starts the scan with the prefilled value', () => {
    renderSteamRecon(['/steam-recon?q=76561197960435530']);

    expect(startScan).toHaveBeenCalledWith(
      '76561197960435530',
      expect.objectContaining({ includeCsReport: true }),
    );
  });

  it('leaves the field empty and does not start a scan with no prefill value', () => {
    renderSteamRecon(['/steam-recon']);

    expect(startScan).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/steam id, profile url/i).value).toBe('');
  });

  it('routes directly to the profile tab', () => {
    renderSteamRecon(['/steam-recon/profile']);

    expect(screen.getByRole('button', { name: /look up/i })).toBeInTheDocument();
  });
});
