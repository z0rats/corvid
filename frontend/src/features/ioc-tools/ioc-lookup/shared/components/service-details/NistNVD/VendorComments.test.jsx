import React from 'react';
import { render, screen } from '@testing-library/react';
import VendorComments from './VendorComments';

describe('VendorComments', () => {
  it('renders a table row for each vendor comment', () => {
    render(
      <VendorComments
        comments={[
          { organization: 'Acme Corp', comment: 'Patched in 2.0.1', lastModified: '2024-01-05' },
        ]}
      />
    );

    expect(screen.getByText('Vendor Comments')).toBeInTheDocument();
    expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    expect(screen.getByText('Patched in 2.0.1')).toBeInTheDocument();
    expect(screen.getByText('2024-01-05')).toBeInTheDocument();
  });
});
