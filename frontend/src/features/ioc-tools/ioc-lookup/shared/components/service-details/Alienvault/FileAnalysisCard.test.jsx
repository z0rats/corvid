import React from 'react';
import { render, screen } from '@testing-library/react';
import FileAnalysisCard from './FileAnalysisCard';

describe('FileAnalysisCard', () => {
  it('renders the file type, status, and malware family when present', () => {
    render(
      <FileAnalysisCard
        analysis={{
          analysis_status: 'completed',
          analysis: {
            info: { results: { file_type: 'PE32 executable' } },
            malware: { family: ['Emotet', 'TrickBot'] },
          },
        }}
      />
    );

    expect(screen.getByText('File Analysis')).toBeInTheDocument();
    expect(screen.getByText('PE32 executable')).toBeInTheDocument();
    expect(screen.getByText('completed')).toBeInTheDocument();
    expect(screen.getByText('Emotet, TrickBot')).toBeInTheDocument();
  });

  it('falls back to Unknown status and omits optional fields when data is sparse', () => {
    render(<FileAnalysisCard analysis={{ analysis: {} }} />);

    expect(screen.getByText('Unknown')).toBeInTheDocument();
    expect(screen.queryByText('File Type')).not.toBeInTheDocument();
    expect(screen.queryByText('Malware Family')).not.toBeInTheDocument();
  });
});
