import React from 'react';
import { render, screen } from '@testing-library/react';
import ShodanDetails from './ShodanDetails';

describe('ShodanDetails', () => {
  it('shows a loading message when result is missing', () => {
    render(<ShodanDetails result={null} ioc="1.2.3.4" />);
    expect(screen.getByText('Loading Shodan details...')).toBeInTheDocument();
  });

  it('shows an error message when shodan_error is present', () => {
    render(<ShodanDetails result={{ shodan_error: 'API limit reached' }} ioc="1.2.3.4" />);
    expect(
      screen.getByText('Error fetching Shodan details: API limit reached')
    ).toBeInTheDocument();
  });

  it('shows a no-info message for a bare ip_str-only result', () => {
    render(<ShodanDetails result={{ ip_str: '1.2.3.4' }} ioc="1.2.3.4" />);
    expect(
      screen.getByText('No detailed Shodan information found for "1.2.3.4".')
    ).toBeInTheDocument();
  });

  it('renders general info, ports, domains, tags, and vulnerabilities', () => {
    render(
      <ShodanDetails
        result={{
          ip_str: '1.2.3.4',
          city: 'Ashburn',
          region_code: 'VA',
          country_name: 'United States',
          org: 'Amazon',
          asn: 'AS16509',
          isp: 'Amazon.com',
          ports: [22, 80, 443],
          domains: ['evil.example'],
          hostnames: ['host.evil.example'],
          tags: ['cloud'],
          vulns: ['CVE-2021-1234'],
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Shodan IP Report for:')).toBeInTheDocument();
    expect(screen.getByText('Ashburn, VA, United States')).toBeInTheDocument();
    expect(screen.getByText('Amazon (AS16509)')).toBeInTheDocument();
    expect(screen.getByText('Open Ports (3)')).toBeInTheDocument();
    expect(screen.getByText('22')).toBeInTheDocument();
    expect(screen.getByText('Domains & Hostnames')).toBeInTheDocument();
    expect(screen.getByText('evil.example')).toBeInTheDocument();
    expect(screen.getByText('host.evil.example')).toBeInTheDocument();
    // Tags is collapsed by default (unlike ports/domains/vulns above), so its
    // chip content isn't in the DOM until expanded - only the section title is.
    expect(screen.getByText('Tags (1)')).toBeInTheDocument();
    expect(screen.getByText('Vulnerabilities (1)')).toBeInTheDocument();
    expect(screen.getByText('CVE-2021-1234')).toBeInTheDocument();
  });

  it('renders service banner data under Service Banners', () => {
    render(
      <ShodanDetails
        result={{
          ip_str: '1.2.3.4',
          data: [{ port: 80, transport: 'tcp', product: 'nginx' }],
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Service Banners / Detailed Data (1)')).toBeInTheDocument();
  });
});
