import React from 'react';
import { render, screen } from '@testing-library/react';
import IpGeoDetails from './IpGeoDetails';

describe('IpGeoDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<IpGeoDetails result={null} />);
    expect(screen.getByText('IP geolocation details are unavailable or still loading.')).toBeInTheDocument();
  });

  it('says a reserved address was not sent anywhere', () => {
    render(<IpGeoDetails result={{ ip: '10.0.0.1', reserved: true }} />);
    expect(screen.getByText('Private or reserved address')).toBeInTheDocument();
    expect(screen.getByText(/Not sent to any third party/)).toBeInTheDocument();
  });

  it('shows place, ASN, company and coordinates, skipping empty fields', () => {
    render(
      <IpGeoDetails
        result={{
          ip: '1.1.1.1',
          reserved: false,
          country: 'Australia',
          region: 'Queensland',
          city: 'Brisbane',
          lat: -27.46,
          lon: 153.02,
          timezone: null,
          asn: 'AS13335 Cloudflare, Inc.',
          company: 'APNIC Research and Development',
        }}
      />,
    );
    expect(screen.getByText('Brisbane, Queensland, Australia')).toBeInTheDocument();
    expect(screen.getByText('AS13335 Cloudflare, Inc.')).toBeInTheDocument();
    expect(screen.getByText('APNIC Research and Development')).toBeInTheDocument();
    expect(screen.getByText('-27.46, 153.02')).toBeInTheDocument();
    expect(screen.queryByText('Time zone')).not.toBeInTheDocument();
  });
});
