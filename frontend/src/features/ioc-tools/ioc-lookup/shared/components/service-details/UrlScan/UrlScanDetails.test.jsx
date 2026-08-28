import React from 'react';
import { render, screen } from '@testing-library/react';
import UrlScanDetails from './UrlScanDetails';

function makeScan(overrides = {}) {
  return {
    _id: 's1',
    screenshot: 'https://urlscan.example/screenshot/s1.png',
    result: 'https://urlscan.io/result/s1',
    task: {
      apexDomain: 'evil.example',
      domain: 'sub.evil.example',
      url: 'https://sub.evil.example/phish',
      time: '2024-01-15T12:00:00Z',
      visibility: 'public',
      tags: ['phishing'],
    },
    page: {
      ip: '1.2.3.4',
      url: 'https://sub.evil.example/phish',
      title: 'Fake Login Page',
      country: 'US',
      asn: 'AS1234',
      asnname: 'Example Networks',
      server: 'nginx',
      status: '200',
      mimeType: 'text/html',
    },
    ...overrides,
  };
}

describe('UrlScanDetails', () => {
  it('shows a no-info message when there are no scans', () => {
    render(<UrlScanDetails result={{ results: [] }} />);
    expect(
      screen.getByText('No urlscan.io information was found for this indicator.')
    ).toBeInTheDocument();
  });

  it('shows a no-info message when result is missing', () => {
    render(<UrlScanDetails result={null} />);
    expect(
      screen.getByText('No urlscan.io information was found for this indicator.')
    ).toBeInTheDocument();
  });

  it('renders summary stats and scan details', () => {
    render(<UrlScanDetails result={{ total: 1, results: [makeScan()] }} />);

    expect(screen.getByText('Total Scans')).toBeInTheDocument();
    expect(screen.getByText('Unique Apex Domains')).toBeInTheDocument();
    expect(screen.getByText('Scan Results (1)')).toBeInTheDocument();
    expect(screen.getByText('sub.evil.example')).toBeInTheDocument();
    expect(screen.getByText('phishing')).toBeInTheDocument();
    expect(screen.getByText('Fake Login Page')).toBeInTheDocument();
    expect(screen.getByText('1.2.3.4')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /view full report/i });
    expect(link).toHaveAttribute('href', 'https://urlscan.io/result/s1');
  });

  it('paginates when there are more than 5 scans', () => {
    const scans = Array.from({ length: 7 }, (_, i) =>
      makeScan({ _id: `s${i}`, page: { ...makeScan().page, title: `Page ${i}` } })
    );
    render(<UrlScanDetails result={{ total: 7, results: scans }} />);

    expect(screen.getByText('Page 0')).toBeInTheDocument();
    expect(screen.queryByText('Page 5')).not.toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });
});
