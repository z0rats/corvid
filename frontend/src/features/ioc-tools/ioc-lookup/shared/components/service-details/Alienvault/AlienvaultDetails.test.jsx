import React from 'react';
import { render, screen } from '@testing-library/react';
import AlienvaultDetails from './AlienvaultDetails';

// GeneralInfoCard/PulseInfoCard/MalwareSamplesCard/FileAnalysisCard each have their
// own dedicated tests; this covers the orchestrator's branching for which cards mount.
describe('AlienvaultDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<AlienvaultDetails result={null} />);
    expect(
      screen.getByText('Detailed information for AlienVault OTX is unavailable or still loading.')
    ).toBeInTheDocument();
  });

  it('shows the unavailable message when the result carries an error', () => {
    render(<AlienvaultDetails result={{ error: true }} />);
    expect(
      screen.getByText('Detailed information for AlienVault OTX is unavailable or still loading.')
    ).toBeInTheDocument();
  });

  it('renders only the general info card for a minimal result', () => {
    render(<AlienvaultDetails result={{ indicator: 'evil.example' }} />);

    expect(screen.getByText('General Information')).toBeInTheDocument();
    expect(screen.queryByText('Pulse Information')).not.toBeInTheDocument();
    expect(screen.queryByText(/^Malware Samples/)).not.toBeInTheDocument();
    expect(screen.queryByText('File Analysis')).not.toBeInTheDocument();
  });

  it('mounts the pulse card when pulse_info is present', () => {
    render(<AlienvaultDetails result={{ indicator: 'evil.example', pulse_info: { count: 2 } }} />);
    expect(screen.getByText('Pulse Information')).toBeInTheDocument();
  });

  it('mounts the malware samples card when section_malware has data', () => {
    render(
      <AlienvaultDetails
        result={{
          indicator: 'evil.example',
          section_malware: { data: [{ hash: 'deadbeef' }] },
        }}
      />
    );
    expect(screen.getByText('Malware Samples (1)')).toBeInTheDocument();
  });

  it('mounts the file analysis card only for a file-type result', () => {
    render(
      <AlienvaultDetails
        result={{
          indicator: 'deadbeef',
          type: 'file',
          section_analysis: { analysis: {} },
        }}
      />
    );
    expect(screen.getByText('File Analysis')).toBeInTheDocument();
  });

  it('does not mount the file analysis card for a non-file type even with section_analysis', () => {
    render(
      <AlienvaultDetails
        result={{
          indicator: 'evil.example',
          type: 'domain',
          section_analysis: { analysis: {} },
        }}
      />
    );
    expect(screen.queryByText('File Analysis')).not.toBeInTheDocument();
  });
});
