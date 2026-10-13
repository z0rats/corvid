import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import FoundProvidersList, { FailedChecksNote } from './FoundProvidersList';

const providers = [
  { provider_name: 'Gmail', emails: ['target@gmail.com'] },
  { provider_name: 'Mail.ru', emails: ['target@mail.ru'] },
];

const renderList = (props) => render(
  <MemoryRouter><FoundProvidersList providers={providers} {...props} /></MemoryRouter>,
);

describe('FoundProvidersList Google profile action', () => {
  it('is offered only for Google addresses and reports the address', () => {
    const onLookupGoogleProfile = vi.fn();
    renderList({ onLookupGoogleProfile });

    const buttons = screen.getAllByRole('button', { name: 'Google profile' });
    expect(buttons).toHaveLength(1);
    fireEvent.click(buttons[0]);
    expect(onLookupGoogleProfile).toHaveBeenCalledWith('target@gmail.com');
  });

  it('is hidden when no handler is given (e.g. history view)', () => {
    renderList();
    expect(screen.queryByRole('button', { name: 'Google profile' })).toBeNull();
  });
});

describe('FoundProvidersList profile details', () => {
  const extra = {
    category: 'shopping',
    url: 'https://etsy.test',
    fields: { name: 'Ann Lee', followers: 3, display_name: 'ann' },
    links: { avatar: 'https://img.evil.test/a.png' },
  };

  it('shows the category, the service link and what the profile exposed', () => {
    renderList({ providers: [{ provider_name: 'Etsy', emails: ['a@b.test'], extra }] });

    expect(screen.getByText('shopping')).toBeTruthy();
    expect(screen.getByRole('link', { name: 'open service' }).getAttribute('href')).toBe('https://etsy.test');
    expect(screen.getByText(/name: Ann Lee · followers: 3 · display name: ann/)).toBeTruthy();
  });

  it('never loads image links the profile owner controls', () => {
    const { container } = renderList({ providers: [{ provider_name: 'Etsy', emails: ['a@b.test'], extra }] });

    expect(container.querySelector('img')).toBeNull();
    expect(container.innerHTML).not.toContain('img.evil.test');
  });

  it('does not make a link out of a non-http(s) service URL', () => {
    renderList({ providers: [{ provider_name: 'X', emails: [], extra: { url: 'javascript:alert(1)' } }] });

    expect(screen.queryByRole('link', { name: 'open service' })).toBeNull();
  });
});

describe('FoundProvidersList for a User Scanner run', () => {
  const hits = [
    { provider_name: 'Etsy', emails: ['target@gmail.com'] },
    { provider_name: 'Patreon', emails: ['target@gmail.com'] },
    { provider_name: 'Vivino', emails: ['target@gmail.com'] },
  ];

  it('offers the searched address\'s actions once, not on every hit', () => {
    renderList({ providers: hits, searchedEmail: 'target@gmail.com', onLookupGoogleProfile: vi.fn() });

    expect(screen.getAllByRole('button', { name: 'Google profile' })).toHaveLength(1);
    expect(screen.getAllByRole('button', { name: /IOC Lookup/ })).toHaveLength(1);
    expect(screen.queryByText('target@gmail.com')).toBeNull();
  });
});

describe('FailedChecksNote', () => {
  it('says failed checks are not "not registered", and stays silent without any', () => {
    const { rerender } = render(<FailedChecksNote count={3} />);
    expect(screen.getByText(/3 check\(s\) failed/)).toBeTruthy();

    rerender(<FailedChecksNote count={0} />);
    expect(screen.queryByText(/failed/)).toBeNull();
  });
});
