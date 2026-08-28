import React from 'react';
import { render, screen } from '@testing-library/react';
import HudsonRockDetails from './HudsonRockDetails';

describe('HudsonRockDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<HudsonRockDetails result={null} />);
    expect(
      screen.getByText('Hudson Rock details are unavailable or the data is incomplete.')
    ).toBeInTheDocument();
  });

  it('shows an error message when success is false', () => {
    render(<HudsonRockDetails result={{ success: false, message: 'rate limited' }} />);
    expect(screen.getByText('Error fetching Hudson Rock details: rate limited')).toBeInTheDocument();
  });

  it('shows a no-exposure message when there are no stealers', () => {
    render(<HudsonRockDetails result={{ stealers: [] }} />);
    expect(screen.getByText('No infostealer exposure found.')).toBeInTheDocument();
  });

  it('renders each stealer infection with its details', () => {
    render(
      <HudsonRockDetails
        result={{
          stealers: [
            {
              date_compromised: '2023-05-01T00:00:00Z',
              computer_name: 'DESKTOP-ABC',
              operating_system: 'Windows 10',
              malware_path: 'C:\\temp\\malware.exe',
              antiviruses: ['Defender'],
              top_logins: ['alice@example.com'],
              total_user_services: 3,
              total_corporate_services: 1,
            },
          ],
        }}
      />
    );

    expect(screen.getByText('1 infostealer infection(s) found')).toBeInTheDocument();
    expect(screen.getByText('DESKTOP-ABC — Windows 10')).toBeInTheDocument();
    expect(screen.getByText('C:\\temp\\malware.exe')).toBeInTheDocument();
    expect(screen.getByText('Defender')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    expect(screen.getByText('3 user service(s)')).toBeInTheDocument();
  });

  it('renders the domain view when result.data is present', () => {
    render(
      <HudsonRockDetails
        result={{
          total: 5,
          employees: 2,
          users: 3,
          third_parties: 1,
          data: {
            employees_urls: [
              { url: 'https://portal.example.com', occurrence: 4 },
              { url: 'https://vpn.example.com', occurrence: 1 },
            ],
          },
        }}
      />
    );

    expect(screen.getByText('5 infected machine(s) linked to this domain')).toBeInTheDocument();
    expect(screen.getByText('https://portal.example.com')).toBeInTheDocument();
    expect(screen.getByText('4 occurrence(s)')).toBeInTheDocument();
  });

  it('shows a no-exposure message for a clean domain', () => {
    render(<HudsonRockDetails result={{ total: 0, data: { employees_urls: [] } }} />);
    expect(screen.getByText('No infostealer exposure found.')).toBeInTheDocument();
  });
});
