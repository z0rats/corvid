import React from 'react';
import { render, screen } from '@testing-library/react';
import MandiantIndicators from './MandiantIndicators';

describe('MandiantIndicators', () => {
  it('renders each indicator with its risk score and sources', () => {
    render(
      <MandiantIndicators
        indicators={[
          {
            value: 'evil.example',
            type: 'domain',
            mscore: 75,
            first_seen: '2024-01-01',
            last_seen: '2024-01-10',
            sources: [{ source_name: 'FeedX', category: ['malware'] }],
          },
        ]}
        page={1}
        onPageChange={() => {}}
      />
    );

    expect(screen.getByText('evil.example')).toBeInTheDocument();
    expect(screen.getByText('75')).toBeInTheDocument();
    expect(screen.getByText('Sources:')).toBeInTheDocument();
    expect(screen.getByText('FeedX')).toBeInTheDocument();
    expect(screen.getByText('malware')).toBeInTheDocument();
  });

  it('paginates when there are more than 10 indicators', () => {
    const indicators = Array.from({ length: 11 }, (_, i) => ({
      value: `evil-${i}.example`,
      type: 'domain',
      mscore: 10,
    }));
    render(<MandiantIndicators indicators={indicators} page={1} onPageChange={() => {}} />);

    expect(screen.getByText('evil-0.example')).toBeInTheDocument();
    expect(screen.queryByText('evil-10.example')).not.toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });
});
