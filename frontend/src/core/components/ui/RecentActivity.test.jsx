import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { Provider, createStore } from 'jotai';
import RecentActivity from './RecentActivity';
import { activityService } from '../../services/api/activityService';
import { modulesState } from '../../state/atoms';

vi.mock('../../services/api/activityService', () => ({ activityService: { listRecent: vi.fn() } }));

const NOW = new Date().toISOString();

function renderActivity(store = createStore()) {
  return render(
    <Provider store={store}>
      <MemoryRouter><RecentActivity /></MemoryRouter>
    </Provider>,
  );
}

afterEach(() => vi.clearAllMocks());

describe('RecentActivity', () => {
  it('links each run to its own history page', async () => {
    activityService.listRecent.mockResolvedValue([
      { feature: 'amass', id: 5, target: 'example.com', status: 'completed', timestamp: NOW },
      { feature: 'ioc_lookup', id: 9, target: '1.2.3.4', status: 'completed', timestamp: NOW },
      { feature: 'social_analyzer', id: 3, target: 'alice', status: 'failed', timestamp: NOW },
    ]);
    renderActivity();

    expect((await screen.findByText('example.com')).closest('a')).toHaveAttribute('href', '/amass/history/5');
    expect(screen.getByText('1.2.3.4').closest('a')).toHaveAttribute('href', '/ioc-tools/lookup/history/9');
    expect(screen.getByText('alice').closest('a')).toHaveAttribute('href', '/username-search/history/3');
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('hides runs of disabled modules', async () => {
    activityService.listRecent.mockResolvedValue([
      { feature: 'amass', id: 5, target: 'example.com', status: 'completed', timestamp: NOW },
      { feature: 'git_recon', id: 6, target: 'torvalds', status: 'completed', timestamp: NOW },
    ]);
    const store = createStore();
    store.set(modulesState, { amass: { enabled: false } });
    renderActivity(store);

    expect(await screen.findByText('torvalds')).toBeInTheDocument();
    expect(screen.queryByText('example.com')).not.toBeInTheDocument();
  });

  it('renders nothing when there is no activity or loading fails', async () => {
    activityService.listRecent.mockRejectedValue(new Error('down'));
    const { container } = renderActivity();
    await Promise.resolve();
    expect(container).toBeEmptyDOMElement();
  });
});
