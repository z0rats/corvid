import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import i18n from '../../../../../core/i18n';
import ExportCalculation from './ExportCalculation';
import { CVSS40_INITIAL } from '../../../shared/state/cvssAtoms';

const { downloadBlob } = vi.hoisted(() => ({ downloadBlob: vi.fn() }));
vi.mock('../../../shared/utils/fileUtils', () => ({ downloadBlob }));

const { base, threat, supplemental, environmental } = CVSS40_INITIAL.metrics;
const metrics = {
  ...base,
  attack_vector: 'L',
  vulnerable_system_confidentiality: 'H',
  ...threat,
  exploit_maturity: 'A',
  ...supplemental,
  safety: 'P',
  provider_urgency: 'R',
  ...environmental,
  modified_attack_vector: 'P',
  modified_subsequent_system_availability: 'H',
};
const scores = { base_score: 8.7, base_severity: 'High' };
const vector = 'CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/E:A/MAV:P/MSA:H/S:P/U:Red';

async function exportAs(format) {
  render(<ExportCalculation metrics={metrics} scores={scores} vectorString={vector} />);
  if (format === 'markdown') {
    fireEvent.click(screen.getByRole('button', { name: /export calculation/i }));
  } else {
    fireEvent.click(screen.getByRole('button', { name: 'Export options' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: /json/i }));
  }
  expect(downloadBlob).toHaveBeenCalledTimes(1);
  const [blob, filename] = downloadBlob.mock.calls[0];
  return { filename, content: await blob.text() };
}

describe('CVSS 4.0 ExportCalculation', () => {
  beforeEach(() => downloadBlob.mockReset());
  afterEach(() => i18n.changeLanguage('en'));

  it('keeps the translated metric labels in a Russian export', async () => {
    await i18n.changeLanguage('ru');
    render(<ExportCalculation metrics={metrics} scores={scores} vectorString={vector} />);
    fireEvent.click(screen.getByRole('button', { name: i18n.t('cvssCalculator:common.exportCalculation') }));
    const content = await downloadBlob.mock.calls[0][0].text();
    expect(content).toContain('**Вектор атаки (AV)**: Local');
    expect(content).not.toMatch(/cvss40\.export\./);
  });

  it('exports base, threat, environmental and supplemental metrics as JSON', async () => {
    const { filename, content } = await exportAs('json');
    const json = JSON.parse(content);

    expect(filename).toBe('cvss_4.0_calculation.json');
    expect(json.vectorString).toBe(vector);
    expect(json.baseScore).toBe(8.7);
    expect(json.baseSeverity).toBe('High');
    expect(json.baseMetrics.attackVector).toBe('Local');
    expect(json.baseMetrics.vulnerableSystemConfidentiality).toBe('High');
    expect(json.threatMetrics.exploitMaturity).toBe('Attacked');
    // Field names and order are the export's public shape - consumers parse these files.
    expect(Object.keys(json.baseMetrics)).toEqual([
      'attackVector', 'attackComplexity', 'attackRequirements', 'privilegesRequired', 'userInteraction',
      'vulnerableSystemConfidentiality', 'vulnerableSystemIntegrity', 'vulnerableSystemAvailability',
      'subsequentSystemConfidentiality', 'subsequentSystemIntegrity', 'subsequentSystemAvailability',
    ]);
    expect(Object.keys(json.threatMetrics)).toEqual(['exploitMaturity']);

    expect(json.environmentalMetrics).toMatchObject({
      modifiedAttackVector: 'Physical',
      modifiedAttackComplexity: 'Not Defined',
      modifiedSubsequentSystemAvailability: 'High',
    });
    expect(Object.keys(json.environmentalMetrics)).toHaveLength(Object.keys(environmental).length);

    expect(json.supplementalMetrics).toMatchObject({
      safety: 'Present',
      automatable: 'Not Defined',
      providerUrgency: 'Red',
    });
    expect(Object.keys(json.supplementalMetrics)).toHaveLength(Object.keys(supplemental).length);
  });

  it('exports every metric group in the markdown report', async () => {
    const { filename, content } = await exportAs('markdown');

    expect(filename).toBe('cvss_4.0_calculation.md');
    expect(content).toContain('**Attack Vector (AV)**: Local');
    expect(content).toContain('**Exploit Maturity (E)**: Attacked');
    expect(content).toContain('## Environmental Metrics');
    expect(content).toContain('**Attack Vector (MAV)**: Physical');
    expect(content).toContain('**Availability (MSA)**: High');
    expect(content).toContain('## Supplemental Metrics');
    expect(content).toContain('**Safety (S)**: Present');
    expect(content).toContain('**Provider Urgency (U)**: Red');
    expect(content).toContain('Overall Score: 8.7 (High)');
    // Every metric line resolved to a real translation, not a raw i18n key.
    expect(content).not.toMatch(/cvss40\.export\./);
  });

  it('splits the environmental section into the same sub-groups as the base metrics', async () => {
    const { content } = await exportAs('markdown');
    const environmental = content.slice(content.indexOf('## Environmental Metrics'), content.indexOf('## Supplemental Metrics'));

    expect(environmental).toMatch(/### Exploitability Metrics\n- \*\*Attack Vector \(MAV\)\*\*/);
    expect(environmental).toMatch(/### Vulnerable System Impact\n- \*\*Confidentiality \(MVC\)\*\*/);
    expect(environmental).toMatch(/### Subsequent System Impact\n- \*\*Confidentiality \(MSC\)\*\*/);
  });

  it('falls back to a zero None score before the first calculation', async () => {
    render(<ExportCalculation metrics={metrics} scores={{}} vectorString="" />);
    fireEvent.click(screen.getByRole('button', { name: 'Export options' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: /json/i }));
    const json = JSON.parse(await downloadBlob.mock.calls[0][0].text());
    expect(json.baseScore).toBe(0);
    expect(json.baseSeverity).toBe('None');
  });
});
