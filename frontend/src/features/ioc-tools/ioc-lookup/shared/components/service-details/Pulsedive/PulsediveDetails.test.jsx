import React from 'react';
import { render, screen } from '@testing-library/react';
import PulsediveDetails from './PulsediveDetails';

describe('PulsediveDetails', () => {
  it('shows a loading message when result is missing', () => {
    render(<PulsediveDetails result={null} ioc="1.2.3.4" />);
    expect(screen.getByText('Loading Pulsedive details...')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<PulsediveDetails result={{ error: true, message: 'timeout' }} ioc="1.2.3.4" />);
    expect(screen.getByText('Error fetching Pulsedive details: timeout')).toBeInTheDocument();
  });

  it('shows a not-found message when status is "Not found"', () => {
    render(<PulsediveDetails result={{ status: 'Not found' }} ioc="1.2.3.4" />);
    expect(
      screen.getByText('Indicator "1.2.3.4" not found or no details in Pulsedive.')
    ).toBeInTheDocument();
  });

  it('shows a not-found message when results is empty', () => {
    render(<PulsediveDetails result={{ results: [] }} ioc="1.2.3.4" />);
    expect(
      screen.getByText('Indicator "1.2.3.4" not found or no details in Pulsedive.')
    ).toBeInTheDocument();
  });

  it('renders the risk level and a no-properties message', () => {
    render(
      <PulsediveDetails
        result={{ results: [{ indicator: '1.2.3.4', risk: 'high', summary: { properties: {} } }] }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Pulsedive Analysis for:')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('No specific properties found.')).toBeInTheDocument();
  });

  it('renders dns, geo, and http properties when present', () => {
    render(
      <PulsediveDetails
        result={{
          results: [
            {
              indicator: '1.2.3.4',
              risk: 'medium',
              summary: {
                properties: {
                  dns: { ptr: 'host.example.com' },
                  geo: { country: 'US', countrycode: 'US', city: 'Ashburn', org: 'Amazon' },
                  http: { '++content-type': 'text/html', '++code': '200' },
                },
              },
            },
          ],
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('DNS PTR')).toBeInTheDocument();
    expect(screen.getByText(/host\.example\.com/)).toBeInTheDocument();
    expect(screen.getByText('Geolocation')).toBeInTheDocument();
    expect(screen.getByText(/Ashburn/)).toBeInTheDocument();
    expect(screen.getByText('HTTP Properties')).toBeInTheDocument();
    expect(screen.getByText(/text\/html/)).toBeInTheDocument();
  });
});
