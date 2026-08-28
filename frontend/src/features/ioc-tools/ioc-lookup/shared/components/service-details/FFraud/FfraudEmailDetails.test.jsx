import React from 'react';
import { render, screen } from '@testing-library/react';
import FfraudEmailDetails from './FfraudEmailDetails';

describe('FfraudEmailDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<FfraudEmailDetails result={null} />);
    expect(
      screen.getByText('FFraud details are unavailable or the data is incomplete.')
    ).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<FfraudEmailDetails result={{ error: true, message: 'timeout' }} />);
    expect(screen.getByText('Error fetching FFraud details: timeout')).toBeInTheDocument();
  });

  it('renders the email checks with yes/no formatting', () => {
    render(
      <FfraudEmailDetails
        result={{
          is_disposable: false,
          valid_format: true,
          is_role_address: true,
          safe_domain: false,
          community_blacklisted: false,
        }}
      />
    );

    expect(screen.getByText('Email Checks')).toBeInTheDocument();
    expect(screen.getByText('Disposable')).toBeInTheDocument();
    expect(screen.getByText('Valid Format')).toBeInTheDocument();
  });

  it('shows the blacklist report count when community blacklisted', () => {
    render(<FfraudEmailDetails result={{ community_blacklisted: true, blacklist_reports: 5 }} />);
    expect(screen.getByText('Yes (5 report(s))')).toBeInTheDocument();
  });
});
