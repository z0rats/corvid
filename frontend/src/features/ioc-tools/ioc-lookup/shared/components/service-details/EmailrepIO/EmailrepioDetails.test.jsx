import React from 'react';
import { render, screen } from '@testing-library/react';
import EmailrepioDetails from './EmailrepioDetails';

describe('EmailrepioDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<EmailrepioDetails result={null} ioc="alice@example.com" />);
    expect(
      screen.getByText('Emailrep.io details are unavailable or the data is incomplete.')
    ).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(
      <EmailrepioDetails result={{ error: true, message: 'timeout' }} ioc="alice@example.com" />
    );
    expect(screen.getByText('Error fetching Emailrep.io details: timeout')).toBeInTheDocument();
  });

  it('shows the unavailable message when details is missing', () => {
    render(<EmailrepioDetails result={{ reputation: 'high' }} ioc="alice@example.com" />);
    expect(
      screen.getByText('Emailrep.io details are unavailable or the data is incomplete.')
    ).toBeInTheDocument();
  });

  it('renders reputation fields with yes/no formatting', () => {
    render(
      <EmailrepioDetails
        result={{
          email: 'alice@example.com',
          reputation: 'high',
          suspicious: false,
          references: 3,
          details: {
            blacklisted: true,
            malicious_activity: false,
            credentials_leaked: true,
            first_seen: '2020-01-01',
            domain_exists: true,
            profiles: [],
          },
        }}
        ioc="alice@example.com"
      />
    );

    expect(screen.getByText('Reputation & Details')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('2020-01-01')).toBeInTheDocument();
    expect(screen.getByText('No profiles found.')).toBeInTheDocument();
  });

  it('falls back to N/A for a field with no value', () => {
    render(
      <EmailrepioDetails
        result={{ details: { profiles: [] } }}
        ioc="alice@example.com"
      />
    );

    expect(screen.getAllByText('N/A').length).toBeGreaterThan(0);
  });

  it('lists online profiles when present', () => {
    render(
      <EmailrepioDetails
        result={{ details: { profiles: ['twitter', 'linkedin'] } }}
        ioc="alice@example.com"
      />
    );

    expect(screen.getByText('twitter')).toBeInTheDocument();
    expect(screen.getByText('linkedin')).toBeInTheDocument();
    expect(screen.queryByText('No profiles found.')).not.toBeInTheDocument();
  });
});
