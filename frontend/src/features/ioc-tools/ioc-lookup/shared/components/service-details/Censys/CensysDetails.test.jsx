import React from 'react';
import { render, screen } from '@testing-library/react';
import CensysDetails from './CensysDetails';
import { isWaf, softwareLabel } from '../../../utils/detailFormat';

const CERT = {
  subject_dn: 'CN=cloudflare-dns.com',
  issuer_dn: 'CN=DigiCert Global G2 TLS RSA SHA256 2020 CA1',
  fingerprint_sha256: 'ab'.repeat(32),
  names: ['one.one.one.one'],
};

describe('softwareLabel', () => {
  it('drops a vendor that repeats the product and appends the version', () => {
    expect(softwareLabel({ vendor: 'cloudflare', product: 'cloudflare' })).toBe('cloudflare');
    expect(softwareLabel({ vendor: 'f5', product: 'nginx', version: '1.25' })).toBe('f5 nginx 1.25');
    expect(softwareLabel({ vendor: 'microsoft', product: null })).toBe('microsoft');
  });
});

describe('isWaf', () => {
  it('matches a WAF type tag case-insensitively and tolerates missing types', () => {
    expect(isWaf({ types: ['CDN', 'waf'] })).toBe(true);
    expect(isWaf({ types: ['CDN'] })).toBe(false);
    expect(isWaf({})).toBe(false);
  });
});

describe('CensysDetails', () => {
  it('says a reserved IP was not sent to Censys', () => {
    render(<CensysDetails result={{ kind: 'host', reserved: true, not_found: true, services: [] }} />);
    expect(screen.getByText('Private or reserved address')).toBeInTheDocument();
  });

  it('highlights a WAF and renders duplicate products without dropping one', () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <CensysDetails
        result={{
          kind: 'webproperty',
          not_found: false,
          hostname: 'example.com',
          port: 443,
          software: [
            { vendor: 'cloudflare', product: 'waf', version: null, types: ['WAF'] },
            { vendor: 'nginx', product: 'nginx', version: null, types: [] },
            { vendor: 'nginx', product: 'nginx', version: null, types: [] },
          ],
          cert: null,
        }}
      />,
    );
    expect(screen.getByText('cloudflare waf · WAF')).toBeInTheDocument();
    expect(screen.getAllByText('nginx')).toHaveLength(2);
    expect(errorSpy.mock.calls.flat().map(String).join(' ')).not.toMatch(/same key/);
    errorSpy.mockRestore();
  });

  it('shows the unavailable message when result is missing', () => {
    render(<CensysDetails result={null} />);
    expect(screen.getByText('Censys details are unavailable or still loading.')).toBeInTheDocument();
  });

  it('shows a not-found card, not an error', () => {
    render(<CensysDetails result={{ kind: 'host', not_found: true, services: [], hostnames: [] }} />);
    expect(screen.getByText('Censys has no data on this asset')).toBeInTheDocument();
  });

  it('lists a host\'s services with their certificate subject', () => {
    render(
      <CensysDetails
        result={{
          kind: 'host',
          not_found: false,
          ip: '1.1.1.1',
          service_count: 2,
          services: [
            { port: 53, protocol: 'DNS', transport_protocol: 'udp', scan_time: null, cert: null },
            { port: 443, protocol: 'HTTP', transport_protocol: 'tcp', scan_time: null, cert: CERT },
          ],
          hostnames: ['one.one.one.one'],
          location: { country: 'Australia', city: 'Brisbane' },
          autonomous_system: { asn: 13335, name: 'CLOUDFLARENET', bgp_prefix: '1.1.1.0/24' },
        }}
      />,
    );
    expect(screen.getByText('2 service(s)')).toBeInTheDocument();
    expect(screen.getByText('AS13335 CLOUDFLARENET')).toBeInTheDocument();
    expect(screen.getByText('DNS')).toBeInTheDocument();
    expect(screen.getByText('CN=cloudflare-dns.com')).toBeInTheDocument();
  });

  it('shows a web property\'s software and certificate', () => {
    render(
      <CensysDetails
        result={{
          kind: 'webproperty',
          not_found: false,
          hostname: 'example.com',
          port: 443,
          scan_time: null,
          software: [{ vendor: 'cloudflare', product: 'cloudflare', version: null }],
          cert: CERT,
        }}
      />,
    );
    expect(screen.getByText('example.com:443')).toBeInTheDocument();
    expect(screen.getByText('cloudflare')).toBeInTheDocument();
    expect(screen.getByText('CN=DigiCert Global G2 TLS RSA SHA256 2020 CA1')).toBeInTheDocument();
    expect(screen.getByText('ab'.repeat(32))).toBeInTheDocument();
  });
});
