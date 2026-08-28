import React from 'react';
import { render, screen } from '@testing-library/react';
import CisaKevDetails from './CisaKevDetails';

describe('CisaKevDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<CisaKevDetails result={null} />);
    expect(screen.getByText('CISA KEV details are unavailable.')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<CisaKevDetails result={{ error: true, message: 'timeout' }} />);
    expect(screen.getByText('Error fetching CISA KEV details: timeout')).toBeInTheDocument();
  });

  it('shows the not-listed message when the CVE is not in the catalog', () => {
    render(<CisaKevDetails result={{ listed: false }} />);
    expect(
      screen.getByText("Not listed in CISA's Known Exploited Vulnerabilities catalog.")
    ).toBeInTheDocument();
  });

  it('renders the full catalog entry when listed', () => {
    render(
      <CisaKevDetails
        result={{
          listed: true,
          knownRansomwareCampaignUse: 'Known',
          vulnerabilityName: 'Example RCE',
          shortDescription: 'A remote code execution flaw.',
          vendorProject: 'Acme',
          product: 'Widget',
          dateAdded: '2024-01-15',
          dueDate: '2024-02-05',
          requiredAction: 'Apply the vendor patch.',
        }}
      />
    );

    expect(screen.getByText('Listed in CISA KEV')).toBeInTheDocument();
    expect(screen.getByText('Known ransomware use')).toBeInTheDocument();
    expect(screen.getByText('Example RCE')).toBeInTheDocument();
    expect(screen.getByText('A remote code execution flaw.')).toBeInTheDocument();
    expect(screen.getByText('Acme / Widget')).toBeInTheDocument();
    expect(screen.getByText('2024-01-15')).toBeInTheDocument();
    expect(screen.getByText('2024-02-05')).toBeInTheDocument();
    expect(screen.getByText('Apply the vendor patch.')).toBeInTheDocument();
  });

  it('omits the ransomware chip and optional fields when absent', () => {
    render(<CisaKevDetails result={{ listed: true }} />);

    expect(screen.getByText('Listed in CISA KEV')).toBeInTheDocument();
    expect(screen.queryByText('Known ransomware use')).not.toBeInTheDocument();
    expect(screen.queryByText('Vendor / Product')).not.toBeInTheDocument();
  });
});
