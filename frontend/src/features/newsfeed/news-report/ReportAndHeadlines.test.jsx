import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import Report from './Report';
import Headlines from '../headlines/Headlines';
import { useReportAnalysis } from '../hooks/api/useReportAnalysis';
import { newsfeedApi } from '../services/api/newsfeedApi';
import * as reportUtils from '../utils/reportUtils';

vi.mock('../hooks/api/useReportAnalysis', () => ({ useReportAnalysis: vi.fn() }));
vi.mock('../services/api/newsfeedApi', () => ({ newsfeedApi: { getRecentArticles: vi.fn() } }));

const BASE = {
  step: 0, isLoading: false, error: null, infoMessage: null, ranking: [], analysisResults: [],
  showStopButton: false, startAnalysis: vi.fn(), stopAnalysis: vi.fn(),
};
const state = (overrides) => useReportAnalysis.mockReturnValue({ ...BASE, ...overrides });

afterEach(() => vi.clearAllMocks());

describe('Report', () => {
  it('idle: offers to start', () => {
    state({});
    render(<Report />);
    fireEvent.click(screen.getByRole('button', { name: 'Start Analysis' }));
    expect(BASE.startAnalysis).toHaveBeenCalled();
    expect(screen.queryByText('Fetch all news articles of the last 7 days')).toBeNull();
  });

  it('running: shows progress, steps so far, ranking and a stop button', () => {
    state({
      step: 4, isLoading: true, showStopButton: true, infoMessage: 'Analyzing 3/10',
      ranking: [{ id: 1, title: 'Big breach', reason: 'Affects finance' }],
    });
    render(<Report />);
    expect(screen.getByText('Fetching / Analyzing...')).toBeInTheDocument();
    expect(screen.getByText('Analyzing 3/10')).toBeInTheDocument();
    expect(screen.getByText('Big breach')).toBeInTheDocument();
    expect(screen.getByText('Reason: Affects finance')).toBeInTheDocument();
    expect(screen.getByText('Waiting for the first analysis result...')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Start Analysis' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Stop Analysis' }));
    expect(BASE.stopAnalysis).toHaveBeenCalled();
  });

  it('error state', () => {
    state({ step: 1, error: 'LLM provider unavailable' });
    render(<Report />);
    expect(screen.getByText('LLM provider unavailable')).toBeInTheDocument();
  });

  it('completed: renders analysis cards and downloads the markdown report', () => {
    const download = vi.spyOn(reportUtils, 'downloadMarkdown').mockImplementation(() => {});
    const ranking = [{ id: 1, title: 'Big breach', reason: 'r' }];
    const analysisResults = [{
      article_id: 1, title: 'Big breach',
      analysis: { Risk: 'High', Summary: 'Data stolen', 'Analysis comment': 'c', 'Action items': ['Rotate'], Source: 'https://x' },
    }];
    state({ step: 5, ranking, analysisResults });
    render(<Report />);
    expect(screen.getByText('Risk: High')).toBeInTheDocument();
    expect(screen.getByText('Data stolen')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Start Analysis' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Download Markdown Report' }));
    expect(download).toHaveBeenCalledWith(expect.stringContaining('# Newsfeed Analysis Report'));
    expect(download.mock.calls[0][0]).toContain('- **Risk**: High');
  });

  it('no ranked articles message', () => {
    state({ step: 3 });
    render(<Report />);
    expect(screen.getByText('No articles found or none returned.')).toBeInTheDocument();
  });
});

describe('Headlines', () => {
  const HEADLINES = [
    { id: 1, feedname: 'BleepingComputer', title: 'Ransomware hits hospital', date: '2026-10-01T10:00:00Z', url: 'https://bc.example/1' },
    { id: 2, feedname: 'The Hacker News', title: 'Zero-day in VPN', date: '2026-10-03T10:00:00Z', url: 'javascript:alert(1)' },
  ];

  it('lists, filters and refuses to open non-http links', async () => {
    newsfeedApi.getRecentArticles.mockResolvedValue(HEADLINES);
    const open = vi.spyOn(window, 'open').mockImplementation(() => null);
    render(<Headlines />);
    expect(await screen.findByText('Ransomware hits hospital')).toBeInTheDocument();

    const rows = screen.getAllByRole('row').slice(1);
    expect(within(rows[0]).getByText('Zero-day in VPN')).toBeInTheDocument(); // newest first
    expect(within(rows[0]).getByRole('button', { name: 'Open article' })).toBeDisabled();
    fireEvent.click(within(rows[1]).getByRole('button', { name: 'Open article' }));
    expect(open).toHaveBeenCalledWith('https://bc.example/1', '_blank', 'noopener,noreferrer');

    fireEvent.change(screen.getByLabelText('Filter Title'), { target: { value: 'ransom' } });
    expect(screen.queryByText('Zero-day in VPN')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    await waitFor(() => expect(newsfeedApi.getRecentArticles).toHaveBeenCalledTimes(2));
    open.mockRestore();
  });

  it('sorts by source', async () => {
    newsfeedApi.getRecentArticles.mockResolvedValue(HEADLINES);
    render(<Headlines />);
    await screen.findByText('Ransomware hits hospital');
    fireEvent.click(screen.getByRole('button', { name: 'Source' }));
    const rows = screen.getAllByRole('row').slice(1);
    expect(within(rows[0]).getByText('BleepingComputer')).toBeInTheDocument();
  });
});
