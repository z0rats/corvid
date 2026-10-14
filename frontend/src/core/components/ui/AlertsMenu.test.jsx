import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import AlertsMenu from './AlertsMenu';
import { alertsService } from '../../services/api/alertsService';

vi.mock('../../services/api/alertsService', () => ({
  alertsService: {
    getUnreadCount: vi.fn(),
    list: vi.fn(),
    markRead: vi.fn(),
    markAllRead: vi.fn(),
    deleteAll: vi.fn(),
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, useNavigate: () => mockNavigate };
});

const ALERTS = [
  { id: 1, module: 'amass', title: 'amass: scan completed', message: 'Scan #5 (domain=a.com) completed.', read: false, timestamp: '2026-10-14T10:00:00' },
  { id: 2, module: 'scheduler', title: 'news_fetch: job failing', message: 'boom', read: true, timestamp: '2026-10-14T09:00:00+00:00' },
];

beforeEach(() => {
  vi.clearAllMocks();
  alertsService.getUnreadCount.mockResolvedValue(1);
  alertsService.list.mockResolvedValue(ALERTS);
  alertsService.markRead.mockResolvedValue({});
  alertsService.markAllRead.mockResolvedValue();
  alertsService.deleteAll.mockResolvedValue();
});

const renderMenu = () => render(<MemoryRouter><AlertsMenu /></MemoryRouter>);

describe('AlertsMenu', () => {
  it('shows the unread count on the bell', async () => {
    renderMenu();
    expect(await screen.findByRole('button', { name: 'Alerts, 1 unread' })).toBeInTheDocument();
  });

  it('opens the inbox, marks a clicked alert read and follows its link', async () => {
    renderMenu();
    fireEvent.click(await screen.findByRole('button', { name: /alerts, 1 unread/i }));
    fireEvent.click(await screen.findByText('amass: scan completed'));

    expect(alertsService.markRead).toHaveBeenCalledWith(1);
    expect(mockNavigate).toHaveBeenCalledWith('/amass/history/5');
  });

  it('does not navigate for an alert without a link', async () => {
    renderMenu();
    fireEvent.click(await screen.findByRole('button', { name: /alerts/i }));
    fireEvent.click(await screen.findByText('news_fetch: job failing'));

    expect(mockNavigate).not.toHaveBeenCalled();
    expect(alertsService.markRead).not.toHaveBeenCalled(); // already read
  });

  it('marks everything read', async () => {
    renderMenu();
    fireEvent.click(await screen.findByRole('button', { name: /alerts, 1 unread/i }));
    await screen.findByText('amass: scan completed');
    fireEvent.click(screen.getByRole('button', { name: 'Mark all read' }));

    expect(alertsService.markAllRead).toHaveBeenCalled();
    expect(await screen.findByRole('button', { name: 'Alerts, 0 unread', hidden: true })).toBeInTheDocument();
  });

  it('only clears alerts after confirmation', async () => {
    renderMenu();
    fireEvent.click(await screen.findByRole('button', { name: /alerts/i }));
    await screen.findByText('amass: scan completed');
    fireEvent.click(screen.getByRole('button', { name: 'Clear' }));
    expect(alertsService.deleteAll).not.toHaveBeenCalled();

    const dialog = await screen.findByRole('dialog', { name: 'Delete all alerts?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }));

    await waitFor(() => expect(alertsService.deleteAll).toHaveBeenCalled());
    expect(await screen.findByText(/no alerts yet/i)).toBeInTheDocument();
  });
});
