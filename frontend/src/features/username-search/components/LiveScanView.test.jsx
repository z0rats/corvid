import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import LiveScanView from './LiveScanView';
import { buildInitialState } from '../state/scanAtoms';

const scan = (overrides) => ({
  ...buildInitialState('site_check'),
  phase: 'completed',
  username: 'jsmith_dev',
  siteNames: ['Twitter'],
  totalSites: 1,
  checked: 1,
  cancelScan: vi.fn(),
  ...overrides,
});

const renderView = (s) => render(
  <MemoryRouter><LiveScanView scan={s} onSearchUsername={() => {}} /></MemoryRouter>,
);

describe('LiveScanView: one-site check outcome', () => {
  it('warns that a blocked check is inconclusive instead of reporting no profiles', () => {
    renderView(scan({ siteStatuses: { Twitter: 'unknown' } }));

    expect(screen.getByRole('alert')).toHaveTextContent(/could not check twitter/i);
    expect(screen.queryByText('No profiles found')).not.toBeInTheDocument();
    expect(screen.queryByText(/Checked 1 sites/)).not.toBeInTheDocument();
  });

  it('reports a clean negative as usual when the site answered', () => {
    renderView(scan({ siteStatuses: { Twitter: 'available' } }));

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByText('No profiles found')).toBeInTheDocument();
  });

  it('still lists a found profile', () => {
    renderView(scan({
      siteStatuses: { Twitter: 'claimed' },
      foundSites: [{ site_name: 'Twitter', url_user: 'https://twitter.com/jsmith_dev' }],
    }));

    expect(screen.getByText('https://twitter.com/jsmith_dev')).toBeInTheDocument();
  });
});
