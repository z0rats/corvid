import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import yaml from 'js-yaml';
import Sigma from './Sigma';
import { captureExport } from '../shared/testUtils';

const type = (label, value) => fireEvent.change(screen.getByLabelText(label), { target: { value } });
const pressEnter = (label) => fireEvent.keyDown(screen.getByLabelText(label), { key: 'Enter' });
const addVia = (label, value) => { type(label, value); pressEnter(label); };
const addWith = (label, value, button) => {
  type(label, value);
  fireEvent.click(screen.getByRole('button', { name: button }));
};
const SECTIONS = ['References', 'Tags', 'Log Source', 'Detection', 'Fields', 'False Positives'];
function renderExpanded() {
  render(<Sigma />);
  for (const title of SECTIONS) fireEvent.click(screen.getByText(title, { selector: 'h6, p, span, .MuiTypography-root' }));
}

function openPreview() {
  fireEvent.click(screen.getByRole('button', { name: 'Preview Rule' }));
  return screen.getByRole('dialog');
}

beforeEach(() => {
  vi.spyOn(window, 'alert').mockImplementation(() => {});
});
afterEach(() => vi.restoreAllMocks());

describe('Sigma rule builder', () => {
  it('preview/export need a title and an id (the id starts pre-generated)', () => {
    render(<Sigma />);
    expect(screen.getByLabelText('ID *').value).not.toBe('');
    expect(screen.getByRole('button', { name: 'Preview Rule' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Export Sigma Rule' })).toBeDisabled();

    type('Title *', 'Suspicious vssadmin');
    expect(screen.getByRole('button', { name: 'Preview Rule' })).toBeEnabled();
    type('ID *', '  ');
    expect(screen.getByRole('button', { name: 'Preview Rule' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Generate UUID' }));
    expect(screen.getByLabelText('ID *').value).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    expect(screen.getByRole('button', { name: 'Preview Rule' })).toBeEnabled();
  });

  it('collects every section into the previewed rule', () => {
    renderExpanded();
    type('Title *', 'Shadow copy deletion');
    type('ID *', '11111111-2222-4333-8444-555555555555');
    type('Description', 'Detects vssadmin delete shadows');
    addVia('Add Author', 'Alice');
    addVia('Add Author', 'Alice'); // duplicate ignored
    addVia('Reference', 'https://example.com/blog');
    addWith('Add Tag', 'Attack.T1490', 'Add tag'); // lower-cased on add
    addVia('Add Field', 'CommandLine');
    addVia('Add False Positive', 'Backup software');
    addWith('Keyword', 'vssadmin', 'Add keyword');

    expect(screen.getAllByText('Alice')).toHaveLength(1);
    expect(screen.getByText('#attack.t1490')).toBeInTheDocument();

    const text = openPreview().textContent;
    for (const expected of [
      'title: Shadow copy deletion',
      'id: 11111111-2222-4333-8444-555555555555',
      'Detects vssadmin delete shadows',
      'Alice',
      'https://example.com/blog',
      'attack.t1490',
      'CommandLine',
      'Backup software',
      'vssadmin',
      'detection:',
    ]) {
      expect(text).toContain(expected);
    }

    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Close' }));
    return waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('exports a valid Sigma YAML file including keywords and conditions', async () => {
    renderExpanded();
    type('Title *', 'Shadow copy deletion: vssadmin');
    type('Field', 'CommandLine');
    type('Value', 'delete shadows');
    fireEvent.click(screen.getByRole('button', { name: 'Add condition' }));
    addWith('Keyword', 'vssadmin', 'Add keyword');

    const { filename, content } = await captureExport(fireEvent, screen.getByRole('button', { name: 'Export Sigma Rule' }));
    expect(filename).toBe('Shadow_copy_deletion_vssadmin.yml');
    const doc = yaml.load(content);
    expect(doc.title).toBe('Shadow copy deletion: vssadmin');
    expect(doc.detection).toEqual({
      selection: { CommandLine: 'delete shadows' },
      keywords: ['vssadmin'],
      condition: 'selection and keywords',
    });
  });

  it('chips can be removed again', () => {
    renderExpanded();
    addWith('Add Tag', 'attack.execution', 'Add tag');
    addVia('Add Field', 'Image');
    const tagChip = screen.getByText('#attack.execution').closest('.MuiChip-root');
    fireEvent.click(within(tagChip).getByTestId('CancelIcon'));
    expect(screen.queryByText('#attack.execution')).not.toBeInTheDocument();
    const fieldChip = screen.getByText('Image').closest('.MuiChip-root');
    fireEvent.click(within(fieldChip).getByTestId('CancelIcon'));
    expect(screen.queryByText('Image')).not.toBeInTheDocument();
  });

  it('a blank keyword is rejected with an alert', () => {
    renderExpanded();
    fireEvent.click(screen.getByRole('button', { name: 'Add keyword' }));
    expect(window.alert).toHaveBeenCalledWith('Keyword is required.');
  });

  it('a selection condition needs field+value, then lands in the rule', () => {
    renderExpanded();
    type('Title *', 'Cond');
    const add = screen.getByRole('button', { name: 'Add condition' });
    expect(add).toBeDisabled();
    type('Field', 'CommandLine');
    type('Value', 'delete shadows');
    fireEvent.click(add);
    expect(screen.getByLabelText('Value')).toHaveValue('');
    const text = openPreview().textContent;
    expect(text).toContain('CommandLine');
    expect(text).toContain('delete shadows');
  });

  it('Reset asks for confirmation; cancel keeps, confirm clears', async () => {
    // Regression: the confirmation dialog was never rendered, so Reset did nothing.
    render(<Sigma />);
    type('Title *', 'Keep me');
    fireEvent.click(screen.getByRole('button', { name: 'Reset' }));
    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Reset Form')).toBeInTheDocument();

    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(screen.getByLabelText('Title *')).toHaveValue('Keep me');

    fireEvent.click(screen.getByRole('button', { name: 'Reset' }));
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Confirm' }));
    await waitFor(() => expect(screen.getByLabelText('Title *')).toHaveValue(''));
  });
});
