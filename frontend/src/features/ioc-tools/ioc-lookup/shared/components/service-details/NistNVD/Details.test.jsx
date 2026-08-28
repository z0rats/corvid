import React from 'react';
import { render, screen } from '@testing-library/react';
import Details from './Details';

describe('Details', () => {
  it('renders the CVE metadata and description', () => {
    render(
      <Details
        details={{
          sourceIdentifier: 'cve@mitre.org',
          published: '2024-01-01T00:00:00.000',
          lastModified: '2024-01-10T00:00:00.000',
          vulnStatus: 'Analyzed',
          descriptions: [{ value: 'A remote code execution vulnerability.' }],
        }}
      />
    );

    expect(screen.getByText('Details')).toBeInTheDocument();
    expect(screen.getByText('cve@mitre.org')).toBeInTheDocument();
    expect(screen.getByText('2024-01-01T00:00:00.000')).toBeInTheDocument();
    expect(screen.getByText('Analyzed')).toBeInTheDocument();
    expect(screen.getByText('A remote code execution vulnerability.')).toBeInTheDocument();
  });

  it('renders nothing extra when details is missing', () => {
    render(<Details details={null} />);
    expect(screen.getByText('Details')).toBeInTheDocument();
  });
});
