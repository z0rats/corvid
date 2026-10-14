import { act, render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import HistoryTable, { HISTORY_PAGE_SIZE, RUNNING_REFRESH_MS } from './HistoryTable';

const columns = [{ key: 'name', header: 'Name' }];

function renderTable(overrides = {}) {
  const props = {
    columns,
    fetchRows: vi.fn().mockResolvedValue([{ id: 1, name: 'alice' }]),
    onDelete: vi.fn().mockResolvedValue(undefined),
    onRowClick: vi.fn(),
    emptyText: 'nothing yet',
    actionsLabel: 'Actions',
    ...overrides,
  };
  render(<HistoryTable {...props} />);
  return props;
}

describe('HistoryTable', () => {
  it('asks for confirmation before deleting, and only deletes on confirm', async () => {
    const props = renderTable();
    fireEvent.click(await screen.findByRole('button', { name: 'Delete' }));

    expect(props.onDelete).not.toHaveBeenCalled();
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }));

    await waitFor(() => expect(props.onDelete).toHaveBeenCalledWith(1));
    await waitFor(() => expect(screen.queryByText('alice')).not.toBeInTheDocument());
    expect(props.onRowClick).not.toHaveBeenCalled();
  });

  it('keeps the row when the delete is cancelled', async () => {
    const props = renderTable();
    fireEvent.click(await screen.findByRole('button', { name: 'Delete' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Cancel' }));

    expect(props.onDelete).not.toHaveBeenCalled();
    expect(screen.getByText('alice')).toBeInTheDocument();
  });

  it('opens a row exactly once from the view button', async () => {
    const props = renderTable();
    fireEvent.click(await screen.findByRole('button', { name: 'View' }));
    expect(props.onRowClick).toHaveBeenCalledTimes(1);
  });

  it('shows an error instead of the empty state when loading fails', async () => {
    renderTable({ fetchRows: vi.fn().mockRejectedValue(new Error('boom')) });
    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't load history/i);
    expect(screen.queryByText('nothing yet')).not.toBeInTheDocument();
  });
});

describe('HistoryTable — filter, sort, paging, live refresh', () => {
  const people = [
    { id: 1, name: 'charlie', status: 'completed' },
    { id: 2, name: 'alice', status: 'completed' },
    { id: 3, name: 'bob', status: 'completed' },
  ];

  it('requests the first page with skip/limit', async () => {
    const props = renderTable({ fetchRows: vi.fn().mockResolvedValue(people) });
    await screen.findByText('alice');
    expect(props.fetchRows).toHaveBeenCalledWith(0, HISTORY_PAGE_SIZE);
  });

  it('filters loaded rows by any column value', async () => {
    renderTable({ fetchRows: vi.fn().mockResolvedValue(people) });
    fireEvent.change(await screen.findByLabelText('Filter loaded runs'), { target: { value: 'ali' } });

    expect(screen.getByText('alice')).toBeInTheDocument();
    expect(screen.queryByText('bob')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Filter loaded runs'), { target: { value: 'zzz' } });
    expect(screen.getByText('No runs match this filter.')).toBeInTheDocument();
  });

  it('sorts by a column header, toggling direction', async () => {
    renderTable({ fetchRows: vi.fn().mockResolvedValue(people) });
    await screen.findByText('alice');
    const names = () => screen.getAllByRole('row').slice(1).map((row) => within(row).getAllByRole('cell')[0].textContent);

    fireEvent.click(screen.getByText('Name'));
    expect(names()).toEqual(['alice', 'bob', 'charlie']);
    fireEvent.click(screen.getByText('Name'));
    expect(names()).toEqual(['charlie', 'bob', 'alice']);
    fireEvent.click(screen.getByText('Name'));
    expect(names()).toEqual(['charlie', 'alice', 'bob']); // back to server order
  });

  it('offers older runs when a full page came back', async () => {
    const firstPage = Array.from({ length: HISTORY_PAGE_SIZE }, (_, i) => ({ id: i, name: `run${i}` }));
    const fetchRows = vi.fn()
      .mockResolvedValueOnce(firstPage)
      .mockResolvedValueOnce([{ id: 999, name: 'oldest' }]);
    renderTable({ fetchRows });

    fireEvent.click(await screen.findByRole('button', { name: 'Load older runs' }));

    expect(await screen.findByText('oldest')).toBeInTheDocument();
    expect(fetchRows).toHaveBeenLastCalledWith(HISTORY_PAGE_SIZE, HISTORY_PAGE_SIZE);
    expect(screen.queryByRole('button', { name: 'Load older runs' })).not.toBeInTheDocument();
  });

  it('refreshes while a run is still running, and stops once it finishes', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      const fetchRows = vi.fn()
        .mockResolvedValueOnce([{ id: 1, name: 'alice', status: 'running' }])
        .mockResolvedValue([{ id: 1, name: 'alice', status: 'completed' }]);
      renderTable({ fetchRows, columns: [{ key: 'name', header: 'Name' }, { key: 'status', header: 'Status' }] });
      await screen.findByText('running');

      await act(async () => { await vi.advanceTimersByTimeAsync(RUNNING_REFRESH_MS); });
      expect(await screen.findByText('completed')).toBeInTheDocument();

      const calls = fetchRows.mock.calls.length;
      await act(async () => { await vi.advanceTimersByTimeAsync(RUNNING_REFRESH_MS * 2); });
      expect(fetchRows.mock.calls.length).toBe(calls);
    } finally {
      vi.useRealTimers();
    }
  });
});
