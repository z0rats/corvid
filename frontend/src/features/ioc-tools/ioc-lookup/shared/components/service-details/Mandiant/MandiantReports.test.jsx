import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MandiantReports from './MandiantReports';

describe('MandiantReports', () => {
  it('renders each report with its metadata', () => {
    render(
      <MandiantReports
        reports={[
          {
            report_id: 'RPT-1',
            title: 'Emotet Resurgence',
            publish_date: '2024-01-15T00:00:00Z',
            report_type: 'Threat Report',
            threat_scape: ['Cyber Crime'],
          },
        ]}
        page={1}
        onPageChange={() => {}}
      />
    );

    expect(screen.getByText('Emotet Resurgence')).toBeInTheDocument();
    expect(screen.getByText(/Threat Report/)).toBeInTheDocument();
    expect(screen.getByText('Cyber Crime')).toBeInTheDocument();
    expect(screen.getByText('Report ID: RPT-1')).toBeInTheDocument();
  });

  it('opens the report in a new tab when Open is clicked', async () => {
    const user = userEvent.setup();
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => {});

    render(
      <MandiantReports
        reports={[{ report_id: 'RPT-1', title: 'Emotet Resurgence', publish_date: '2024-01-15' }]}
        page={1}
        onPageChange={() => {}}
      />
    );

    await user.click(screen.getByRole('button', { name: 'Open' }));

    expect(openSpy).toHaveBeenCalledWith(
      'https://advantage.mandiant.com/reports/RPT-1',
      '_blank',
      'noopener,noreferrer'
    );

    openSpy.mockRestore();
  });

  it('paginates when there are more than 10 reports', () => {
    const reports = Array.from({ length: 11 }, (_, i) => ({
      report_id: `RPT-${i}`,
      title: `Report ${i}`,
      publish_date: '2024-01-01',
    }));
    render(<MandiantReports reports={reports} page={1} onPageChange={() => {}} />);

    expect(screen.getByText('Report 0')).toBeInTheDocument();
    expect(screen.queryByText('Report 10')).not.toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });
});
