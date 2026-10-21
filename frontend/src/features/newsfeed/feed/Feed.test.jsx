import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import { Provider, createStore } from 'jotai';
import Feed from './Feed';
import { newsfeedApi } from '../services/api/newsfeedApi';
import { newsfeedSettingsApi } from '../services/api/settingsApi';
import { apiKeysState } from '../../../core/state/atoms';

vi.mock('../services/api/newsfeedApi', () => ({
  newsfeedApi: {
    getArticles: vi.fn(), analyzeArticle: vi.fn(), updateArticle: vi.fn(), fetchNews: vi.fn(),
  },
}));
vi.mock('../services/api/settingsApi', () => ({ newsfeedSettingsApi: { getNewsfeeds: vi.fn() } }));

const MITRE = {
  has_mitre_data: true,
  threat_actors: [{ name: 'APT29', mitre_url: 'https://attack.mitre.org/groups/G0016/' }],
  software: [{ name: 'EvilTool', type: 'malware', mitre_url: 'https://phish.example/login' }],
  targeted_sectors: ['Government'],
  ttps: [{
    tactic: { name: 'Initial Access', id: 'TA0001' },
    technique: { name: 'Phishing', id: 'T1566', url: 'https://attack.mitre.org/techniques/T1566/' },
    behavior: 'Spearphishing emails with ISO attachments',
    procedure_example: 'Sends an ISO containing an LNK',
    detection_opportunities: ['Monitor ISO mounts'],
  }],
};

const ARTICLE = {
  id: 1,
  feedname: 'BleepingComputer',
  title: 'APT29 phishing wave',
  summary: 'Breaking &amp; <img src=x onerror="window.__xss=1"> news',
  date: '2026-10-01T10:00:00Z',
  link: 'https://bc.example/article',
  tlp: 'TLP:CLEAR',
  icon: 'bc.png',
  note: '',
  matches: ['APT29'],
  iocs: { ips: ['45.33.32.156'] },
  mitre_attack: MITRE,
  analysis_result: null,
};

function renderFeed(articles = [ARTICLE], { llm = true } = {}) {
  newsfeedApi.getArticles.mockResolvedValue({ articles, total_count: articles.length });
  newsfeedSettingsApi.getNewsfeeds.mockResolvedValue([{ name: 'BleepingComputer', reliability: 'B' }]);
  const store = createStore();
  if (llm) store.set(apiKeysState, { openai: true });
  return render(<Provider store={store}><Feed /></Provider>);
}

const card = () => screen.getByText('APT29 phishing wave').closest('.MuiCard-root');

afterEach(() => {
  vi.clearAllMocks();
  delete window.__xss;
});

