import React, { cloneElement } from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Provider } from 'jotai';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../core/config/theme';
import api from '../../../core/services/baseApi';
import Cvss40Calculator from './Cvss40Calculator';

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
        <Cvss40Calculator />
      </ThemeProvider>
    </Provider>,
  );

async function choose(label, option) {
  fireEvent.mouseDown(screen.getByRole('combobox', { name: label }));
  fireEvent.click(await screen.findByRole('option', { name: option }));
}

const expand = (title) => fireEvent.click(screen.getByRole('button', { name: title }));

// Real 500 ms debounce: assert on the request that eventually carries every edit rather than on
// call counts, which depend on how fast the UI steps run (slow under a full parallel suite).
describe('Cvss40Calculator', { timeout: 20000 }, () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.post.mockResolvedValue({
      data: {
        vector_string: 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/E:A/MAV:L/S:P',
        base_score: 8.2,
        base_severity: 'High',
      },
    });
  });

  it('routes each metric to its group in the request and shows the returned score', async () => {
    renderPage();
    expect(screen.getAllByText('None').length).toBeGreaterThan(0);

    await choose('Confidentiality (VC)', 'High');
    expand('Threat Metrics (optional)');
    await choose('Exploit Maturity (E)', 'Attacked');
    expand('Supplemental Metrics (optional)');
    await choose('Safety (S)', 'Present');
    expand('Environmental (Modified Base Metrics) (optional)');
    await choose('Attack Vector (MAV)', 'Local');

    await waitFor(() => {
      const [url, payload] = api.post.mock.calls.at(-1);
      expect(url).toBe('/api/cvss/v4.0/calculate');
      expect(payload.base_metrics.vulnerable_system_confidentiality).toBe('H');
      expect(payload.threat_metrics).toEqual({ exploit_maturity: 'A' });
      expect(payload.supplemental_metrics.safety).toBe('P');
      expect(payload.environmental_metrics.modified_attack_vector).toBe('L');
    }, { timeout: 5000 });
    const payload = api.post.mock.calls.at(-1)[1];
    expect(payload.base_metrics).not.toHaveProperty('safety');
    expect(payload.base_metrics).not.toHaveProperty('modified_attack_vector');

    expect(await screen.findByText(/Vector String: CVSS:4\.0\/AV:N/)).toBeInTheDocument();
    expect(screen.getAllByText('8.2').length).toBeGreaterThan(0);
    expect(screen.getAllByText('High').length).toBeGreaterThan(0);
  });

  it('exports what the user selected, including environmental and supplemental metrics', async () => {
    renderPage();
    expand('Supplemental Metrics (optional)');
    await choose('Recovery (R)', 'Irrecoverable');
    expand('Environmental (Modified Base Metrics) (optional)');
    await choose('Integrity (MVI)', 'Low');
    await screen.findByText(/Vector String: CVSS:4\.0/, {}, { timeout: 5000 });

    fireEvent.click(screen.getByRole('button', { name: /export calculation/i }));
    expect(downloadBlob).toHaveBeenCalledTimes(1);
    const [blob, filename] = downloadBlob.mock.calls[0];
    const markdown = await blob.text();

    expect(filename).toBe('cvss_4.0_calculation.md');
    expect(markdown).toContain('**Recovery (R)**: Irrecoverable');
    expect(markdown).toContain('**Integrity (MVI)**: Low');
    expect(markdown).toContain('Overall Score: 8.2 (High)');
  });

  it('explains a metric in an info dialog', async () => {
    renderPage();
    fireEvent.click(screen.getAllByRole('button', { name: 'Show metric info' })[0]);
    expect(await screen.findByRole('dialog')).toHaveTextContent(/context by which vulnerability exploitation is possible/);
  });

  it('shows the backend error when the score cannot be calculated', async () => {
    api.post.mockRejectedValue({ response: { data: { detail: 'Unsupported vector' } } });
    renderPage();
    await choose('Attack Vector (AV)', 'Physical');
    expect(await screen.findByText('Unsupported vector', {}, { timeout: 5000 })).toBeInTheDocument();
  });
});
