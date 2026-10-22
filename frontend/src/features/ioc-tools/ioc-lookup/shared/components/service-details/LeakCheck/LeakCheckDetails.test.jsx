import React from 'react';
import { render, screen, within } from '@testing-library/react';
import LeakCheckDetails from './LeakCheckDetails';

describe('LeakCheckDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<LeakCheckDetails result={null} />);
    expect(screen.getByText('LeakCheck details are unavailable or still loading.')).toBeInTheDocument();
  });

  it('shows a clean card when the address is in no breach', () => {
    render(<LeakCheckDetails result={{ found: 0, fields: [], sources: [] }} />);
    expect(screen.getByText('Not found in any breach')).toBeInTheDocument();
  });

  it('renders every row when name and date repeat', () => {
    const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <LeakCheckDetails
        result={{ found: 2, fields: [], sources: [{ name: 'Stealer Logs', date: '' }, { name: 'Stealer Logs', date: '' }] }}
      />,
    );

    expect(screen.getAllByText('Stealer Logs')).toHaveLength(2);
    expect(errors.mock.calls.some(([message]) => String(message).includes('same key'))).toBe(false);
    errors.mockRestore();
  });

  it('lists exposed fields and sources newest first, undated last', () => {
    render(
      <LeakCheckDetails
        result={{
          found: 3,
          fields: ['username', 'password'],
          sources: [
            { name: 'Old.com', date: '2013-07' },
            { name: 'Stealer Logs', date: '' },
            { name: 'New.com', date: '2024-06' },
          ],
        }}
      />,
    );

    expect(screen.getByText('Found in 3 breach(es)')).toBeInTheDocument();
    expect(screen.getByText('username')).toBeInTheDocument();
    expect(screen.getByText('password')).toBeInTheDocument();

    const rows = within(screen.getByRole('table', { name: 'Breach sources' })).getAllByRole('row').slice(1);
    expect(rows.map((row) => within(row).getAllByRole('cell')[0].textContent)).toEqual([
      'New.com',
      'Old.com',
      'Stealer Logs',
    ]);
    expect(within(rows[2]).getByText('Unknown')).toBeInTheDocument();
  });
});
