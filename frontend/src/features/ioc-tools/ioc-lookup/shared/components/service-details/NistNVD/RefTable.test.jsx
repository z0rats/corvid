import React from 'react';
import { render, screen } from '@testing-library/react';
import RefTable from './RefTable';

describe('RefTable', () => {
  it('renders a table row for each reference', () => {
    render(
      <RefTable
        references={[{ url: 'https://example.com/advisory', source: 'cve@mitre.org' }]}
      />
    );

    expect(screen.getByText('https://example.com/advisory')).toBeInTheDocument();
    expect(screen.getByText('cve@mitre.org')).toBeInTheDocument();
  });
});
