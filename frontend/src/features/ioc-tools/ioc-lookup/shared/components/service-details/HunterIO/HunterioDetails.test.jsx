import React from 'react';
import { render, screen } from '@testing-library/react';
import HunterioDetails from './HunterioDetails';

describe('HunterioDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<HunterioDetails result={null} ioc="alice@example.com" />);
    expect(
      screen.getByText('Hunter.io details are unavailable or the data is incomplete.')
    ).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(
      <HunterioDetails result={{ error: true, message: 'timeout' }} ioc="alice@example.com" />
    );
    expect(screen.getByText('Error fetching Hunter.io details: timeout')).toBeInTheDocument();
  });

  it('renders verification fields and a no-sources message', () => {
    render(
      <HunterioDetails
        result={{
          data: {
            email: 'alice@example.com',
            result: 'deliverable',
            status: 'valid',
            score: 92,
            sources: [],
          },
        }}
        ioc="alice@example.com"
      />
    );

    expect(screen.getByText('Email Verification Details')).toBeInTheDocument();
    expect(screen.getByText('deliverable')).toBeInTheDocument();
    expect(screen.getByText('valid')).toBeInTheDocument();
    expect(screen.getByText('92')).toBeInTheDocument();
    expect(screen.getByText('Sources (0)')).toBeInTheDocument();
    expect(screen.getByText('No public sources found for this email address.')).toBeInTheDocument();
  });

  it('renders a table row for each source', () => {
    render(
      <HunterioDetails
        result={{
          data: {
            email: 'alice@example.com',
            sources: [
              {
                domain: 'example.com',
                uri: 'https://example.com/page',
                extracted_on: '2024-01-01',
                last_seen_on: '2024-02-01',
                still_on_page: true,
              },
            ],
          },
        }}
        ioc="alice@example.com"
      />
    );

    expect(screen.getByText('Sources (1)')).toBeInTheDocument();
    expect(screen.getByText('example.com')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'https://example.com/page' })).toHaveAttribute(
      'href',
      'https://example.com/page'
    );
    expect(screen.getByText('2024-01-01')).toBeInTheDocument();
  });
});
