import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import ManageNewsfeeds from './ManageNewsfeeds';
import { newsfeedSettingsApi } from '../services/api/settingsApi';

vi.mock('../services/api/settingsApi', () => ({
  newsfeedSettingsApi: {
    getNewsfeeds: vi.fn(),
    enableNewsfeed: vi.fn(),
    disableNewsfeed: vi.fn(),
    setNewsfeedReliability: vi.fn(),
    validateFeed: vi.fn(),
    addNewsfeed: vi.fn(),
    uploadFeedIcon: vi.fn(),
    deleteNewsfeed: vi.fn(),
    deleteFeedIcon: vi.fn(),
    refetchFeedIcon: vi.fn(),
    refetchAllMissingIcons: vi.fn(),
  },
}));

const FEEDS = [
  { name: 'BleepingComputer', url: 'https://bc.example/rss', enabled: true, icon: 'bc.png', icon_id: 'bc.png', reliability: 'B' },
  { name: 'Custom Blog', url: 'https://blog.example/rss', enabled: false, icon: 'default.png', icon_id: null },
];

async function setup(feeds = FEEDS) {
  newsfeedSettingsApi.getNewsfeeds.mockResolvedValue(feeds);
  render(<ManageNewsfeeds />);
  await screen.findByText('Manage Newsfeeds');
  if (feeds.length) await screen.findByText(feeds[0].name);
}

const row = (name) => screen.getByText(name).closest('li');

afterEach(() => vi.clearAllMocks());

describe('ManageNewsfeeds', () => {
  it('lists feeds and shows an empty state', async () => {
    await setup();
    expect(screen.getByText('Custom Blog')).toBeInTheDocument();
  });

  it('empty list', async () => {
    newsfeedSettingsApi.getNewsfeeds.mockResolvedValue([]);
    render(<ManageNewsfeeds />);
    expect(await screen.findByText(/No feeds configured/)).toBeInTheDocument();
  });

  it('toggling a feed calls the matching endpoint and reports it', async () => {
    newsfeedSettingsApi.disableNewsfeed.mockResolvedValue({});
    newsfeedSettingsApi.enableNewsfeed.mockResolvedValue({});
    await setup();
    fireEvent.click(within(row('BleepingComputer')).getByRole('switch'));
    expect(await screen.findByText('Feed disabled successfully')).toBeInTheDocument();
    expect(newsfeedSettingsApi.disableNewsfeed).toHaveBeenCalledWith('BleepingComputer');

    fireEvent.click(within(row('Custom Blog')).getByRole('switch'));
    expect(await screen.findByText('Feed enabled successfully')).toBeInTheDocument();
  });

  it('a failed toggle is reported', async () => {
    newsfeedSettingsApi.disableNewsfeed.mockRejectedValue(new Error('x'));
    await setup();
    fireEvent.click(within(row('BleepingComputer')).getByRole('switch'));
    expect(await screen.findByText('Failed to toggle feed')).toBeInTheDocument();
  });

  it('deleting asks for confirmation first', async () => {
    newsfeedSettingsApi.deleteNewsfeed.mockResolvedValue({});
    await setup();
    fireEvent.click(within(row('Custom Blog')).getByRole('button', { name: 'Delete feed' }));
    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Delete Feed')).toBeInTheDocument();
    expect(newsfeedSettingsApi.deleteNewsfeed).not.toHaveBeenCalled();

    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }));
    expect(await screen.findByText('Feed deleted successfully')).toBeInTheDocument();
    expect(newsfeedSettingsApi.deleteNewsfeed).toHaveBeenCalledWith('Custom Blog');
    await waitFor(() => expect(screen.queryByText('Custom Blog')).not.toBeInTheDocument());
  });

  it('a failed delete keeps the feed and reports the error', async () => {
    newsfeedSettingsApi.deleteNewsfeed.mockRejectedValue(new Error('x'));
    await setup();
    fireEvent.click(within(row('Custom Blog')).getByRole('button', { name: 'Delete feed' }));
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Delete' }));
    expect(await screen.findByText('Error deleting feed')).toBeInTheDocument();
    expect(screen.getByText('Custom Blog')).toBeInTheDocument();
  });

  it('refreshing a favicon reports the backend message', async () => {
    newsfeedSettingsApi.refetchFeedIcon.mockResolvedValue({ success: false, message: 'Could not download favicon: No icon found' });
    await setup();
    fireEvent.click(within(row('Custom Blog')).getByRole('button', { name: 'Refresh favicon' }));
    expect(await screen.findByText('Could not download favicon: No icon found')).toBeInTheDocument();
  });

  it('bulk-fetches missing icons, and is disabled when none are missing', async () => {
    newsfeedSettingsApi.refetchAllMissingIcons.mockResolvedValue({ total: 1, succeeded: 1, failed: 0, results: [] });
    await setup();
    fireEvent.click(screen.getByRole('button', { name: 'Fetch Missing Icons' }));
    expect(await screen.findByText('Fetched 1 of 1 missing icons')).toBeInTheDocument();
  });

  it('bulk fetch with nothing downloaded is an error', async () => {
    newsfeedSettingsApi.refetchAllMissingIcons.mockResolvedValue({ total: 1, succeeded: 0, failed: 1, results: [] });
    await setup();
    fireEvent.click(screen.getByRole('button', { name: 'Fetch Missing Icons' }));
    expect(await screen.findByText('No favicons could be downloaded')).toBeInTheDocument();
  });

  it('bulk fetch button is disabled when every feed has an icon', async () => {
    await setup([FEEDS[0]]);
    expect(screen.getByRole('button', { name: 'Fetch Missing Icons' })).toBeDisabled();
  });
});

