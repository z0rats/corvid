import React from 'react';
import { render, screen } from '@testing-library/react';
import Filenames from './Filenames';

describe('Filenames', () => {
  it('lists each known filename', () => {
    render(
      <Filenames
        result={{ data: { attributes: { names: ['invoice.exe', 'invoice_final.exe'] } } }}
      />
    );

    expect(screen.getByText('Filenames')).toBeInTheDocument();
    expect(screen.getByText('invoice.exe')).toBeInTheDocument();
    expect(screen.getByText('invoice_final.exe')).toBeInTheDocument();
  });

  it('renders an empty list without crashing when there are no names', () => {
    render(<Filenames result={{ data: { attributes: { names: [] } } }} />);
    expect(screen.getByText('Filenames')).toBeInTheDocument();
  });
});
