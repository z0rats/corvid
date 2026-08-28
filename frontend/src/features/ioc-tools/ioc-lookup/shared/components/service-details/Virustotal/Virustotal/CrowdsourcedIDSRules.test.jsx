import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../../core/config/theme';
import CrowdsourcedIDSRules from './CrowdsourcedIDSRules';

function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

describe('CrowdsourcedIDSRules', () => {
  it('renders a table row for each IDS rule', () => {
    renderWithTheme(
      <CrowdsourcedIDSRules
        result={{
          data: {
            attributes: {
              crowdsourced_ids_results: [
                {
                  rule_id: 'rule-1',
                  rule_category: 'trojan',
                  alert_severity: 'high',
                  rule_msg: 'Suspicious outbound connection',
                  rule_raw: 'alert tcp any any -> any any',
                  rule_url: 'https://rules.example/rule-1',
                  rule_source: 'suricata',
                },
              ],
            },
          },
        }}
      />
    );

    expect(screen.getByText('Crowdsourced IDS rules')).toBeInTheDocument();
    expect(screen.getByText('trojan')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('Suspicious outbound connection')).toBeInTheDocument();
    expect(screen.getByText('suricata')).toBeInTheDocument();
  });
});
