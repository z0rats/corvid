import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import RedditSearch from './RedditSearch';
import { useRedditSearch } from './hooks/useRedditSearch';

vi.mock('./hooks/useRedditSearch');

const emptyTab = () => ({ items: [], sources: [], page: 1, hasMore: false, loading: false, error: null });

// RedditSearch owns its own nested <Routes> (index/new/history), same as it's mounted in the
// real app (routes.jsx's `path="reddit-search/*"`) — mounting it bare under MemoryRouter without
// this wrapping route fails to match anything, since its own `index` route only matches an empty
// relative path once nested under a `/*` parent.
function renderRedditSearch(initialEntries) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="reddit-search/*" element={<RedditSearch />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('RedditSearch — cross-feature prefill (command palette pivot)', () => {
  let search;

  beforeEach(() => {
    search = vi.fn();
    useRedditSearch.mockReturnValue({
      username: '', searchId: null, posts: emptyTab(), comments: emptyTab(),
      search, goNext: vi.fn(), goPrev: vi.fn(),
    });
  });

  afterEach(() => vi.clearAllMocks());

  it('preserves ?q= through the index -> new redirect and prefills the username field', () => {
    renderRedditSearch(['/reddit-search?q=john_doe']);

    expect(screen.getByLabelText(/username/i).value).toBe('john_doe');
  });

  it('auto-runs the search with the prefilled value', () => {
    renderRedditSearch(['/reddit-search?q=john_doe']);

    expect(search).toHaveBeenCalledWith('john_doe');
  });

  it('leaves the field empty and does not search with no prefill value', () => {
    renderRedditSearch(['/reddit-search']);

    expect(screen.getByLabelText(/username/i).value).toBe('');
    expect(search).not.toHaveBeenCalled();
  });
});
