import React from 'react';
import { render, screen } from '@testing-library/react';
import UrlHausDetails from './UrlHausDetails';

const HOST_RESULT = {
  query_status: 'ok',
  host: 'evil.example',
  firstseen: '2019-01-15 07:09:01 UTC',
  url_count: '120',
  urlhaus_reference: 'https://urlhaus.abuse.ch/host/evil.example/',
  blacklists: { spamhaus_dbl: 'abused_legit_malware', surbl: 'not listed' },
  urls: [
    { id: '1', url: 'http://evil.example/a.exe', url_status: 'online', urlhaus_reference: 'https://urlhaus.abuse.ch/url/1/', tags: ['AZORult'] },
    { id: '2', url: 'http://evil.example/b.exe', url_status: 'offline', urlhaus_reference: 'https://urlhaus.abuse.ch/url/2/', tags: [] },
  ],
};

const URL_RESULT = {
  query_status: 'ok',
  url: 'http://evil.example/a.exe',
  url_status: 'online',
  host: 'evil.example',
  date_added: '2019-01-19 01:33:26 UTC',
  threat: 'malware_download',
  reporter: 'Cryptolaemus1',
  tags: ['emotet'],
  blacklists: { spamhaus_dbl: 'not listed', surbl: 'listed' },
  urlhaus_reference: 'https://urlhaus.abuse.ch/url/105821/',
  payloads: [{ filename: 'inv.doc', file_type: 'doc', signature: 'Heodo', response_sha256: 'a'.repeat(64) }],
};

describe('UrlHausDetails', () => {
  it('shows an unavailable message when there is no result', () => {
    render(<UrlHausDetails result={null} ioc="evil.example" />);
    expect(screen.getByText('URLhaus details are unavailable.')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<UrlHausDetails result={{ error: true, message: 'timeout' }} ioc="evil.example" />);
    expect(screen.getByText('Error fetching URLhaus details: timeout')).toBeInTheDocument();
  });

  it('shows a not-listed message for no_results', () => {
    render(<UrlHausDetails result={{ query_status: 'no_results' }} ioc="clean.example" />);
    expect(screen.getByText('"clean.example" is not listed in URLhaus.')).toBeInTheDocument();
  });

  it('shows the query status for any other non-ok status', () => {
    render(<UrlHausDetails result={{ query_status: 'invalid_host' }} ioc="x" />);
    expect(screen.getByText('URLhaus query status: invalid host.')).toBeInTheDocument();
  });

  it('renders a host result with its URL list and blacklist chips', () => {
    render(<UrlHausDetails result={HOST_RESULT} ioc="evil.example" />);
    expect(screen.getByText('Malware host: evil.example')).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
    expect(screen.getByText('http://evil.example/a.exe')).toBeInTheDocument();
    expect(screen.getByText('AZORult')).toBeInTheDocument();
    expect(screen.getByText('spamhaus_dbl: abused legit malware')).toBeInTheDocument();
    expect(screen.getByText('surbl: not listed')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View on URLhaus' })).toHaveAttribute(
      'href',
      'https://urlhaus.abuse.ch/host/evil.example/'
    );
  });

  it('caps the host URL list and reports how many were left out', () => {
    const urls = Array.from({ length: 13 }, (_, i) => ({
      id: String(i), url: `http://evil.example/${i}`, url_status: 'online', urlhaus_reference: `https://urlhaus.abuse.ch/url/${i}/`,
    }));
    render(<UrlHausDetails result={{ ...HOST_RESULT, urls }} ioc="evil.example" />);
    expect(screen.getByText('http://evil.example/9')).toBeInTheDocument();
    expect(screen.queryByText('http://evil.example/10')).not.toBeInTheDocument();
    expect(screen.getByText('…and 3 more on URLhaus.')).toBeInTheDocument();
  });

  it('renders a single-URL result with its payloads', () => {
    render(<UrlHausDetails result={URL_RESULT} ioc="http://evil.example/a.exe" />);
    expect(screen.getByText('Malware URL')).toBeInTheDocument();
    expect(screen.getByText('online')).toBeInTheDocument();
    expect(screen.getByText('Cryptolaemus1')).toBeInTheDocument();
    expect(screen.getByText('emotet')).toBeInTheDocument();
    expect(screen.getByText('Payloads (1)')).toBeInTheDocument();
    expect(screen.getByText('inv.doc · doc · Heodo')).toBeInTheDocument();
  });
});
