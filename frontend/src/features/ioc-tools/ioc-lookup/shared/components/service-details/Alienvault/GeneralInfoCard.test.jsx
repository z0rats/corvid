import React from 'react';
import { render, screen } from '@testing-library/react';
import GeneralInfoCard from './GeneralInfoCard';

describe('GeneralInfoCard', () => {
  it('renders the indicator with a fallback to N/A', () => {
    render(<GeneralInfoCard result={{}} />);
    expect(screen.getByText('General Information')).toBeInTheDocument();
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('renders type, location, asn, reputation, and validation chips', () => {
    render(
      <GeneralInfoCard
        result={{
          indicator: 'evil.example',
          type: 'domain',
          city: 'Ashburn',
          region: 'VA',
          country_name: 'United States',
          asn: 'AS15169 Google',
          reputation: 3,
          validation: [{ name: 'whitelist_check' }],
        }}
      />
    );

    expect(screen.getByText('evil.example')).toBeInTheDocument();
    expect(screen.getByText('domain')).toBeInTheDocument();
    expect(screen.getByText('Ashburn, VA, United States')).toBeInTheDocument();
    expect(screen.getByText('AS15169 Google')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('whitelist_check')).toBeInTheDocument();
  });

  it('omits the reputation row when reputation is zero', () => {
    render(<GeneralInfoCard result={{ indicator: 'evil.example', reputation: 0 }} />);
    expect(screen.queryByText('Reputation Score')).not.toBeInTheDocument();
  });
});
