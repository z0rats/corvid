import React from 'react';
import { render, screen } from '@testing-library/react';
import ConfTable from './ConfTable';

describe('ConfTable', () => {
  it('renders a table row for each CPE match', () => {
    render(
      <ConfTable
        index={0}
        configuration={{
          nodes: [
            {
              cpeMatch: [
                {
                  vulnerable: true,
                  criteria: 'cpe:2.3:a:acme:widget:*:*:*:*:*:*:*:*',
                  versionStartIncluding: '1.0',
                  versionEndExcluding: '2.0',
                  matchCriteriaId: 'ABC-123',
                },
              ],
            },
          ],
        }}
      />
    );

    expect(screen.getByText('cpe:2.3:a:acme:widget:*:*:*:*:*:*:*:*')).toBeInTheDocument();
    expect(screen.getByText('1.0')).toBeInTheDocument();
    expect(screen.getByText('2.0')).toBeInTheDocument();
    expect(screen.getByText('ABC-123')).toBeInTheDocument();
  });
});
