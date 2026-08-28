import React from 'react';
import { render, screen } from '@testing-library/react';
import MaltiverseDetails from './MaltiverseDetails';

describe('MaltiverseDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<MaltiverseDetails result={null} ioc="1.2.3.4" />);
    expect(
      screen.getByText('Maltiverse details are unavailable or data is incomplete.')
    ).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<MaltiverseDetails result={{ error: true, message: 'timeout' }} ioc="1.2.3.4" />);
    expect(screen.getByText('Error fetching Maltiverse details: timeout')).toBeInTheDocument();
  });

  it('shows an insufficient-data message when there is no classification or ip_addr', () => {
    render(<MaltiverseDetails result={{}} ioc="1.2.3.4" />);
    expect(screen.getByText('Insufficient data from Maltiverse.')).toBeInTheDocument();
  });

  it('renders ip characteristics and a no-blacklist-entries message', () => {
    render(
      <MaltiverseDetails
        result={{
          ip_addr: '1.2.3.4',
          classification: 'malicious',
          is_tor_node: true,
          is_cnc: false,
          blacklist: [],
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Threat Profile & IP Characteristics')).toBeInTheDocument();
    expect(screen.getByText('malicious')).toBeInTheDocument();
    expect(screen.getByText('No blacklist entries found.')).toBeInTheDocument();
  });

  it('renders a table row for each blacklist entry', () => {
    render(
      <MaltiverseDetails
        result={{
          ip_addr: '1.2.3.4',
          classification: 'malicious',
          blacklist: [
            { description: 'Known C2 server', first_seen: '2024-01-01', source: 'FeedX' },
          ],
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Blacklist Mentions (1)')).toBeInTheDocument();
    expect(screen.getByText('Known C2 server')).toBeInTheDocument();
    expect(screen.getByText('FeedX')).toBeInTheDocument();
  });
});
