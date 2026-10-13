import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import HistoryDetail from './HistoryDetail';
import { usernameSearchApi } from '../services/api/usernameSearchApi';

vi.mock('../services/api/usernameSearchApi');
vi.mock('../hooks/api/useHudsonRockCheck', () => ({ useHudsonRockCheck: () => null }));

const run = (overrides = {}) => ({
  id: 9,
  username: 'jsmith_dev',
  source: 'maigret',
  status: 'completed',
  total_sites_checked: 1,
  found_count: 1,
  site_results: [],
  pivots: null,
  ...overrides,
});

const renderDetail = () => render(
  <MemoryRouter initialEntries={['/username-search/history/9']}>
    <Routes><Route path="/username-search/history/:id" element={<HistoryDetail />} /></Routes>
  </MemoryRouter>,
);

describe('HistoryDetail: followed-from line', () => {
  afterEach(() => vi.clearAllMocks());

  it('links to the parent run while it still exists', async () => {
    usernameSearchApi.getRun.mockResolvedValue(
      run({ parent_search_id: 4, parent_exists: true, pivot_source: 'link on GitHub' }),
    );

    renderDetail();

    const link = await screen.findByRole('button', { name: 'Followed from run #4' });
    expect(link).toBeInTheDocument();
    expect(screen.getByText(/link on GitHub/)).toBeInTheDocument();
    // Existence comes with the run itself - no second request for the parent.
    expect(usernameSearchApi.getRun).toHaveBeenCalledTimes(1);
  });

  it('shows plain text, no link, once the parent has been deleted', async () => {
    usernameSearchApi.getRun.mockResolvedValue(run({ parent_search_id: 4, parent_exists: false }));

    renderDetail();

    expect(await screen.findByText('Followed from run #4')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Followed from/ })).not.toBeInTheDocument();
  });

  it('shows nothing for a run that followed no pivot', async () => {
    usernameSearchApi.getRun.mockResolvedValue(run({ parent_search_id: null }));

    renderDetail();

    await screen.findByText('jsmith_dev');
    expect(screen.queryByText(/Followed from/)).not.toBeInTheDocument();
  });
});

describe('HistoryDetail: site check', () => {
  afterEach(() => vi.clearAllMocks());

  it('reads a blocked check as inconclusive, not as "not found"', async () => {
    usernameSearchApi.getRun.mockResolvedValue(run({
      found_count: 0, site_statuses: { Twitter: 'unknown' },
    }));

    renderDetail();

    expect(await screen.findByText(/Could not check Twitter/)).toBeInTheDocument();
    expect(screen.getByText('Maigret site check')).toBeInTheDocument();
    expect(screen.queryByText('No profiles found')).not.toBeInTheDocument();
  });

  it('shows no warning when the site answered', async () => {
    usernameSearchApi.getRun.mockResolvedValue(run({
      found_count: 0, site_statuses: { Twitter: 'available' },
    }));

    renderDetail();

    await screen.findByText('jsmith_dev');
    expect(screen.queryByText(/Could not check/)).not.toBeInTheDocument();
  });
});