describe('AddFeedDialog via ManageNewsfeeds', () => {
  async function openDialog() {
    await setup();
    fireEvent.click(screen.getByRole('button', { name: 'Add Feed' }));
    return screen.findByRole('dialog');
  }

  it('validates, adds and closes; the new feed is listed', async () => {
    newsfeedSettingsApi.validateFeed.mockResolvedValue({ valid: true });
    newsfeedSettingsApi.addNewsfeed.mockResolvedValue({ name: 'New Feed', url: 'https://new.example/rss', enabled: true, icon: 'default.png' });
    const dialog = await openDialog();
    const add = within(dialog).getByRole('button', { name: 'Add Feed' });
    expect(add).toBeDisabled();

    fireEvent.change(within(dialog).getByLabelText('Feed Name'), { target: { value: 'New Feed' } });
    fireEvent.change(within(dialog).getByLabelText('Feed URL'), { target: { value: 'https://new.example/rss' } });
    fireEvent.click(add);

    expect(await screen.findByText('Feed added successfully')).toBeInTheDocument();
    expect(newsfeedSettingsApi.validateFeed).toHaveBeenCalledWith({ name: 'New Feed', url: 'https://new.example/rss', enabled: true });
    expect(newsfeedSettingsApi.uploadFeedIcon).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(screen.getByText('New Feed')).toBeInTheDocument();
  });

  it('shows the backend validation error and stays open', async () => {
    newsfeedSettingsApi.validateFeed.mockRejectedValue({ response: { data: { detail: 'Feed URL is unreachable or not allowed' } } });
    const dialog = await openDialog();
    fireEvent.change(within(dialog).getByLabelText('Feed Name'), { target: { value: 'Internal' } });
    fireEvent.change(within(dialog).getByLabelText('Feed URL'), { target: { value: 'http://10.0.0.1/rss' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Add Feed' }));
    expect(await within(dialog).findByText('Feed URL is unreachable or not allowed')).toBeInTheDocument();
    expect(newsfeedSettingsApi.addNewsfeed).not.toHaveBeenCalled();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('cancel resets the form', async () => {
    const dialog = await openDialog();
    fireEvent.change(within(dialog).getByLabelText('Feed Name'), { target: { value: 'x' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Add Feed' }));
    expect(within(await screen.findByRole('dialog')).getByLabelText('Feed Name')).toHaveValue('');
  });
});
