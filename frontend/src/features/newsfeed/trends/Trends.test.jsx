import { cloneElement } from 'react';
import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import Trends from './Trends';
import { trendsApi } from '../services/api/trendsApi';
import { newsfeedApi } from '../services/api/newsfeedApi';
import { newsfeedSettingsApi } from '../services/api/settingsApi';

// jsdom has no layout, so ResponsiveContainer would measure 0x0 and draw no bars
vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    ResponsiveContainer: ({ children }) => (
      <div style={{ width: 800, height: 400 }}>{cloneElement(children, { width: 800, height: 400 })}</div>
    ),
  };
});
vi.mock('../services/api/trendsApi', () => ({
  trendsApi: { getTitleWordFrequency: vi.fn(), getTopIocs: vi.fn(), getTopCves: vi.fn(), getIocTypeDistribution: vi.fn() },
}));
vi.mock('../services/api/newsfeedApi', () => ({ newsfeedApi: { getArticlesByIds: vi.fn() } }));
vi.mock('../services/api/settingsApi', () => ({
  newsfeedSettingsApi: { getBlacklistEntries: vi.fn(), addBlacklistEntry: vi.fn(), deleteBlacklistEntry: vi.fn() },
}));

function setup() {
  trendsApi.getTitleWordFrequency.mockResolvedValue([
    { word: 'ransomware', count: 12, article_ids: [1, 2] },
    { word: 'microsoft', count: 5, article_ids: [3] },
  ]);
  trendsApi.getTopIocs.mockResolvedValue([{ value: '45.33.32.156', count: 3, article_ids: [1] }]);
  trendsApi.getTopCves.mockResolvedValue([{ value: 'CVE-2024-3094', count: 4, article_ids: [2] }]);
  trendsApi.getIocTypeDistribution.mockResolvedValue([{ name: 'ips', value: 10 }, { name: 'md5', value: 2 }]);
  newsfeedSettingsApi.getBlacklistEntries.mockResolvedValue([]);
  newsfeedApi.getArticlesByIds.mockImplementation(async (ids) => ids.map((id) => ({
    id, title: `Article ${id}`, feedname: 'BleepingComputer', date: '2026-10-01T10:00:00Z', link: `https://bc.example/${id}`,
  })));
  return render(<Trends />);
}

const bars = (container) => [...container.querySelectorAll('rect[rx="4"]')];

afterEach(() => vi.clearAllMocks());

describe('Trends', () => {
  it('loads every panel for the default 7-day window', async () => {
    setup();
    expect(await screen.findByText('Top Words in Headlines')).toBeInTheDocument();
    await waitFor(() => expect(trendsApi.getTopCves).toHaveBeenCalledWith(10, '7d'));
    expect(trendsApi.getTitleWordFrequency).toHaveBeenCalledWith(10, '7d');
    expect(trendsApi.getIocTypeDistribution).toHaveBeenCalledWith('7d');
    expect(trendsApi.getTopIocs).toHaveBeenCalledWith(expect.any(String), 10, '7d');
  });

  it('clicking a word bar lists the matching articles', async () => {
    const { container } = setup();
    await screen.findByText('Top Words in Headlines');
    await waitFor(() => expect(bars(container).length).toBeGreaterThan(0));
    fireEvent.click(bars(container)[0]);

    expect(await screen.findByText('Article 1')).toBeInTheDocument();
    expect(screen.getByText('Article 2')).toBeInTheDocument();
    expect(newsfeedApi.getArticlesByIds).toHaveBeenCalledWith([1, 2]);
    expect(screen.getByText(/Word: ransomware/)).toBeInTheDocument();
    for (const link of screen.getAllByRole('link', { name: 'Open article' })) {
      expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'));
    }
  });

  it('a failed article lookup is shown per row', async () => {
    const { container } = setup();
    newsfeedApi.getArticlesByIds.mockRejectedValue(new Error('timeout'));
    await screen.findByText('Top Words in Headlines');
    await waitFor(() => expect(bars(container).length).toBeGreaterThan(0));
    fireEvent.click(bars(container)[0]);
    expect(await screen.findByText('Error loading article 1: timeout')).toBeInTheDocument();
  });

  it('blacklisting a word hides it and refetches', async () => {
    newsfeedSettingsApi.addBlacklistEntry.mockResolvedValue({ id: 9, value: 'microsoft' });
    const { container } = setup();
    await screen.findByText('Top Words in Headlines');
    await waitFor(() => expect(container.querySelectorAll('text').length).toBeGreaterThan(0));
    const crosses = [...container.querySelectorAll('g[transform] > text')].filter((el) => el.textContent === '✕');
    fireEvent.click(crosses[1].parentElement);
    expect(await screen.findByText('"microsoft" added to blacklist')).toBeInTheDocument();
    expect(newsfeedSettingsApi.addBlacklistEntry).toHaveBeenCalledWith('microsoft', 'word');
    await waitFor(() => expect(trendsApi.getTitleWordFrequency).toHaveBeenCalledTimes(2));
  });

  it('changing the time range refetches with the new window', async () => {
    setup();
    await screen.findByText('Top Words in Headlines');
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Time Range' }));
    const options = within(screen.getByRole('listbox')).getAllByRole('option');
    fireEvent.click(options[options.length - 1]);
    await waitFor(() => expect(trendsApi.getTitleWordFrequency).toHaveBeenCalledTimes(2));
    expect(trendsApi.getTitleWordFrequency.mock.calls[1][1]).not.toBe('7d');
  });

  it('empty data shows the no-data messages', async () => {
    trendsApi.getTitleWordFrequency.mockResolvedValue([]);
    trendsApi.getTopIocs.mockResolvedValue([]);
    trendsApi.getTopCves.mockResolvedValue([]);
    trendsApi.getIocTypeDistribution.mockResolvedValue([]);
    newsfeedSettingsApi.getBlacklistEntries.mockResolvedValue([]);
    render(<Trends />);
    expect(await screen.findByText('No word frequency data available for the selected time range.')).toBeInTheDocument();
    expect(await screen.findByText('No CVE data available for the selected time range.')).toBeInTheDocument();
    expect(await screen.findByText('No IOC type distribution data available for the selected time range.')).toBeInTheDocument();
  });
});
