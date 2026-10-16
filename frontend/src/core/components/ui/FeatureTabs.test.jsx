import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import FeatureTabs from './FeatureTabs';

const tabs = [
  { label: 'New Search', path: '/username-search/new', icon: null },
  { label: 'History', path: '/username-search/history', icon: null },
];

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <FeatureTabs tabs={tabs} />
    </MemoryRouter>,
  );
}

describe('FeatureTabs', () => {
  it('renders every tab as a link to its path', () => {
    renderAt('/username-search/new');
    expect(screen.getByRole('tab', { name: 'History' })).toHaveAttribute('href', '/username-search/history');
  });

  it('marks the tab a detail route sits under as selected', () => {
    renderAt('/username-search/history/42');
    expect(screen.getByRole('tab', { name: 'History' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: 'New Search' })).toHaveAttribute('aria-selected', 'false');
  });
});
