import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import DiscoveredIdentifiers from './DiscoveredIdentifiers';

const sites = [
  {
    site_name: 'GitHub',
    extra: {
      discovered_usernames: [{ value: 'jsmith_alt', type: 'username' }],
      discovered_names: ['John Smith'],
    },
  },
];

const renderIt = (props = {}) => render(
  <MemoryRouter>
    <DiscoveredIdentifiers sites={sites} username="jsmith" onSearchUsername={() => {}} {...props} />
  </MemoryRouter>,
);

describe('DiscoveredIdentifiers', () => {
  it('lets a discovered handle be searched', () => {
    const onSearchUsername = vi.fn();
    renderIt({ onSearchUsername });
    fireEvent.click(screen.getByText('jsmith_alt'));
    expect(onSearchUsername).toHaveBeenCalledWith('jsmith_alt');
  });

  it('shows the name and handle guesses derived from it', () => {
    renderIt();
    expect(screen.getByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('johnsmith')).toBeInTheDocument();
  });

  it('offers email guesses for the searched handle', () => {
    renderIt({ sites: [] });
    expect(screen.getByText('jsmith@gmail.com')).toBeInTheDocument();
  });
});
