import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import DiscoveredIdentifiers from './DiscoveredIdentifiers';

const pivots = {
  usernames: [
    { value: 'jsmith_alt', kind: 'reported', id_type: 'username', searchable: true, site: null, sites: ['GitHub'] },
    { value: 'jsmith_x', kind: 'link', id_type: 'username', searchable: true, site: 'Twitter', sites: ['GitHub'] },
    { value: '76561198000000000', kind: 'reported', id_type: 'steam_id', searchable: false, site: null, sites: ['Steam'] },
  ],
  names: [{ value: 'John Smith', sites: ['GitHub'] }],
  emails: [{ value: 'dev@acme.dev', sites: ['GitHub'] }],
};

const renderIt = (props = {}) => render(
  <MemoryRouter>
    <DiscoveredIdentifiers pivots={pivots} username="jsmith" onSearchUsername={() => {}} {...props} />
  </MemoryRouter>,
);

describe('DiscoveredIdentifiers', () => {
  it('lets a reported handle and a link-derived handle be searched', () => {
    const onSearchUsername = vi.fn();
    renderIt({ onSearchUsername });

    fireEvent.click(screen.getByText('jsmith_alt'));
    fireEvent.click(screen.getByText('jsmith_x'));

    expect(onSearchUsername).toHaveBeenNthCalledWith(1, 'jsmith_alt', { pivotSource: 'reported by GitHub' });
    expect(onSearchUsername).toHaveBeenNthCalledWith(2, 'jsmith_x', { pivotSource: 'link on GitHub' });
  });

  it('offers a one-site check only for a link-derived handle whose site is known', () => {
    const onCheckSite = vi.fn();
    renderIt({ onCheckSite });

    expect(screen.getAllByRole('button', { name: /check on/i })).toHaveLength(1);
    fireEvent.click(screen.getByRole('button', { name: 'Check on Twitter' }));

    expect(onCheckSite).toHaveBeenCalledWith(pivots.usernames[1], { pivotSource: 'link on GitHub' });
  });

  it('also offers the check for a handle that was both reported and linked, since its site is known', () => {
    const both = { ...pivots.usernames[0], site: 'GitHub' };
    renderIt({ onCheckSite: vi.fn(), pivots: { ...pivots, usernames: [both] } });

    expect(screen.getByRole('button', { name: 'Check on GitHub' })).toBeInTheDocument();
  });

  it('caps the provenance label at the 200 characters the backend accepts', () => {
    const onSearchUsername = vi.fn();
    const sites = Array.from({ length: 60 }, (_, i) => `Site${i}`);
    renderIt({ onSearchUsername, pivots: { ...pivots, usernames: [{ ...pivots.usernames[0], sites }] } });

    fireEvent.click(screen.getByText('jsmith_alt'));

    expect(onSearchUsername.mock.calls[0][1].pivotSource).toHaveLength(200);
  });

  it('shows no site-check button when the parent cannot run one', () => {
    renderIt();
    expect(screen.queryByRole('button', { name: /check on/i })).not.toBeInTheDocument();
  });

  it('shows platform account IDs as plain labels that cannot start a username search', () => {
    const onSearchUsername = vi.fn();
    renderIt({ onSearchUsername });

    fireEvent.click(screen.getByText('76561198000000000 (steam_id)'));

    expect(onSearchUsername).not.toHaveBeenCalled();
  });

  it('shows the name and handle guesses derived from it', () => {
    renderIt();
    expect(screen.getByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('johnsmith')).toBeInTheDocument();
  });

  it('lists emails the profiles published, apart from the guesses', () => {
    renderIt();
    expect(screen.getByText('dev@acme.dev')).toBeInTheDocument();
    expect(screen.getByText('jsmith@gmail.com')).toBeInTheDocument();
  });

  it('still offers email guesses when no pivots came back (null while loading or on older runs)', () => {
    renderIt({ pivots: null });
    expect(screen.getByText('jsmith@gmail.com')).toBeInTheDocument();
  });
});
