import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HaveibeenpwndDetails from './HaveibeenpwndDetails';

describe('HaveibeenpwndDetails', () => {
  it('shows a loading message when result is missing', () => {
    render(<HaveibeenpwndDetails result={null} ioc="alice@example.com" />);
    expect(screen.getByText('Loading Have I Been Pwned details...')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(
      <HaveibeenpwndDetails result={{ error: true, message: 'timeout' }} ioc="alice@example.com" />
    );
    expect(screen.getByText('Error fetching HIBP details: timeout')).toBeInTheDocument();
  });

  it('shows a no-results message when there are no breaches or pastes', () => {
    render(<HaveibeenpwndDetails result={{}} ioc="alice@example.com" />);
    expect(
      screen.getByText('No breaches or pastes found for "alice@example.com" according to Have I Been Pwned.')
    ).toBeInTheDocument();
  });

  it('renders only the breaches card when there are no pastes', () => {
    render(
      <HaveibeenpwndDetails
        result={{
          breachedaccount: [
            { Name: 'Adobe', Domain: 'adobe.com', IsVerified: true },
          ],
        }}
        ioc="alice@example.com"
      />
    );

    expect(screen.getByText('Breaches (1)')).toBeInTheDocument();
    expect(screen.getByText('Adobe')).toBeInTheDocument();
    expect(screen.getByText('(Verified)')).toBeInTheDocument();
    expect(screen.queryByText('Pastes')).not.toBeInTheDocument();
    expect(screen.queryByText(/^Pastes \(/)).not.toBeInTheDocument();
  });

  it('renders only the pastes card when there are no breaches', () => {
    render(
      <HaveibeenpwndDetails
        result={{
          pasteaccount: [
            { Id: 'p1', Title: 'Leak dump', Source: 'Pastebin', EmailCount: 500 },
          ],
        }}
        ioc="alice@example.com"
      />
    );

    expect(screen.getByText('Pastes (1)')).toBeInTheDocument();
    expect(screen.getByText('Leak dump')).toBeInTheDocument();
    expect(screen.getByText('Pastebin')).toBeInTheDocument();
    expect(screen.queryByText(/^Breaches \(/)).not.toBeInTheDocument();
  });

  it('renders both cards when breaches and pastes are present', () => {
    render(
      <HaveibeenpwndDetails
        result={{
          breachedaccount: [{ Name: 'Adobe' }],
          pasteaccount: [{ Id: 'p1', Title: 'Leak dump' }],
        }}
        ioc="alice@example.com"
      />
    );

    expect(screen.getByText('Breaches (1)')).toBeInTheDocument();
    expect(screen.getByText('Pastes (1)')).toBeInTheDocument();
  });

  it('filters breaches by the search box', async () => {
    const user = userEvent.setup();
    render(
      <HaveibeenpwndDetails
        result={{ breachedaccount: [{ Name: 'Adobe' }, { Name: 'LinkedIn' }] }}
        ioc="alice@example.com"
      />
    );

    await user.type(screen.getByLabelText('Search Breaches'), 'linked');

    expect(screen.queryByText('Adobe')).not.toBeInTheDocument();
    expect(screen.getByText('LinkedIn')).toBeInTheDocument();
  });

  it('shows a no-matching message when the search filters out everything', async () => {
    const user = userEvent.setup();
    render(
      <HaveibeenpwndDetails result={{ breachedaccount: [{ Name: 'Adobe' }] }} ioc="alice@example.com" />
    );

    await user.type(screen.getByLabelText('Search Breaches'), 'zzz-no-match');

    expect(screen.getByText('No matching breaches found for search term.')).toBeInTheDocument();
  });
});
