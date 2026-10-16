import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { Provider, createStore } from 'jotai';
import ActiveScansMenu from './ActiveScansMenu';
import { activityService } from '../../services/api/activityService';
import { announceScanLifecycle } from '../../utils/scanLifecycleEvent';

vi.mock('../../services/api/activityService', () => ({ activityService: { listActive: vi.fn() } }));

const NOW = new Date().toISOString();

function renderMenu() {
  return render(
    <Provider store={createStore()}>
      <MemoryRouter><ActiveScansMenu /></MemoryRouter>
    </Provider>,
  );
}

afterEach(() => vi.clearAllMocks());

describe('ActiveScansMenu', () => {
  it('renders nothing while no scan is running', async () => {
    activityService.listActive.mockResolvedValue([]);
    const { container } = renderMenu();
    await waitFor(() => expect(activityService.listActive).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it('shows the unfinished count and lists each run with its status and link', async () => {
    const user = userEvent.setup();
    activityService.listActive.mockResolvedValue([
      { feature: 'amass', id: 4, target: 'example.com', status: 'queued', timestamp: NOW },
      { feature: 'social_analyzer', id: 2, target: 'alice', status: 'running', timestamp: NOW },
    ]);
    renderMenu();

    await user.click(await screen.findByRole('button', { name: 'Active scans, 2 unfinished' }));

    expect(screen.getByText('example.com').closest('a')).toHaveAttribute('href', '/amass/history/4');
    expect(screen.getByText('alice').closest('a')).toHaveAttribute('href', '/username-search/history/2');
    expect(screen.getByText('Queued')).toBeInTheDocument();
    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('does not reopen by itself when the list empties while open and later refills', async () => {
    const user = userEvent.setup();
    const run = { feature: 'amass', id: 4, target: 'example.com', status: 'running', timestamp: NOW };
    activityService.listActive.mockResolvedValue([run]);
    renderMenu();
    await user.click(await screen.findByRole('button', { name: /Active scans/ }));
    expect(screen.getByText('example.com')).toBeInTheDocument();

    // The last scan finishes while the menu is open...
    activityService.listActive.mockResolvedValue([]);
    act(() => { announceScanLifecycle('completed'); });
    await waitFor(() => expect(screen.queryByRole('button', { name: /Active scans/ })).not.toBeInTheDocument());

    // ...and a new one starts: the button comes back, the menu must stay closed.
    activityService.listActive.mockResolvedValue([run]);
    act(() => { announceScanLifecycle('started'); });
    await screen.findByRole('button', { name: /Active scans/ });
    expect(screen.queryByText('example.com')).not.toBeInTheDocument();
  });
});

