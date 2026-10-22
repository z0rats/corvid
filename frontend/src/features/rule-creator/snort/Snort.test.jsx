import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import Snort from './Snort';

const type = (label, value) => fireEvent.change(screen.getByLabelText(label), { target: { value } });

/** Types into a field, then clicks the "Add" button in the same form row. */
function addIn(fields, button = 'Add') {
  let input;
  for (const [label, value] of Object.entries(fields)) {
    input = screen.getByLabelText(label);
    fireEvent.change(input, { target: { value } });
  }
  const row = input.closest('.MuiGrid-container');
  fireEvent.click(within(row).getByRole('button', { name: button }));
}

function renderExpanded() {
  render(<Snort />);
  for (const title of ['Rule Options', 'Detection Content', 'Enhanced Metadata']) {
    fireEvent.click(screen.getByText(title));
  }
}

function previewText() {
  fireEvent.click(screen.getByRole('button', { name: 'Preview Rule' }));
  return screen.getByRole('dialog').textContent;
}

beforeEach(() => vi.spyOn(window, 'alert').mockImplementation(() => {}));
afterEach(() => vi.restoreAllMocks());

describe('Snort rule builder', { timeout: 20000 }, () => {
  it('needs a message (SID is pre-generated) before preview/export', () => {
    renderExpanded();
    expect(screen.getByLabelText(/^SID/)).not.toHaveValue('');
    expect(screen.getByRole('button', { name: 'Preview Rule' })).toBeDisabled();
    type(/^Message/, 'ET MALWARE beacon');
    expect(screen.getByRole('button', { name: 'Export Snort Rule' })).toBeEnabled();
    type(/^SID/, ' ');
    expect(screen.getByRole('button', { name: 'Preview Rule' })).toBeDisabled();
  });

  it('builds the header and options into a single rule line', () => {
    renderExpanded();
    type('Source IP', '$HOME_NET');
    type('Dest Port', '443');
    type(/^Message/, 'ET MALWARE beacon');
    type(/^SID/, '9000001');
    type('Revision', '2');

    const text = previewText();
    expect(text).toContain('alert tcp $HOME_NET any -> any 443');
    expect(text).toContain('msg:"ET MALWARE beacon"');
    expect(text).toContain('sid:9000001');
    expect(text).toContain('rev:2');
  });

  it('content, pcre, flowbits, references, metadata, tags and malware families reach the rule', () => {
    renderExpanded();
    type(/^Message/, 'Full rule');
    addIn({ Content: 'GET /admin' });
    addIn({ 'PCRE Pattern': '/evil[0-9]+/i' });
    addIn({ 'Flowbit Name': 'seen_login' });
    addIn({ 'Reference Value': 'CVE-2024-3094' });
    addIn({ Key: 'policy', Value: 'balanced' });
    addIn({ 'Add Tag': 'beacon' });
    addIn({ 'Add Malware Family': 'Cobalt Strike' });
    type('Threshold', 'type limit, track by_src, count 1, seconds 60');

    expect(screen.getByLabelText('Content')).toHaveValue('');
    const text = previewText();
    for (const expected of [
      'content:"GET /admin"',
      'pcre:"/evil[0-9]+/i"',
      'seen_login',
      'CVE-2024-3094',
      'policy balanced',
      'beacon',
      'Cobalt',
      'threshold:type limit, track by_src, count 1, seconds 60',
    ]) {
      expect(text).toContain(expected);
    }
  });

  it('rejects duplicate custom tags and malware families', () => {
    renderExpanded();
    addIn({ 'Add Tag': 'beacon' });
    addIn({ 'Add Tag': 'beacon' });
    expect(window.alert).toHaveBeenCalledWith('Tag already exists.');
    addIn({ 'Add Malware Family': 'Emotet' });
    addIn({ 'Add Malware Family': 'Emotet' });
    expect(window.alert).toHaveBeenCalledWith('Malware family already exists.');
  });

  it('added rows can be deleted', () => {
    renderExpanded();
    addIn({ Content: 'abc' });
    addIn({ 'PCRE Pattern': '/x/' });
    fireEvent.click(screen.getByRole('button', { name: 'Delete content' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete PCRE' }));
    expect(screen.queryByRole('button', { name: 'Delete content' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Delete PCRE' })).not.toBeInTheDocument();
  });

  it('Reset (after confirming) restores the defaults', async () => {
    renderExpanded();
    type(/^Message/, 'temp');
    type('Source IP', '10.0.0.1');
    fireEvent.click(screen.getByRole('button', { name: 'Reset' }));
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Confirm' }));
    await waitFor(() => expect(screen.getByLabelText(/^Message/)).toHaveValue(''));
    expect(screen.getByLabelText('Source IP')).toHaveValue('any');
  });
});
