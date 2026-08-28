import React from 'react';
import { render, screen } from '@testing-library/react';
import ThreatClassification from './ThreatClassification';

describe('ThreatClassification', () => {
  it('renders the suggested label, categories, and names', () => {
    render(
      <ThreatClassification
        result={{
          data: {
            attributes: {
              popular_threat_classification: {
                suggested_threat_label: 'trojan.emotet/generic',
                popular_threat_category: [{ value: 'trojan', count: 40 }],
                popular_threat_name: [{ value: 'emotet', count: 35 }],
              },
            },
          },
        }}
      />
    );

    expect(screen.getByText('Popular threat classification')).toBeInTheDocument();
    expect(screen.getByText('trojan.emotet/generic')).toBeInTheDocument();
    expect(screen.getByText('trojan')).toBeInTheDocument();
    expect(screen.getByText('40')).toBeInTheDocument();
    expect(screen.getByText('emotet')).toBeInTheDocument();
    expect(screen.getByText('35')).toBeInTheDocument();
  });
});
