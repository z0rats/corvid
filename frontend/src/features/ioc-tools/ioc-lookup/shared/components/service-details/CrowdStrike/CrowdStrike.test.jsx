import React from 'react';
import { render, screen } from '@testing-library/react';
import CrowdStrikeDetails from './CrowdStrike';

function makeIndicator(overrides = {}) {
  return {
    id: 'ind-1',
    indicator: 'evil.example',
    type: 'domain',
    malicious_confidence: 'high',
    published_date: 1700000000,
    last_updated: 1700100000,
    ...overrides,
  };
}

describe('CrowdStrikeDetails', () => {
  it('shows a no-info message when result is missing', () => {
    render(<CrowdStrikeDetails result={null} />);
    expect(
      screen.getByText('No intelligence information found for this indicator in CrowdStrike')
    ).toBeInTheDocument();
  });

  it('shows a no-info message when resources is empty', () => {
    render(<CrowdStrikeDetails result={{ resources: [] }} />);
    expect(
      screen.getByText('No intelligence information found for this indicator in CrowdStrike')
    ).toBeInTheDocument();
  });

  it('renders summary stats and an indicator card without optional chips', () => {
    render(<CrowdStrikeDetails result={{ resources: [makeIndicator()] }} />);

    expect(screen.getByText('Confidence Level')).toBeInTheDocument();
    expect(screen.getByText('80')).toBeInTheDocument();
    expect(screen.getByText('Indicators (1)')).toBeInTheDocument();
    expect(screen.getByText('evil.example')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    // No threat types / kill chains anywhere -> the charts card isn't rendered at all.
    expect(screen.queryByText('Threat Types')).not.toBeInTheDocument();
    expect(screen.queryByText('Kill Chain Phases')).not.toBeInTheDocument();
  });

  it('renders the threat-types chart section when indicators have threat types', () => {
    render(
      <CrowdStrikeDetails
        result={{ resources: [makeIndicator({ threat_types: ['ransomware'] })] }}
      />
    );

    expect(screen.getByText('Threat Types')).toBeInTheDocument();
    expect(screen.getByText('Threat Types:')).toBeInTheDocument();
    expect(screen.getByText('ransomware')).toBeInTheDocument();
  });

  it('renders the kill-chain stepper with the active phase expanded', () => {
    render(
      <CrowdStrikeDetails
        result={{ resources: [makeIndicator({ kill_chains: ['c2'] })] }}
      />
    );

    expect(screen.getByText('Kill Chain Phases')).toBeInTheDocument();
    expect(screen.getByText('Command & Control')).toBeInTheDocument();
    expect(screen.getByText('c2 (Observed 1 time(s))')).toBeInTheDocument();
    // Inactive phases are still listed but without their StepContent detail.
    expect(screen.getByText('Reconnaissance')).toBeInTheDocument();
  });

  it('renders actor and malware-family chips on an indicator', () => {
    render(
      <CrowdStrikeDetails
        result={{
          resources: [
            makeIndicator({ actors: ['FANCY BEAR'], malware_families: ['Emotet'] }),
          ],
        }}
      />
    );

    expect(screen.getByText('Threat Actors:')).toBeInTheDocument();
    expect(screen.getByText('FANCY BEAR')).toBeInTheDocument();
    expect(screen.getByText('Malware Families:')).toBeInTheDocument();
    expect(screen.getByText('Emotet')).toBeInTheDocument();
  });

  it('falls back to Unknown for a missing confidence label', () => {
    render(
      <CrowdStrikeDetails
        result={{ resources: [makeIndicator({ malicious_confidence: undefined })] }}
      />
    );

    expect(screen.getByText('Unknown')).toBeInTheDocument();
  });

  it('paginates when there are more than 5 indicators', () => {
    const resources = Array.from({ length: 7 }, (_, i) =>
      makeIndicator({ id: `ind-${i}`, indicator: `evil-${i}.example` })
    );
    render(<CrowdStrikeDetails result={{ resources }} />);

    expect(screen.getByText('evil-0.example')).toBeInTheDocument();
    expect(screen.queryByText('evil-5.example')).not.toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });
});
