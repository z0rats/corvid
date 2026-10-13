import { render, screen, fireEvent, within } from '@testing-library/react';
import Filters from './Filters';
import { DEFAULT_FILTERS } from '../constants/newsfeedConstants';

const renderFilters = (filters = DEFAULT_FILTERS, setFilters = vi.fn()) => {
  render(
    <Filters
      filters={filters}
      setFilters={setFilters}
      applyFilters={vi.fn()}
      resetFilters={vi.fn()}
      refreshData={vi.fn()}
    />,
  );
  // The filters live in a collapsed accordion; the form fields are still in the DOM.
  return setFilters;
};

describe('Newsfeed filters: minimum reliability', () => {
  it('defaults to no filter, which the API layer strips from the request', () => {
    expect(DEFAULT_FILTERS.min_reliability).toBe('');
  });

  it('offers Any plus grades A-E (F is no threshold) and applies the chosen one', () => {
    const setFilters = renderFilters();

    fireEvent.mouseDown(screen.getAllByRole('combobox', { hidden: true })
      .find((el) => el.getAttribute('aria-labelledby')?.includes('min-reliability-label')));
    const options = within(screen.getByRole('listbox')).getAllByRole('option');
    expect(options.map((o) => o.textContent)).toEqual([
      'Any',
      'A — Completely reliable',
      'B — Usually reliable',
      'C — Fairly reliable',
      'D — Not usually reliable',
      'E — Unreliable',
    ]);

    fireEvent.click(options[2]);
    expect(setFilters).toHaveBeenCalledWith(expect.objectContaining({ min_reliability: 'B' }));
  });

  it('warns that unrated and F-graded feeds are hidden while it is set', () => {
    renderFilters();
    expect(screen.getByText(/hides unrated feeds and F/i)).toBeInTheDocument();
  });
});
