import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Whois from './Whois';

describe('Whois', () => {
  it('renders a short whois record without a toggle button', () => {
    render(<Whois result={{ data: { attributes: { whois: 'Domain Name: EVIL.EXAMPLE' } } }} />);

    expect(screen.getByText('Domain Name: EVIL.EXAMPLE')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('truncates a long whois record behind a Read More toggle', () => {
    const longWhois = 'x'.repeat(300);
    render(<Whois result={{ data: { attributes: { whois: longWhois } } }} />);

    expect(screen.getByText('x'.repeat(200))).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Read More' })).toBeInTheDocument();
  });

  it('expands to the full record when Read More is clicked', async () => {
    const user = userEvent.setup();
    const longWhois = 'x'.repeat(300);
    render(<Whois result={{ data: { attributes: { whois: longWhois } } }} />);

    await user.click(screen.getByRole('button', { name: 'Read More' }));

    expect(screen.getByText(longWhois)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Read Less' })).toBeInTheDocument();
  });
});
