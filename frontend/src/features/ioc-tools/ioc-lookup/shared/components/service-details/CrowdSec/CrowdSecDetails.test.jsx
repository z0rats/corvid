import React from 'react';
import { render, screen } from '@testing-library/react';
import CrowdSecDetails from './CrowdSecDetails';

// The reputation card, scores chart, and countries section (map + pie) each have
// their own dedicated tests; this covers the orchestrator's own branching and
// which optional sections (behaviours/attack details/references) get mounted.
describe('CrowdSecDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<CrowdSecDetails result={null} ioc="1.2.3.4" />);
    expect(screen.getByText('CrowdSec details are unavailable.')).toBeInTheDocument();
  });

  it('shows a not-found message when the error mentions "not found"', () => {
    render(<CrowdSecDetails result={{ message: 'IP not found in database' }} ioc="1.2.3.4" />);
    expect(screen.getByText('IP not found in CrowdSec CTI.')).toBeInTheDocument();
  });

  it('shows an error message when the result carries a generic error', () => {
    render(<CrowdSecDetails result={{ error: true, message: 'timeout' }} ioc="1.2.3.4" />);
    expect(screen.getByText('Error fetching CrowdSec details: timeout')).toBeInTheDocument();
  });

  it('shows an insufficient-data message when ip_range_score is missing', () => {
    render(<CrowdSecDetails result={{}} ioc="1.2.3.4" />);
    expect(screen.getByText('Insufficient data received from CrowdSec CTI.')).toBeInTheDocument();
  });

  it('renders the reputation card and scores chart for a minimal valid result', () => {
    render(<CrowdSecDetails result={{ ip: '1.2.3.4', ip_range_score: 2 }} ioc="1.2.3.4" />);

    expect(screen.getByText('IP Reputation Details (1.2.3.4)')).toBeInTheDocument();
    expect(screen.getByText('CTI Scores Breakdown')).toBeInTheDocument();
    expect(screen.queryByText('Behaviours')).not.toBeInTheDocument();
    expect(screen.queryByText('Attack Details')).not.toBeInTheDocument();
    expect(screen.queryByText('References')).not.toBeInTheDocument();
  });

  it('mounts behaviours, attack details, and references when present', () => {
    render(
      <CrowdSecDetails
        result={{
          ip: '1.2.3.4',
          ip_range_score: 4,
          behaviors: [{ name: 'ssh-bf', description: 'SSH bruteforce' }],
          attack_details: [{ name: 'http-probing', description: 'HTTP probing' }],
          references: [{ url: 'https://example.com/ref' }],
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Behaviours')).toBeInTheDocument();
    expect(screen.getByText('ssh-bf')).toBeInTheDocument();
    expect(screen.getByText('Attack Details')).toBeInTheDocument();
    expect(screen.getByText('http-probing')).toBeInTheDocument();
    expect(screen.getByText('References')).toBeInTheDocument();
    expect(screen.getByText('Reference 1')).toBeInTheDocument();
    expect(screen.getByText('https://example.com/ref')).toBeInTheDocument();
  });
});
