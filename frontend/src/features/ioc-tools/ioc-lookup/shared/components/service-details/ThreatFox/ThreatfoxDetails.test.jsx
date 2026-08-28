import React from 'react';
import { render, screen } from '@testing-library/react';
import ThreatfoxDetails from './ThreatfoxDetails';

describe('ThreatfoxDetails', () => {
  it('shows a loading message when result is missing', () => {
    render(<ThreatfoxDetails result={null} ioc="1.2.3.4" />);
    expect(screen.getByText('Loading ThreatFox details...')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<ThreatfoxDetails result={{ error: true, message: 'timeout' }} ioc="1.2.3.4" />);
    expect(screen.getByText('Error fetching ThreatFox details: timeout')).toBeInTheDocument();
  });

  it('shows a not-found message when query_status is no_result', () => {
    render(<ThreatfoxDetails result={{ query_status: 'no_result' }} ioc="1.2.3.4" />);
    expect(screen.getByText('IOC "1.2.3.4" not found in ThreatFox database.')).toBeInTheDocument();
  });

  it('shows the query status for any other non-ok status', () => {
    render(<ThreatfoxDetails result={{ query_status: 'illegal_ioc_format' }} ioc="1.2.3.4" />);
    expect(
      screen.getByText('ThreatFox query status: illegal ioc format.')
    ).toBeInTheDocument();
  });

  it('shows a found-no-entries message when data is empty', () => {
    render(<ThreatfoxDetails result={{ query_status: 'ok', data: [] }} ioc="1.2.3.4" />);
    expect(
      screen.getByText('IOC Found by ThreatFox, but no specific data entries returned.')
    ).toBeInTheDocument();
  });

  it('renders each entry with its indicators', () => {
    render(
      <ThreatfoxDetails
        result={{
          query_status: 'ok',
          data: [
            {
              id: '12345',
              confidence_level: 90,
              ioc_value: 'evil.example',
              ioc_type: 'domain',
              ioc_type_desc: 'Domain Indicator',
              threat_type: 'botnet_cc',
              threat_type_desc: 'Botnet C2',
              malware: 'emotet',
              malware_printable: 'Emotet',
              malware_alias: 'Heodo',
              malware_malpedia: 'https://malpedia.example/emotet',
              first_seen_utc: '2024-01-01 00:00:00',
              last_seen_utc: '2024-01-02 00:00:00',
              reporter: 'abc',
              reference: 'https://twitter.com/abc/status/1',
              tags: ['emotet', 'c2'],
            },
          ],
        }}
        ioc="search-term-xyz"
      />
    );

    expect(screen.getByText('ThreatFox Intelligence for:')).toBeInTheDocument();
    expect(screen.getByText('Displaying 1 record(s) from ThreatFox.')).toBeInTheDocument();
    expect(screen.getByText('Entry ID: 12345 (Confidence: 90%)')).toBeInTheDocument();
    expect(screen.getByText('evil.example')).toBeInTheDocument();
    expect(screen.getByText('Emotet (emotet)')).toBeInTheDocument();
    expect(screen.getByText(/Alias:\s*Heodo/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /malpedia entry/i })).toHaveAttribute(
      'href',
      'https://malpedia.example/emotet'
    );
    expect(screen.getByText('abc')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'https://twitter.com/abc/status/1' })).toBeInTheDocument();
    expect(screen.getByText('emotet')).toBeInTheDocument();
    expect(screen.getByText('c2')).toBeInTheDocument();
  });
});
