import React from 'react';
import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Provider, createStore } from 'jotai';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../core/config/theme';
import { apiKeysState } from '../../core/state/atoms';
import { emailAnalyzerApi } from './services/api/emailAnalyzerApi';
import { aiAssistantApi } from './services/api/aiAssistantApi';
import EmailAnalyzer from './EmailAnalyzer';

vi.mock('./services/api/emailAnalyzerApi', () => ({
  emailAnalyzerApi: { analyzeEmail: vi.fn(), exportReport: vi.fn() },
}));
vi.mock('./services/api/aiAssistantApi', () => ({ aiAssistantApi: { analyzeMailBody: vi.fn() } }));
vi.mock('../ioc-tools/ioc-lookup/shared/components/IocLookupDialog', () => ({
  default: ({ open, ioc, iocType }) => (open ? <div role="dialog">lookup {iocType} {ioc}</div> : null),
}));
vi.mock('../../core/components/ui/PageHeader', () => ({ default: ({ title }) => <h1>{title}</h1> }));

const MD5 = 'a'.repeat(32);
const SHA1 = 'b'.repeat(40);
const SHA256 = 'c'.repeat(64);

const RESULT = {
  basic_info: { from: 'Alice <alice@example.com>', to: 'bob@example.org', subject: 'Invoice overdue' },
  eml_hashes: { md5: MD5, sha1: SHA1, sha256: SHA256 },
  headers: [{ From: 'alice@example.com' }, { Subject: 'Invoice overdue' }, { 'X-Mailer': 'PhishKit 2.0' }],
  attachments: [{ filename: 'invoice.pdf', md5: '1'.repeat(32), sha1: '2'.repeat(40), sha256: '3'.repeat(64) }],
  hops: [{ number: 1, from_server: 'mail.example.com', by_server: 'mx.example.org', with_protocol: 'ESMTP', date: 'Mon' }],
  warnings: [{ warning_tlp: 'red', warning_title: 'SPF failed', warning_message: 'Sender not authorized' }],
  urls: ['https://pay.example.net/login'],
  message_text: '<p>Please pay the <b>invoice</b> today.</p>',
};

function renderPage({ llm = true } = {}) {
  const store = createStore();
  store.set(apiKeysState, llm ? { openai: true } : {});
  return render(
    <Provider store={store}>
      <ThemeProvider theme={lightTheme}>
        <EmailAnalyzer />
      </ThemeProvider>
    </Provider>,
  );
}

