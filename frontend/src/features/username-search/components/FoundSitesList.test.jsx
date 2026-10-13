import { render, screen } from '@testing-library/react';
import FoundSitesList from './FoundSitesList';

const sites = [
  { site_name: 'Reddit', url_user: 'https://reddit.com/u/a', extra: { confidence: 'candidate' } },
  { site_name: 'Twitter', url_user: 'https://twitter.com/a', extra: { confidence: 'confirmed' } },
];

describe('FoundSitesList confidence', () => {
  it('shows a chip per rated hit, best-rated first, with the triage caveat', () => {
    render(<FoundSitesList sites={sites} />);

    const items = screen.getAllByRole('listitem').map((li) => li.textContent);
    expect(items[0]).toContain('Twitter');
    expect(items[0]).toContain('Confirmed');
    expect(items[1]).toContain('Candidate');
    expect(screen.getByText(/not proof of the same person/i)).toBeInTheDocument();
  });

  it('shows neither chips nor the caveat for an unrated (plain scan) list', () => {
    render(<FoundSitesList sites={[{ site_name: 'Reddit', url_user: 'https://reddit.com/u/a' }]} />);

    expect(screen.queryByText(/confirmed|likely|candidate|conflicting/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/not proof/i)).not.toBeInTheDocument();
  });
});
