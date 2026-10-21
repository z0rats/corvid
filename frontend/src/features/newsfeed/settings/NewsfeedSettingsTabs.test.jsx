import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import KeywordSettings from './KeywordSettings';
import TrendsSettings from './TrendsSettings';
import CTISettings from './CTISettings';
import Settings from './Settings';
import { newsfeedSettingsApi } from '../services/api/settingsApi';

vi.mock('../services/api/settingsApi', () => ({
  newsfeedSettingsApi: {
    getConfig: vi.fn(), updateConfig: vi.fn(),
    getKeywords: vi.fn(), addKeyword: vi.fn(), deleteKeyword: vi.fn(),
    getBlacklistEntries: vi.fn(), addBlacklistEntry: vi.fn(), deleteBlacklistEntry: vi.fn(),
    getCtiSettings: vi.fn(), updateCtiSettings: vi.fn(),
  },
}));

const CONFIG = { keyword_matching_enabled: true, retention_days: 30, background_fetch_enabled: false, fetch_interval_minutes: 30 };

afterEach(() => vi.clearAllMocks());

const chipDelete = (label) => fireEvent.click(within(screen.getByText(label).closest('.MuiChip-root')).getByTestId('CancelIcon'));

function choose(comboboxName, optionName) {
  fireEvent.mouseDown(screen.getByRole('combobox', { name: comboboxName }));
  fireEvent.click(within(screen.getByRole('listbox')).getByRole('option', { name: optionName }));
}