async function uploadAndAnalyze(container) {
  const file = new File(['From: alice@example.com'], 'suspicious.eml', { type: 'message/rfc822' });
  fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [file] } });
  expect(await screen.findByText(/suspicious\.eml/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Analyze' }));
  return file;
}

const originalClipboard = navigator.clipboard;

const expandSection = (name) => fireEvent.click(screen.getByRole('button', { name }));

describe('EmailAnalyzer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    emailAnalyzerApi.analyzeEmail.mockResolvedValue(RESULT);
    Object.assign(navigator, { clipboard: { writeText: vi.fn() } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    Object.assign(navigator, { clipboard: originalClipboard });
  });

  it('keeps Analyze disabled until a file is chosen, then renders every result section', async () => {
    const { container } = renderPage();
    expect(screen.getByRole('button', { name: 'Analyze' })).toBeDisabled();

    const file = await uploadAndAnalyze(container);

    expect(emailAnalyzerApi.analyzeEmail).toHaveBeenCalledWith(file);
    expect(await screen.findByText('Attachments (1)')).toBeInTheDocument();
    expect(screen.getByText('Complete Header (3 fields)')).toBeInTheDocument();
    expect(screen.getByText('SPF failed')).toBeInTheDocument();
    expect(screen.getByText(MD5)).toBeInTheDocument();
  });

  it('shows the backend error when analysis fails', async () => {
    emailAnalyzerApi.analyzeEmail.mockRejectedValue({ response: { data: { detail: 'Not a valid .eml file' } } });
    const { container } = renderPage();
    await uploadAndAnalyze(container);
    expect(await screen.findByText('Not a valid .eml file')).toBeInTheDocument();
    expect(screen.queryByText(/Attachments \(/)).not.toBeInTheDocument();
  });

  it('filters header fields by key or value', async () => {
    const { container } = renderPage();
    await uploadAndAnalyze(container);
    expandSection(await screen.findByText('Complete Header (3 fields)').then((el) => el.textContent));

    const table = screen.getByRole('table', { name: 'header fields table' });
    expect(within(table).getAllByRole('row')).toHaveLength(4);

    fireEvent.change(screen.getByPlaceholderText('Filter headers...'), { target: { value: 'phishkit' } });
    expect(within(table).getAllByRole('row')).toHaveLength(2);
    expect(within(table).getByText('X-Mailer')).toBeInTheDocument();
    expect(screen.getByText('Showing 1 of 3 fields')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText('Filter headers...'), { target: { value: 'subject' } });
    expect(within(table).getByText('Subject')).toBeInTheDocument();
    expect(within(table).queryByText('X-Mailer')).not.toBeInTheDocument();
  });

  it('copies attachment hashes and looks them up with the detected hash type', async () => {
    const { container } = renderPage();
    await uploadAndAnalyze(container);
    expandSection(await screen.findByText('Attachments (1)').then((el) => el.textContent));

    const table = screen.getByRole('table', { name: 'attachments table' });
    expect(within(table).getByText('invoice.pdf')).toBeInTheDocument();

    const sha1Row = within(table).getByText('SHA1').closest('tr');
    fireEvent.click(within(sha1Row).getByRole('button', { name: 'Copy hash' }));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('2'.repeat(40));

    fireEvent.click(within(sha1Row).getByRole('button', { name: 'Analyze' }));
    expect(screen.getByRole('dialog')).toHaveTextContent(`lookup SHA1 ${'2'.repeat(40)}`);
  });

  it('copies the .eml hashes and looks up the file MD5', async () => {
    const { container } = renderPage();
    await uploadAndAnalyze(container);
    await screen.findByText(SHA256);

    const sha256Row = screen.getByText(SHA256).parentElement;
    fireEvent.click(within(sha256Row).getByRole('button', { name: 'Copy hash' }));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(SHA256);

    fireEvent.click(screen.getByRole('button', { name: 'Analyze .eml hash' }));
    expect(screen.getByRole('dialog')).toHaveTextContent(`lookup MD5 ${MD5}`);
  });

  it('sends the message body as plain text to the AI and renders its markdown answer', async () => {
    aiAssistantApi.analyzeMailBody.mockResolvedValue('## Verdict\n\nLikely **phishing**.');
    const { container } = renderPage();
    await uploadAndAnalyze(container);

    fireEvent.click(await screen.findByRole('button', { name: 'Analyze message body with AI' }));

    expect(aiAssistantApi.analyzeMailBody).toHaveBeenCalledWith('Please pay the invoice today.');
    expect(await screen.findByRole('heading', { name: 'Verdict' })).toBeInTheDocument();
    expect(screen.getByText('AI message-body analysis')).toBeInTheDocument();
  });

  it('tells the user when the AI analysis fails', async () => {
    aiAssistantApi.analyzeMailBody.mockRejectedValue(new Error('rate limited'));
    const { container } = renderPage();
    await uploadAndAnalyze(container);

    fireEvent.click(await screen.findByRole('button', { name: 'Analyze message body with AI' }));

    expect(await screen.findByText('AI analysis failed. Please try again.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Analyze message body with AI' })).toBeEnabled();
  });

  it('drops the previous AI answer when a retry fails', async () => {
    aiAssistantApi.analyzeMailBody
      .mockResolvedValueOnce('## Verdict\n\nLikely **phishing**.')
      .mockRejectedValueOnce(new Error('rate limited'));
    const { container } = renderPage();
    await uploadAndAnalyze(container);

    const analyze = await screen.findByRole('button', { name: 'Analyze message body with AI' });
    fireEvent.click(analyze);
    expect(await screen.findByRole('heading', { name: 'Verdict' })).toBeInTheDocument();

    fireEvent.click(analyze);
    expect(await screen.findByText('AI analysis failed. Please try again.')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Verdict' })).not.toBeInTheDocument();
  });

  it('starts a new analysis without the previous email\'s export error or AI answer', async () => {
    aiAssistantApi.analyzeMailBody.mockResolvedValue('## Verdict\n\nLikely **phishing**.');
    emailAnalyzerApi.exportReport.mockRejectedValue(new Error('boom'));
    const { container } = renderPage();
    await uploadAndAnalyze(container);
    fireEvent.click(await screen.findByRole('button', { name: 'Analyze message body with AI' }));
    await screen.findByRole('heading', { name: 'Verdict' });
    fireEvent.click(screen.getByRole('button', { name: 'HTML' }));
    await screen.findByText('Report export failed. Please try again.');

    fireEvent.click(screen.getByRole('button', { name: 'Analyze' }));

    await waitFor(() => expect(emailAnalyzerApi.analyzeEmail).toHaveBeenCalledTimes(2));
    expect(await screen.findByText('Attachments (1)')).toBeInTheDocument();
    expect(screen.queryByText('Report export failed. Please try again.')).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Verdict' })).not.toBeInTheDocument();
  });

  it('hides the AI action when no LLM is configured', async () => {
    const { container } = renderPage({ llm: false });
    await uploadAndAnalyze(container);
    await screen.findByText('Attachments (1)');
    expect(screen.queryByRole('button', { name: 'Analyze message body with AI' })).not.toBeInTheDocument();
  });

  it('downloads the report in the chosen format and locale', async () => {
    emailAnalyzerApi.exportReport.mockResolvedValue(new Blob(['%PDF']));
    const createObjectURL = vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:x');
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});
    let downloaded;
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function click() { downloaded = this.download; });

    const { container } = renderPage();
    await uploadAndAnalyze(container);
    fireEvent.click(await screen.findByRole('button', { name: 'PDF' }));

    await waitFor(() => expect(downloaded).toBe('email-analysis.pdf'));
    expect(emailAnalyzerApi.exportReport).toHaveBeenCalledWith(RESULT, 'pdf', 'en');
    expect(createObjectURL).toHaveBeenCalled();
  });

  it('blocks a second export while one is still running', async () => {
    let finish;
    emailAnalyzerApi.exportReport.mockReturnValue(new Promise((resolve, reject) => { finish = reject; }));
    const { container } = renderPage();
    await uploadAndAnalyze(container);

    fireEvent.click(await screen.findByRole('button', { name: 'HTML' }));
    expect(screen.getByRole('button', { name: 'PDF' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'HTML' })).toBeDisabled();

    finish(new Error('timeout'));
    expect(await screen.findByText('Report export failed. Please try again.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'PDF' })).toBeEnabled();
    expect(emailAnalyzerApi.exportReport).toHaveBeenCalledTimes(1);
  });

  it('tells the user when the report export fails', async () => {
    emailAnalyzerApi.exportReport.mockRejectedValue(new Error('boom'));
    const { container } = renderPage();
    await uploadAndAnalyze(container);
    fireEvent.click(await screen.findByRole('button', { name: 'HTML' }));
    expect(await screen.findByText('Report export failed. Please try again.')).toBeInTheDocument();
  });
});
