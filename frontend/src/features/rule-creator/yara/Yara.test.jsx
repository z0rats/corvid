import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import Yara from './Yara';
import { captureExport } from '../shared/testUtils';

const type = (label, value) => fireEvent.change(screen.getByLabelText(label), { target: { value } });

function choose(comboboxName, optionName) {
  fireEvent.mouseDown(screen.getByRole('combobox', { name: comboboxName }));
  fireEvent.click(within(screen.getByRole('listbox')).getByRole('option', { name: optionName }));
}

function addString(identifier, value, kind) {
  type(/^Identifier/, identifier);
  if (kind) choose('Type', kind);
  type(/^Value/, value);
  fireEvent.click(screen.getByRole('button', { name: 'Add' }));
}

/** Expands every collapsed section (Tags, Add String, Strings (n), Conditions). */
function renderExpanded() {
  render(<Yara />);
  const summaries = screen.getAllByRole('button', { expanded: false });
  summaries.forEach((summary) => fireEvent.click(summary));
}

const exportRule = () => captureExport(fireEvent, screen.getByRole('button', { name: 'Export YARA Rule' }));

describe('YARA rule builder', { timeout: 20000 }, () => {
  it('requires a valid rule name before preview/export', () => {
    renderExpanded();
    expect(screen.getByRole('button', { name: 'Preview Rule' })).toBeDisabled();
    type(/^Rule Name/, '1bad');
    expect(screen.getByRole('button', { name: 'Preview Rule' })).toBeDisabled();
    type(/^Rule Name/, 'Emotet Loader');
    expect(screen.getByRole('button', { name: 'Preview Rule' })).toBeEnabled();
  });

  it('exports a rule with meta, tags, strings and the chosen condition', async () => {
    renderExpanded();
    type(/^Rule Name/, 'Emotet Loader');
    type(/^Author/, 'Alice');
    type(/^Description/, 'drops "payload" to C:\\Temp');
    type('Add Tag', 'emotet');
    fireEvent.click(screen.getByRole('button', { name: 'Add tag' }));
    addString('mz', '4D 5A', 'HEX');
    addString('path', 'C:\\Windows\\evil.dll');
    choose('String Match', 'Any of them');
    type(/^File Size/, '512');

    expect(screen.getByText('Strings (2)')).toBeInTheDocument();
    expect(screen.getByLabelText(/^Identifier/)).toHaveValue(''); // form reset after add
    const { filename, content } = await exportRule();
    expect(filename).toBe('Emotet_Loader.yar');
    expect(content).toMatch(/^rule Emotet_Loader : emotet \{/);
    expect(content).toContain('    author = "Alice"\n');
    expect(content).toContain('    description = "drops \\"payload\\" to C:\\\\Temp"\n');
    expect(content).toContain('    $mz = { 4D 5A }\n');
    expect(content).toContain('    $path = "C:\\\\Windows\\\\evil.dll"\n');
    expect(content).toMatch(/condition:\n {4}any of them and filesize < 512KB/);
  });

  it('rejects an invalid or duplicate string identifier with a field error', () => {
    renderExpanded();
    addString('9bad', 'x');
    expect(screen.getByText(/Identifier must start with a letter/)).toBeInTheDocument();
    addString('ok', 'x');
    addString('ok', 'y');
    expect(screen.getByText('Identifier must be unique')).toBeInTheDocument();
  });

  it('validates hex string values', () => {
    renderExpanded();
    addString('h', 'ZZ', 'HEX');
    expect(screen.getByText('Hex value must contain only hexadecimal digits and spaces')).toBeInTheDocument();
  });

  it('strings can be deleted', () => {
    renderExpanded();
    addString('a', 'x');
    fireEvent.click(screen.getByText('Strings (1)'));
    fireEvent.click(screen.getByRole('button', { name: 'Delete string' }));
    expect(screen.queryByText(/^Strings \(/)).not.toBeInTheDocument();
  });

  it('Reset (after confirming) clears the form', async () => {
    renderExpanded();
    type(/^Rule Name/, 'Temp');
    addString('a', 'x');
    fireEvent.click(screen.getByRole('button', { name: 'Reset' }));
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Confirm' }));
    await waitFor(() => expect(screen.getByLabelText(/^Rule Name/)).toHaveValue(''));
    expect(screen.queryByText(/^Strings \(/)).not.toBeInTheDocument();
  });
});
