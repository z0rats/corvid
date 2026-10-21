import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ResultsView from './ResultsView';

// Shaped like backend git_recon_schemas.GitReconResult: missing values arrive as "", not null.
const CLONE_RESULT = {
  stats: { repos: 2, commits: 57, persons: 2 },
  repos: [{ url: 'https://github.com/acme/tool', cloned: true }],
  persons: [
    {
      key: 'alice',
      name: 'Alice Doe',
      email: 'alice@example.com',
      is_noreply: false,
      as_author: 40,
      as_committer: 3,
      github_login: 'alicedoe',
      aliases: [{ name: 'adoe', email: '1234+adoe@users.noreply.github.com', is_noreply: true }],
      mentions: [{ repo_url: 'https://github.com/acme/tool', sample_commit: 'abc123', as_author: 5, as_committer: 2 }],
    },
    {
      key: 'bot',
      name: '',
      email: '41898282+bot@users.noreply.github.com',
      is_noreply: true,
      as_author: 0,
      as_committer: 14,
      github_login: null,
      aliases: [],
      mentions: [],
    },
  ],
  shared_name_groups: [{ name: 'Alice Doe', emails: ['alice@example.com', 'alice@corp.example'] }],
  same_person_clusters: [{ names: ['Alice Doe', 'adoe'], emails: ['alice@example.com', 'a@x.example'] }],
  gpg_keys: [],
  commit_hits: [],
  notes: [],
};

const SEARCH_RESULT = {
  stats: { repos: 0, commits: 0, persons: 0 },
  repos: [],
  persons: [],
  shared_name_groups: [],
  same_person_clusters: [],
  gpg_keys: [
    { email: 'alice@example.com', verified: true, key_id: 'ABCDEF12', created_at: '2021-01-01T00:00:00Z', source: 'gpg_keys' },
    { email: 'old@example.com', verified: false, key_id: '', created_at: '', source: 'gpg_keys' },
  ],
  commit_hits: [
    { name: 'Alice Doe', email: 'alice@example.com', role: 'author', repo: 'acme/tool', sha: 'deadbeef', date: '2024-03-05T10:00:00Z' },
    { name: '', email: 'ghost@example.com', role: 'committer', repo: 'acme/other', sha: '', date: '' },
    { name: 'Nobody', email: 'n@example.com', role: 'author', repo: '', sha: '', date: '' },
  ],
  notes: ['GitHub token not set - search limited to 10 requests/minute.'],
};

const rowFor = (text) => screen.getByText(text).closest('tr');

describe('ResultsView', () => {
  it('renders nothing without a result', () => {
    const { container } = render(<ResultsView result={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('says so when a scan found nothing at all', () => {
    render(<ResultsView result={{ ...SEARCH_RESULT, gpg_keys: [], commit_hits: [], notes: [] }} />);
    expect(screen.getByText('No results found for this target.')).toBeInTheDocument();
  });

  it('summarises a clone scan and lists each identity with its aliases and activity', () => {
    render(<ResultsView result={CLONE_RESULT} />);

    expect(screen.getByText('2 repos')).toBeInTheDocument();
    expect(screen.getByText('57 commits')).toBeInTheDocument();
    expect(screen.getByText('Identities (2)')).toBeInTheDocument();

    const alice = screen.getByRole('link', { name: '@alicedoe' }).closest('tr');
    expect(within(alice).getByText(/adoe <1234\+adoe@users\.noreply\.github\.com>/)).toHaveTextContent('(noreply)');
    expect(within(alice).getByRole('link', { name: '@alicedoe' })).toHaveAttribute('href', 'https://github.com/alicedoe');
    const repoLink = within(alice).getByRole('link', { name: 'acme/tool' });
    expect(repoLink).toHaveAttribute('href', 'https://github.com/acme/tool/commit/abc123');
    expect(within(alice).getByText(/7 commits/)).toBeInTheDocument();
    expect(within(alice).getByText('40')).toBeInTheDocument();
  });

  it('marks noreply addresses and handles an identity without a name or GitHub login', () => {
    render(<ResultsView result={CLONE_RESULT} />);

    const bot = rowFor('41898282+bot@users.noreply.github.com');
    expect(within(bot).getByText('?')).toBeInTheDocument();
    expect(within(bot).getByText('noreply')).toBeInTheDocument();
    expect(within(bot).getByText('-')).toBeInTheDocument();
    expect(within(bot).queryByRole('link')).not.toBeInTheDocument();
  });

  it('flags shared names and same-person clusters', () => {
    render(<ResultsView result={CLONE_RESULT} />);

    expect(screen.getByText('Correlation')).toBeInTheDocument();
    expect(screen.getByText(/alice@example\.com, alice@corp\.example/)).toBeInTheDocument();
    expect(screen.getByText(/Alice Doe ≡ adoe/)).toBeInTheDocument();
  });

  it('shows notes, PGP keys and commit-search hits for a search scan without clone stats', () => {
    render(<ResultsView result={SEARCH_RESULT} />);

    expect(screen.getByText(/search limited to 10 requests\/minute/)).toBeInTheDocument();
    expect(screen.queryByText(/repos$/)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Identities/)).not.toBeInTheDocument();

    const verified = rowFor('ABCDEF12');
    expect(within(verified).getByText('verified')).toBeInTheDocument();
    const unverified = rowFor('old@example.com');
    expect(within(unverified).getByText('unverified')).toBeInTheDocument();
    expect(within(unverified).getByText('?')).toBeInTheDocument();

    expect(within(rowFor('Alice Doe')).getByRole('link', { name: 'acme/tool' }))
      .toHaveAttribute('href', 'https://github.com/acme/tool/commit/deadbeef');
    const ghost = rowFor('ghost@example.com');
    expect(within(ghost).getByRole('link', { name: 'acme/other' })).toHaveAttribute('href', 'https://github.com/acme/other');
    expect(within(ghost).getByText('?')).toBeInTheDocument();
    const nobody = rowFor('Nobody');
    expect(within(nobody).queryByRole('link')).not.toBeInTheDocument();
    expect(within(nobody).getAllByText('-')).toHaveLength(2);
  });

  it('shows only the notes when a search scan found no emails', () => {
    render(<ResultsView result={{ ...SEARCH_RESULT, gpg_keys: [], commit_hits: [], notes: ['No emails found via /gpg_keys or /search/commits.'] }} />);
    expect(screen.getByRole('alert')).toHaveTextContent('No emails found');
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });
});
