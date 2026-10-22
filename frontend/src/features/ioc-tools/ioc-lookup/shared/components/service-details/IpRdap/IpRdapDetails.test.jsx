import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router';
import IpRdapDetails from './IpRdapDetails';

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{`${location.pathname}${location.search}`}</div>;
}

const renderDetails = (result) =>
  render(
    <MemoryRouter initialEntries={['/ioc-tools/lookup']}>
      <Routes>
        <Route path="*" element={<><IpRdapDetails result={result} /><LocationProbe /></>} />
      </Routes>
    </MemoryRouter>,
  );

const RIPE = {
  ip: '193.0.6.139',
  reserved: false,
  found: true,
  handle: '193.0.0.0 - 193.0.7.255',
  name: 'RIPE-NCC',
  type: 'ASSIGNED PA',
  start_address: '193.0.0.0',
  end_address: '193.0.7.255',
  cidrs: ['193.0.0.0/21'],
  country: 'NL',
  registrant: 'RIPE Network Coordination Centre',
  abuse_emails: ['abuse@ripe.net'],
  registration: '2003-03-17T12:15:57Z',
  last_changed: null,
  registry: 'RIPE NCC',
  registry_server: 'rdap.db.ripe.net',
};

describe('IpRdapDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    renderDetails(null);
    expect(screen.getByText('IP RDAP details are unavailable or still loading.')).toBeInTheDocument();
  });

  it('distinguishes a reserved address from unallocated space', () => {
    const { unmount } = renderDetails({ ...RIPE, reserved: true, found: false });
    expect(screen.getByText('Private or reserved address')).toBeInTheDocument();
    unmount();

    renderDetails({ ...RIPE, found: false });
    expect(screen.getByText('No RDAP record for this address (unallocated space)')).toBeInTheDocument();
  });

  it('shows the netblock, registry and registrant', () => {
    renderDetails(RIPE);
    expect(screen.getByText('RIPE-NCC · RIPE NCC')).toBeInTheDocument();
    expect(screen.getByText('rdap.db.ripe.net')).toBeInTheDocument();
    expect(screen.getByText('RIPE Network Coordination Centre')).toBeInTheDocument();
    expect(screen.getByText('193.0.0.0/21')).toBeInTheDocument();
    expect(screen.getByText('193.0.0.0 – 193.0.7.255')).toBeInTheDocument();
    expect(screen.queryByText('Last changed')).not.toBeInTheDocument();
  });

  it('falls back to the RDAP server when the registry is unknown', () => {
    renderDetails({ ...RIPE, registry: null, registry_server: 'rdap.example.net' });
    expect(screen.getByText('RIPE-NCC · rdap.example.net')).toBeInTheDocument();
  });

  it('pivots the abuse contact into an IOC lookup', () => {
    renderDetails(RIPE);
    fireEvent.click(screen.getByText('abuse@ripe.net'));
    expect(screen.getByTestId('location')).toHaveTextContent('/ioc-tools/lookup?q=abuse%40ripe.net');
  });
});
