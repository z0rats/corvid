import React from 'react';
import { render, screen } from '@testing-library/react';
import CrowdSecReputationCard from './CrowdSecReputationCard';

describe('CrowdSecReputationCard', () => {
  it('renders the ip reputation fields', () => {
    render(
      <CrowdSecReputationCard
        result={{
          ip: '1.2.3.4',
          ip_range_score: 3,
          as_name: 'Example AS',
          location: { country: 'US', city: 'Ashburn', reverse_dns: 'host.example.com' },
          remediation: 'monitor',
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('IP Reputation Details (1.2.3.4)')).toBeInTheDocument();
    expect(screen.getByText('3/5')).toBeInTheDocument();
    expect(screen.getByText('Example AS')).toBeInTheDocument();
    expect(screen.getByText('US')).toBeInTheDocument();
    expect(screen.getByText('Ashburn')).toBeInTheDocument();
    expect(screen.getByText('host.example.com')).toBeInTheDocument();
    expect(screen.getByText('monitor')).toBeInTheDocument();
  });

  it('falls back to N/A and the ioc prop when fields are missing', () => {
    render(<CrowdSecReputationCard result={{}} ioc="1.2.3.4" />);

    expect(screen.getByText('IP Reputation Details (1.2.3.4)')).toBeInTheDocument();
    expect(screen.getByText('N/A/5')).toBeInTheDocument();
    expect(screen.getAllByText('N/A').length).toBeGreaterThan(0);
  });
});
