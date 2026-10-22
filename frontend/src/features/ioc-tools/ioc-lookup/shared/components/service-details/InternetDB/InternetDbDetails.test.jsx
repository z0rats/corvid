import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router';
import InternetDbDetails from './InternetDbDetails';

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{`${location.pathname}${location.search}`}</div>;
}

const renderDetails = (result) =>
  render(
    <MemoryRouter initialEntries={['/ioc-tools/lookup']}>
      <Routes>
        <Route path="*" element={<><InternetDbDetails result={result} /><LocationProbe /></>} />
      </Routes>
    </MemoryRouter>,
  );

describe('InternetDbDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    renderDetails(null);
    expect(screen.getByText('Shodan InternetDB details are unavailable or still loading.')).toBeInTheDocument();
  });

  it('shows a no-data card, not an error, when Shodan has nothing on the IP', () => {
    renderDetails({ ip: '203.0.113.7', ports: [], hostnames: [], tags: [], cpes: [], vulns: [], no_data: true });
    expect(screen.getByText('Shodan has no data on this IP')).toBeInTheDocument();
  });

  it('lists ports, hostnames, tags, CPEs and CVEs', () => {
    renderDetails({
      ip: '1.1.1.1',
      ports: [53, 443],
      hostnames: ['one.one.one.one'],
      tags: ['cdn'],
      cpes: ['cpe:/a:cloudflare:cloudflare'],
      vulns: ['CVE-2023-0001'],
      no_data: false,
    });

    expect(screen.getByText('2 open port(s), 1 known CVE(s)')).toBeInTheDocument();
    for (const text of ['53', '443', 'one.one.one.one', 'cdn', 'cpe:/a:cloudflare:cloudflare', 'CVE-2023-0001']) {
      expect(screen.getByText(text)).toBeInTheDocument();
    }
  });

  it('pivots a clicked CVE into the IOC lookup', () => {
    renderDetails({ ip: '1.1.1.1', ports: [], hostnames: [], tags: [], cpes: [], vulns: ['CVE-2023-0001'], no_data: false });

    fireEvent.click(screen.getByText('CVE-2023-0001'));

    expect(screen.getByTestId('location')).toHaveTextContent('/ioc-tools/lookup?q=CVE-2023-0001');
  });
});
