import React from 'react';
import { render, screen } from '@testing-library/react';
import FirstEpssDetails from './FirstEpssDetails';

describe('FirstEpssDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<FirstEpssDetails result={null} />);
    expect(screen.getByText('EPSS details are unavailable.')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<FirstEpssDetails result={{ error: true, message: 'timeout' }} />);
    expect(screen.getByText('Error fetching EPSS details: timeout')).toBeInTheDocument();
  });

  it('shows the not-found message when data is empty', () => {
    render(<FirstEpssDetails result={{ data: [] }} />);
    expect(screen.getByText('No EPSS score found for this CVE.')).toBeInTheDocument();
  });

  it('formats the EPSS score and percentile as percentages', () => {
    render(
      <FirstEpssDetails
        result={{ data: [{ epss: '0.5321', percentile: '0.98765', date: '2024-01-15' }] }}
      />
    );

    expect(screen.getByText('Exploit Prediction Scoring System')).toBeInTheDocument();
    expect(screen.getByText('53.21%')).toBeInTheDocument();
    expect(screen.getByText('98.8%')).toBeInTheDocument();
    expect(screen.getByText('As of 2024-01-15')).toBeInTheDocument();
  });

  it('omits the as-of line when date is absent', () => {
    render(<FirstEpssDetails result={{ data: [{ epss: '0.1', percentile: '0.2' }] }} />);
    expect(screen.queryByText(/As of/)).not.toBeInTheDocument();
  });
});
