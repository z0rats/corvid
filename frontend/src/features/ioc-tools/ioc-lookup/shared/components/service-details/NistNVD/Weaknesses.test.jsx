import React from 'react';
import { render, screen } from '@testing-library/react';
import Weaknesses from './Weaknesses';

describe('Weaknesses', () => {
  it('renders a table row for each weakness', () => {
    render(
      <Weaknesses
        weaknesses={[
          { description: [{ value: 'CWE-79 Cross-site Scripting' }], type: 'Primary', source: 'nvd@nist.gov' },
        ]}
      />
    );

    expect(screen.getByText('Weaknesses')).toBeInTheDocument();
    expect(screen.getByText('CWE-79 Cross-site Scripting')).toBeInTheDocument();
    expect(screen.getByText('Primary')).toBeInTheDocument();
    expect(screen.getByText('nvd@nist.gov')).toBeInTheDocument();
  });
});
