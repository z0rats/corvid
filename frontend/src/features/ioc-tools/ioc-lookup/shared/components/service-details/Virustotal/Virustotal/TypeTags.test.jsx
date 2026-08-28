import React from 'react';
import { render, screen } from '@testing-library/react';
import TypeTags from './TypeTags';

describe('TypeTags', () => {
  it('shows None when there are no type tags', () => {
    render(<TypeTags result={{ data: { attributes: { type_tags: [] } } }} />);
    expect(screen.getByText('None')).toBeInTheDocument();
  });

  it('renders a chip for each type tag', () => {
    render(
      <TypeTags result={{ data: { attributes: { type_tags: ['peexe', 'signed'] } } }} />
    );

    expect(screen.getByText('Type tags')).toBeInTheDocument();
    expect(screen.getByText('peexe')).toBeInTheDocument();
    expect(screen.getByText('signed')).toBeInTheDocument();
  });
});