describe('KeywordSettings', () => {
  async function setup(config = CONFIG) {
    newsfeedSettingsApi.getConfig.mockResolvedValue(config);
    newsfeedSettingsApi.getKeywords.mockResolvedValue([{ id: 1, keyword: 'LockBit' }]);
    render(<KeywordSettings />);
    await screen.findByText('Keyword Matching Settings');
  }

  it('hides the keyword list while matching is disabled', async () => {
    await setup({ ...CONFIG, keyword_matching_enabled: false });
    await waitFor(() => expect(screen.getByRole('switch')).not.toBeChecked());
    expect(screen.queryByText('Manage Keywords')).not.toBeInTheDocument();

    newsfeedSettingsApi.updateConfig.mockResolvedValue({ ...CONFIG });
    fireEvent.click(screen.getByRole('switch'));
    expect(await screen.findByText('Keyword matching setting updated.')).toBeInTheDocument();
    expect(screen.getByText('Manage Keywords')).toBeInTheDocument();
  });

  it('adds (Enter) and removes keywords; duplicates warn', async () => {
    await setup();
    expect(await screen.findByText('LockBit')).toBeInTheDocument();
    newsfeedSettingsApi.addKeyword.mockResolvedValue({ id: 2, keyword: 'Akira' });
    const input = screen.getByRole('textbox', { name: 'Add New Keyword' });
    fireEvent.change(input, { target: { value: 'Akira' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(await screen.findByText('Keyword added successfully.')).toBeInTheDocument();
    expect(screen.getByText('Akira')).toBeInTheDocument();
    expect(input).toHaveValue('');

    fireEvent.change(input, { target: { value: 'lockbit' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add New Keyword' }));
    expect(await screen.findByText('Keyword already exists.')).toBeInTheDocument();

    newsfeedSettingsApi.deleteKeyword.mockResolvedValue({});
    chipDelete('LockBit');
    expect(await screen.findByText('Keyword deleted successfully.')).toBeInTheDocument();
    expect(screen.queryByText('LockBit')).not.toBeInTheDocument();
  });

  it('blank input does nothing; API errors are reported', async () => {
    await setup();
    await screen.findByText('LockBit');
    fireEvent.click(screen.getByRole('button', { name: 'Add New Keyword' }));
    expect(newsfeedSettingsApi.addKeyword).not.toHaveBeenCalled();

    newsfeedSettingsApi.addKeyword.mockRejectedValue(new Error('x'));
    fireEvent.change(screen.getByRole('textbox', { name: 'Add New Keyword' }), { target: { value: 'New' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add New Keyword' }));
    expect(await screen.findByText('Failed to add keyword.')).toBeInTheDocument();

    newsfeedSettingsApi.deleteKeyword.mockRejectedValue(new Error('x'));
    chipDelete('LockBit');
    expect(await screen.findByText('Failed to delete keyword.')).toBeInTheDocument();
  });
});

describe('TrendsSettings', () => {
  async function setup() {
    newsfeedSettingsApi.getBlacklistEntries.mockImplementation(async (type) => (
      type === 'word' ? [{ id: 1, value: 'microsoft' }] : [{ id: 2, value: '8.8.8.8' }]
    ));
    render(<TrendsSettings />);
    await screen.findByText('microsoft');
  }

  it('adds to and removes from each list independently', async () => {
    await setup();
    newsfeedSettingsApi.addBlacklistEntry.mockResolvedValue({ id: 3, value: 'google' });
    fireEvent.change(screen.getByLabelText('Add word'), { target: { value: 'google' } });
    fireEvent.keyDown(screen.getByLabelText('Add word'), { key: 'Enter' });
    expect(await screen.findByText('Word added to blacklist.')).toBeInTheDocument();
    expect(newsfeedSettingsApi.addBlacklistEntry).toHaveBeenCalledWith('google', 'word');

    fireEvent.change(screen.getByLabelText('Add IOC'), { target: { value: '8.8.8.8' } });
    fireEvent.keyDown(screen.getByLabelText('Add IOC'), { key: 'Enter' });
    expect(await screen.findByText('IOC is already blacklisted.')).toBeInTheDocument();

    newsfeedSettingsApi.deleteBlacklistEntry.mockResolvedValue({});
    chipDelete('8.8.8.8');
    expect(await screen.findByText('IOC removed from blacklist.')).toBeInTheDocument();
  });

  it('reports failures', async () => {
    await setup();
    newsfeedSettingsApi.addBlacklistEntry.mockRejectedValue(new Error('x'));
    fireEvent.change(screen.getByLabelText('Add IOC'), { target: { value: '1.1.1.1' } });
    fireEvent.keyDown(screen.getByLabelText('Add IOC'), { key: 'Enter' });
    expect(await screen.findByText('Failed to add IOC to blacklist.')).toBeInTheDocument();
    newsfeedSettingsApi.deleteBlacklistEntry.mockRejectedValue(new Error('x'));
    chipDelete('microsoft');
    expect(await screen.findByText('Failed to remove word from blacklist.')).toBeInTheDocument();
  });
});

describe('CTISettings', () => {
  it('edits both tabs and saves the merged settings', async () => {
    newsfeedSettingsApi.getCtiSettings.mockResolvedValue({ settings: { company_profile: { industry_selection: ['Finance'] } } });
    newsfeedSettingsApi.updateCtiSettings.mockResolvedValue({});
    render(<CTISettings />);
    expect(await screen.findByText('Finance')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'Threat Actors' }));
    const actors = screen.getByLabelText('Relevant Threat Actors');
    fireEvent.change(actors, { target: { value: 'APT29' } });
    fireEvent.keyDown(actors, { key: 'Enter' });
    expect(screen.getByText('APT29')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Save Settings' }));
    expect(await screen.findByText('CTI settings saved successfully.')).toBeInTheDocument();
    const saved = newsfeedSettingsApi.updateCtiSettings.mock.calls[0][0];
    expect(saved.company_profile.industry_selection).toEqual(['Finance']);
    expect(JSON.stringify(saved)).toContain('APT29');
  });

  it('reports a save failure', async () => {
    newsfeedSettingsApi.getCtiSettings.mockResolvedValue({ settings: {} });
    newsfeedSettingsApi.updateCtiSettings.mockRejectedValue(new Error('x'));
    render(<CTISettings />);
    fireEvent.click(await screen.findByRole('button', { name: 'Save Settings' }));
    expect(await screen.findByText('Failed to save CTI settings.')).toBeInTheDocument();
  });
});

describe('newsfeed general Settings', () => {
  async function setup() {
    newsfeedSettingsApi.getConfig.mockResolvedValue(CONFIG);
    newsfeedSettingsApi.updateConfig.mockImplementation(async (c) => c);
    render(<Settings />);
    await screen.findByText('General Newsfeed Settings');
  }

  it('saves background fetch and retention changes', async () => {
    await setup();
    fireEvent.click(screen.getByRole('switch'));
    expect(await screen.findByText('Settings updated successfully')).toBeInTheDocument();
    expect(newsfeedSettingsApi.updateConfig).toHaveBeenLastCalledWith(expect.objectContaining({ background_fetch_enabled: true }));

    choose('Retention Period', 'Unlimited');
    await waitFor(() => expect(newsfeedSettingsApi.updateConfig).toHaveBeenLastCalledWith(expect.objectContaining({ retention_days: 0 })));
  });

  it('shows the backend error message on failure', async () => {
    await setup();
    newsfeedSettingsApi.updateConfig.mockRejectedValue({ response: { data: { message: 'Database is locked' } } });
    fireEvent.click(screen.getByRole('switch'));
    expect(await screen.findByText(/Database is locked|An error occurred/)).toBeInTheDocument();
  });
});
