import React from 'react';
import { render, screen } from '@testing-library/react';
import UrlHausDetails from './UrlHausDetails';

// UrlHausDetails is an unimplemented placeholder (see the TODO in the component) - it always
// renders the same static label regardless of props. This just guards against it throwing.
describe('UrlHausDetails', () => {
  it('renders the placeholder label', () => {
    render(<UrlHausDetails result={null} />);
    expect(screen.getByText('UrlHaus')).toBeInTheDocument();
  });
});
