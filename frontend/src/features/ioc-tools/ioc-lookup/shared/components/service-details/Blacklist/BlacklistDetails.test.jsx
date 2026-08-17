import React from 'react';
import { render, screen } from '@testing-library/react';
import BlacklistDetails from './BlacklistDetails';

// Regression test for a bug found after the OpenSanctions source was added: this component
// expected `result.data`, but useServiceFetcher/ServiceResultRow pass the already-unwrapped
// check_blacklist() payload as `result` directly (see FfraudIpDetails.jsx for the same flat
// shape done correctly) - so a real match always rendered "No details available" instead of
// the matched source's card.
describe('BlacklistDetails', () => {
  it('shows no-details message when result is missing', () => {
    render(<BlacklistDetails result={null} />);
    expect(screen.getByText(/unavailable or still loading/i)).toBeInTheDocument();
  });

  it('shows the no-match card for an unlisted address', () => {
    render(<BlacklistDetails result={{ matched: false, sources: [] }} />);
    expect(screen.getByText(/no match/i)).toBeInTheDocument();
  });

  it('renders the OFAC card for a real (flat, unwrapped) OFAC match', () => {
    render(<BlacklistDetails result={{
      matched: true,
      sources: ['OFAC'],
      ofac: { entity_name: 'Roman SEMENOV', program: 'DPRK3', chain: 'ETH', remarks: null },
      scamsniffer: null,
      opensanctions: null,
    }} />);
    expect(screen.getByText('OFAC Sanctioned')).toBeInTheDocument();
    expect(screen.getByText('Roman SEMENOV')).toBeInTheDocument();
  });

  it('renders the OpenSanctions card, holder, and source link for a real match', () => {
    render(<BlacklistDetails result={{
      matched: true,
      sources: ['OPENSANCTIONS'],
      ofac: null,
      scamsniffer: null,
      opensanctions: {
        chain: null, topics: 'crime.terror', holder_name: 'NOBITEX', dataset: 'il_mod_crypto',
        profile_url: 'https://www.opensanctions.org/entities/il-nbctf-abc123/',
      },
    }} />);
    expect(screen.getByText('OpenSanctions Match')).toBeInTheDocument();
    expect(screen.getByText('crime.terror')).toBeInTheDocument();
    expect(screen.getByText('NOBITEX')).toBeInTheDocument();
    expect(screen.getByText('il_mod_crypto')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /view entity on opensanctions/i });
    expect(link).toHaveAttribute('href', 'https://www.opensanctions.org/entities/il-nbctf-abc123/');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('omits the source link when profile_url is unavailable', () => {
    render(<BlacklistDetails result={{
      matched: true,
      sources: ['OPENSANCTIONS'],
      ofac: null,
      scamsniffer: null,
      opensanctions: { chain: null, topics: 'crime.terror', holder_name: null, dataset: 'il_mod_crypto', profile_url: null },
    }} />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
