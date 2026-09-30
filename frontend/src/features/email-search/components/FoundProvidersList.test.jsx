import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import FoundProvidersList from './FoundProvidersList';

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
