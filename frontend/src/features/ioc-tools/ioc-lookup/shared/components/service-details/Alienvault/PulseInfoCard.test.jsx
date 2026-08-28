import React from 'react';
import { render, screen } from '@testing-library/react';
import PulseInfoCard from './PulseInfoCard';

describe('PulseInfoCard', () => {
  it('renders a zero-pulse count without a referenced-pulses section', () => {
    render(<PulseInfoCard pulseInfo={{}} />);

    expect(screen.getByText('Pulse Information')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('Pulses')).toBeInTheDocument();
    expect(screen.queryByText('Referenced Pulses:')).not.toBeInTheDocument();
  });

  it('uses the singular label for exactly one pulse', () => {
    render(<PulseInfoCard pulseInfo={{ count: 1, pulses: [{ id: 'p1', name: 'Campaign A' }] }} />);

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('Pulse')).toBeInTheDocument();
  });

  it('lists deduplicated pulse chips and flags the unique count when lower than the total', () => {
    render(
      <PulseInfoCard
        pulseInfo={{
          count: 3,
          pulses: [
            { id: 'p1', name: 'Campaign A', TLP: 'RED' },
            { id: 'p1', name: 'Campaign A', TLP: 'RED' },
          ],
        }}
      />
    );

    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText(/\(1 unique\)/)).toBeInTheDocument();
    expect(screen.getByText('Referenced Pulses:')).toBeInTheDocument();
    expect(screen.getByText('Campaign A')).toBeInTheDocument();
  });
});