describe('Feed', () => {
  it('renders articles with feed reliability, keywords, IOCs and MITRE sections', async () => {
    renderFeed();
    await screen.findByText('APT29 phishing wave');
    const c = card();
    expect(within(c).getByText('BleepingComputer')).toBeInTheDocument();
    expect(within(c).getByText('MITRE ATT&CK')).toBeInTheDocument();
    expect(within(c).getByText('45.33.32.156')).toBeInTheDocument();
    expect(within(c).getAllByText('APT29').length).toBeGreaterThan(0);
  });

  it('shows the empty state', async () => {
    renderFeed([]);
    expect(await screen.findByText('No articles found.')).toBeInTheDocument();
  });

  it('renders summary HTML as text, never as markup', async () => {
    renderFeed();
    await screen.findByText('APT29 phishing wave');
    expect(within(card()).getByText(/Breaking & <img src=x onerror/)).toBeInTheDocument();
    expect(card().querySelector('img[src="x"]')).toBeNull();
    expect(window.__xss).toBeUndefined();
  });

  it('only links an http(s) original; other schemes get a disabled button', async () => {
    renderFeed([ARTICLE, { ...ARTICLE, id: 2, title: 'Bad link', link: 'javascript:alert(1)' }]);
    await screen.findByText('Bad link');
    const good = within(card()).getByRole('link', { name: 'Open Original Article' });
    expect(good).toHaveAttribute('href', 'https://bc.example/article');
    const badCard = screen.getByText('Bad link').closest('.MuiCard-root');
    expect(within(badCard).queryByRole('link', { name: 'Open Original Article' })).toBeNull();
    expect(within(badCard).getByRole('button', { name: 'Invalid article URL' })).toBeDisabled();
  });

  it('MITRE links only point at attack.mitre.org', async () => {
    renderFeed();
    await screen.findByText('APT29 phishing wave');
    const c = card();
    const actorLinks = within(c).getAllByText('APT29').map((el) => el.closest('a')).filter(Boolean);
    expect(actorLinks.map((a) => a.getAttribute('href'))).toEqual(['https://attack.mitre.org/groups/G0016/']);
    // a prompt-injected, non-ATT&CK URL is rendered as plain text, not a link
    expect(within(c).getByText('EvilTool (malware)').closest('a')).toBeNull();
    expect(c.querySelector('a[href*="phish.example"]')).toBeNull();
  });

  it('changes the TLP through the menu', async () => {
    newsfeedApi.updateArticle.mockResolvedValue({});
    renderFeed();
    await screen.findByText('APT29 phishing wave');
    fireEvent.click(within(card()).getByRole('button', { name: 'Change TLP Level' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'TLP:RED' }));
    await waitFor(() => expect(newsfeedApi.updateArticle).toHaveBeenCalledWith(1, { tlp: 'TLP:RED', note: '', read: false }));
  });

  it('editing a note opens the editor; save persists, cancel leaves edit mode', async () => {
    newsfeedApi.updateArticle.mockResolvedValue({});
    renderFeed([{ ...ARTICLE, note: 'Relevant to our VPN fleet' }]);
    await screen.findByText('Relevant to our VPN fleet');
    fireEvent.click(within(card()).getAllByRole('button', { name: 'Edit Note' })[0]);
    fireEvent.click(await within(card()).findByRole('button', { name: 'Save Note' }));
    await waitFor(() => expect(newsfeedApi.updateArticle).toHaveBeenCalledWith(1, { note: 'Relevant to our VPN fleet' }));
    await waitFor(() => expect(within(card()).queryByRole('button', { name: 'Save Note' })).toBeNull());

    fireEvent.click(within(card()).getAllByRole('button', { name: 'Edit Note' })[0]);
    fireEvent.click(await within(card()).findByRole('button', { name: 'Cancel' }));
    await waitFor(() => expect(within(card()).queryByRole('button', { name: 'Save Note' })).toBeNull());
  });

  it('deletes an existing note after confirmation', async () => {
    newsfeedApi.updateArticle.mockResolvedValue({});
    renderFeed([{ ...ARTICLE, note: 'old note' }]);
    await screen.findByText('old note');
    fireEvent.click(within(card()).getByRole('button', { name: 'Delete Note' }));
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(newsfeedApi.updateArticle).toHaveBeenCalledWith(1, { note: '' }));
  });

  it('runs a MITRE-only analysis from the split button menu', async () => {
    newsfeedApi.analyzeArticle.mockResolvedValue({ mitre_attack: MITRE });
    renderFeed([{ ...ARTICLE, mitre_attack: null }]);
    await screen.findByText('APT29 phishing wave');
    const group = within(card()).getByRole('button', { name: 'Analyze' }).closest('.MuiButtonGroup-root');
    fireEvent.click(within(group).getAllByRole('button')[1]);
    fireEvent.click(await screen.findByRole('menuitem', { name: 'MITRE ATT&CK Mapping' }));
    await waitFor(() => expect(newsfeedApi.analyzeArticle).toHaveBeenCalledWith(1, false, 'mitre'));
    expect(await within(card()).findByText('MITRE ATT&CK')).toBeInTheDocument();
  });

  it('hides AI actions when no LLM is available', async () => {
    renderFeed([ARTICLE], { llm: false });
    await screen.findByText('APT29 phishing wave');
    expect(within(card()).queryByRole('button', { name: /Analyze/ })).toBeNull();
  });

  it('renders a stored AI analysis', async () => {
    renderFeed([{ ...ARTICLE, analysis_result: { markdown: '**Risk**: high for finance' } }]);
    expect(await screen.findByText('AI Analysis')).toBeInTheDocument();
    expect(screen.getByText(/high for finance/)).toBeInTheDocument();
    expect(within(card()).getByRole('button', { name: 'Re-analyze' })).toBeInTheDocument();
  });
});
