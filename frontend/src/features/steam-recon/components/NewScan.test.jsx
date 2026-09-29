import { screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NewScan from './NewScan';
import { useSteamReconScan } from '../hooks/useSteamReconScan';
import { renderFeatureRoute } from '../../../core/testUtils/renderFeatureRoute';

vi.mock('../hooks/useSteamReconScan');

const SCAN_RESULT = {
  status: 'completed',
  result: {
    profile: { persona_name: 'Robin' },
    close_friends: [{ steamid64: '1', persona_name: 'Alice', mutual_count: 3, vac_banned: false, game_banned: false }],
    geolocation: { confidence: 'low', num_voters: 0, coverage: 0, countries: [], states: [], cities: [], self_declared: null },
    cheater_report: null,
  },
};

function mockScan(overrides = {}) {
  const startScan = vi.fn();
  const cancelScan = vi.fn();
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
    cancelScan,
    ...overrides,
  });
  return { startScan, cancelScan };
}

function renderPage() {
  return renderFeatureRoute(NewScan, 'steam-recon/new', ['/steam-recon/new']);
}

afterEach(() => vi.clearAllMocks());

describe('NewScan', () => {
  it('shows only the form before any scan has run', () => {
    mockScan();
    renderPage();

    expect(screen.getByRole('button', { name: /start scan/i })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /close friends/i })).not.toBeInTheDocument();
  });

  it('submits the form through startScan', async () => {
    const { startScan } = mockScan();
    renderPage();

    await userEvent.type(screen.getByLabelText(/steam id, profile url/i), 'robinwalker');
    fireEvent.submit(screen.getByRole('button', { name: /start scan/i }).closest('form'));

    expect(startScan).toHaveBeenCalledWith('robinwalker', expect.objectContaining({ includeCsReport: true }));
  });

  it('shows live progress while running', () => {
    mockScan({ phase: 'running', stage: 'resolving' });
    renderPage();

    expect(screen.getByText(/resolving target/i)).toBeInTheDocument();
  });

  it('renders the friend graph, geolocation and close-friends table once completed', () => {
    mockScan({ phase: 'completed', result: SCAN_RESULT });
    renderPage();

    expect(screen.getByRole('heading', { name: /friends graph/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /geolocation hypothesis/i })).toBeInTheDocument();
    // Alice appears twice: the friend graph's SVG label and the close-friends table row.
    expect(screen.getAllByText('Alice').length).toBeGreaterThan(0);
  });

  it('omits the cheater report card when it was not requested', () => {
    mockScan({ phase: 'completed', result: SCAN_RESULT });
    renderPage();

    expect(screen.queryByRole('heading', { name: /cheater-probability report/i })).not.toBeInTheDocument();
  });

  it('renders the cheater report card when present', () => {
    const withReport = {
      ...SCAN_RESULT,
      result: {
        ...SCAN_RESULT.result,
        cheater_report: {
          probability: 0.1,
          level: 'low',
          coverage: 0.4,
          already_banned: false,
          signals: [],
        },
      },
    };
    mockScan({ phase: 'completed', result: withReport });
    renderPage();

    expect(screen.getByRole('heading', { name: /cheater-probability report/i })).toBeInTheDocument();
  });
});
