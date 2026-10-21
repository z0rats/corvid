import React, { cloneElement } from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Provider } from 'jotai';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../core/config/theme';
import api from '../../../core/services/baseApi';
import Cvss31Calculator from './Cvss31Calculator';

vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    ResponsiveContainer: ({ children }) => <div>{cloneElement(children, { width: 300, height: 300 })}</div>,
  };
});
vi.mock('../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));
const { downloadBlob } = vi.hoisted(() => ({ downloadBlob: vi.fn() }));
vi.mock('../shared/utils/fileUtils', async (importOriginal) => ({ ...(await importOriginal()), downloadBlob }));

const renderPage = () =>
  render(
    <Provider>
      <ThemeProvider theme={lightTheme}>
        <Cvss31Calculator />
      </ThemeProvider>
    </Provider>,
  );

async function choose(label, option) {
  fireEvent.mouseDown(screen.getByRole('combobox', { name: label }));
  fireEvent.click(await screen.findByRole('option', { name: option }));
}

const expand = (title) => fireEvent.click(screen.getByRole('button', { name: title }));

async function exportFile(format) {
  if (format === 'markdown') {
    fireEvent.click(screen.getByRole('button', { name: /export calculation/i }));
  } else {
    fireEvent.click(screen.getByRole('button', { name: 'Export options' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: /json/i }));
  }
  const [blob, filename] = downloadBlob.mock.calls.at(-1);
  return { filename, content: await blob.text() };
}

// Real 1 s debounce: assert on the request that eventually carries every edit rather than on
// call counts, which depend on how fast the UI steps run (slow under a full parallel suite).
describe('Cvss31Calculator', { timeout: 20000 }, () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.post.mockResolvedValue({ data: { vector_string: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H' } });
  });

  it('recalculates the score locally and fetches the vector string for the chosen metrics', async () => {
    renderPage();
    expect(screen.getAllByText('None').length).toBeGreaterThan(0);

    await choose('Confidentiality Impact (C)', 'High');
    await choose('Integrity Impact (I)', 'High');
    await choose('Availability Impact (A)', 'High');

    expect(screen.getAllByText('Critical').length).toBeGreaterThan(0);
    expect(screen.getAllByText('9.8').length).toBeGreaterThan(0);

    await waitFor(() => expect(api.post.mock.calls.at(-1)?.[1].base_metrics).toMatchObject({
      attack_vector: 'N',
      confidentiality_impact: 'H',
      integrity_impact: 'H',
      availability_impact: 'H',
    }), { timeout: 5000 });
    const [url, payload] = api.post.mock.calls.at(-1);
    expect(url).toBe('/api/cvss/v3.1/calculate');
    // Modified metrics left "Not defined" are omitted so the backend falls back to base values.
    expect(payload.environmental_metrics).toEqual({
      confidentiality_requirement: 'X',
      integrity_requirement: 'X',
      availability_requirement: 'X',
    });
    expect(await screen.findByText(/CVSS:3\.1\/AV:N\/AC:L/)).toBeInTheDocument();
  });

  it('sends only the modified environmental metrics that were set', async () => {
    renderPage();
    await choose('Confidentiality Impact (C)', 'High');
    expand('Temporal Score Metrics');
    await choose('Exploit Code Maturity (E)', 'Unproven that exploit exists');
    expand('Environmental Score Metrics');
    await choose('Attack Vector (MAV)', 'Physical');
    await choose('Confidentiality Requirement (CR)', 'Low');

    await waitFor(() => {
      const payload = api.post.mock.calls.at(-1)?.[1];
      expect(payload.temporal_metrics.exploit_code_maturity).toBe('U');
      expect(payload.environmental_metrics).toEqual({
        modified_attack_vector: 'P',
        confidentiality_requirement: 'L',
        integrity_requirement: 'X',
        availability_requirement: 'X',
      });
    }, { timeout: 5000 });

    // Resetting a modified metric to "Not defined" drops it from the payload again.
    await choose('Attack Vector (MAV)', 'Not defined');
    await waitFor(
      () => expect(api.post.mock.calls.at(-1)[1].environmental_metrics).not.toHaveProperty('modified_attack_vector'),
      { timeout: 5000 },
    );
  });

  it('exports the selected base, temporal and environmental metrics as JSON', async () => {
    renderPage();
    await choose('Confidentiality Impact (C)', 'High');
    await choose('Integrity Impact (I)', 'Low');
    await choose('Scope (S)', 'Changed');
    expand('Environmental Score Metrics');
    await choose('Availability Requirement (AR)', 'High');

    const { filename, content } = await exportFile('json');
    const json = JSON.parse(content);

    expect(filename).toBe('cvss_calculation.json');
    expect(json.base).toMatchObject({
      attackVector: 'Network',
      scope: 'Changed',
      confidentialityImpact: 'High',
      integrityImpact: 'Low',
      availabilityImpact: 'None',
    });
    expect(json.base.baseScore).toBeGreaterThan(0);
    expect(json.temporal.exploitCodeMaturity).toBe('Not Defined');
    expect(json.environmental.modifiedAttackVector).toBe('Not Defined');
    expect(json.environmental.availabilityRequirement).toBe('High');
    expect(json.overallScore).toBe(json.environmental.environmentalScore);
  });

  it('exports a markdown report covering every metric group', async () => {
    renderPage();
    await choose('Attack Vector (AV)', 'Local');

    const { filename, content } = await exportFile('markdown');

    expect(filename).toBe('cvss_calculation.md');
    expect(content).toMatch(/Attack Vector \(AV\)\*?\*?: Local/);
    expect(content).toContain('Temporal');
    expect(content).toContain('Environmental');
    expect(content).toMatch(/Confidentiality Requirement \(CR\)\*?\*?: Not Defined/);
  });

  it('shows the backend error when the vector string cannot be fetched', async () => {
    api.post.mockRejectedValue({ response: { data: { detail: 'Invalid metric combination' } } });
    renderPage();
    await choose('Attack Complexity (AC)', 'High');
    expect(await screen.findByText('Invalid metric combination', {}, { timeout: 5000 })).toBeInTheDocument();
  });
});
