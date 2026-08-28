import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../core/config/theme';
import NistNvdDetails from './NistNvdDetails';

// Details/CvssMetrics/ConfTable/RefTable/VendorComments/Weaknesses/Circle each have
// their own dedicated tests; this covers the orchestrator's branching for which
// optional sections mount, and which CVSS metric version is picked as primary.
function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

function cve(overrides = {}) {
  return {
    sourceIdentifier: 'cve@mitre.org',
    descriptions: [{ value: 'A test vulnerability.' }],
    ...overrides,
  };
}

describe('NistNvdDetails', () => {
  it('shows a loading message when result is missing', () => {
    renderWithTheme(<NistNvdDetails result={null} ioc="CVE-2024-0001" />);
    expect(screen.getByText('Loading NIST NVD details...')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    renderWithTheme(
      <NistNvdDetails result={{ error: true, message: 'timeout' }} ioc="CVE-2024-0001" />
    );
    expect(screen.getByText('Error fetching NIST NVD details: timeout')).toBeInTheDocument();
  });

  it('shows a not-found message when totalResults is zero', () => {
    renderWithTheme(
      <NistNvdDetails result={{ totalResults: 0, vulnerabilities: [] }} ioc="CVE-2024-0001" />
    );
    expect(
      screen.getByText('CVE ID: CVE-2024-0001 was not found in the NIST NVD.')
    ).toBeInTheDocument();
  });

  it('shows a no-info message when vulnerabilities is empty but totalResults is unset', () => {
    renderWithTheme(<NistNvdDetails result={{ vulnerabilities: [] }} ioc="CVE-2024-0001" />);
    expect(
      screen.getByText('No detailed vulnerability information found for CVE ID: CVE-2024-0001.')
    ).toBeInTheDocument();
  });

  it('renders the details card alone for a CVE with no CVSS/weaknesses/references', () => {
    renderWithTheme(
      <NistNvdDetails
        result={{ vulnerabilities: [{ cve: cve() }] }}
        ioc="CVE-2024-0001"
      />
    );

    expect(screen.getByText('Details')).toBeInTheDocument();
    expect(screen.queryByText('CVSS 3.1 metrics')).not.toBeInTheDocument();
    expect(screen.queryByText('Weaknesses')).not.toBeInTheDocument();
    expect(screen.queryByText('Affected Configurations (CPEs)')).not.toBeInTheDocument();
  });

  it('picks the v3.1 CVSS metric when available', () => {
    renderWithTheme(
      <NistNvdDetails
        result={{
          vulnerabilities: [
            {
              cve: cve({
                metrics: {
                  cvssMetricV31: [
                    { source: 'nvd@nist.gov', type: 'Primary', exploitabilityScore: 3.9, impactScore: 5.9, cvssData: { vectorString: 'v3.1-vector', baseScore: 7.5, baseSeverity: 'HIGH' } },
                  ],
                  cvssMetricV2: [
                    { source: 'nvd@nist.gov', type: 'Primary', exploitabilityScore: 10, impactScore: 10, cvssData: { vectorString: 'v2-vector', baseScore: 10, baseSeverity: 'HIGH' } },
                  ],
                },
              }),
            },
          ],
        }}
        ioc="CVE-2024-0001"
      />
    );

    expect(screen.getByText('v3.1-vector')).toBeInTheDocument();
    expect(screen.queryByText('v2-vector')).not.toBeInTheDocument();
  });

  it('mounts weaknesses, references, vendor comments, and configurations when present', () => {
    renderWithTheme(
      <NistNvdDetails
        result={{
          vulnerabilities: [
            {
              cve: cve({
                weaknesses: [{ description: [{ value: 'CWE-79' }], type: 'Primary', source: 'nvd@nist.gov' }],
                references: [{ url: 'https://example.com/ref', source: 'cve@mitre.org' }],
                vendorComments: [{ organization: 'Acme', comment: 'Fixed', lastModified: '2024-01-01' }],
                configurations: [{ nodes: [{ operator: 'OR', cpeMatch: [{ vulnerable: true, criteria: 'cpe:2.3:a:acme:widget' }] }] }],
              }),
            },
          ],
        }}
        ioc="CVE-2024-0001"
      />
    );

    expect(screen.getByText('CWE-79')).toBeInTheDocument();
    expect(screen.getByText('References')).toBeInTheDocument();
    expect(screen.getByText('https://example.com/ref')).toBeInTheDocument();
    expect(screen.getByText('Vendor Comments')).toBeInTheDocument();
    expect(screen.getByText('Acme')).toBeInTheDocument();
    expect(screen.getByText('Affected Configurations (CPEs)')).toBeInTheDocument();
    expect(screen.getByText('Configuration #1 (Operator: OR)')).toBeInTheDocument();
    expect(screen.getByText('cpe:2.3:a:acme:widget')).toBeInTheDocument();
  });
});
