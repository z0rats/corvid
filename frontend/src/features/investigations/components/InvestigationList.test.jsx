import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router';
import InvestigationList from './InvestigationList';
import { investigationsService } from '../../../core/services/api/investigationsService';

vi.mock('../../../core/services/api/investigationsService', () => ({
  investigationsService: { list: vi.fn(), create: vi.fn(), remove: vi.fn() },
}));

const ROW = { id: 4, name: 'Case A', notes: null, item_count: 3, created_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-02T00:00:00Z' };

function renderList() {
  return render(
    <MemoryRouter initialEntries={['/investigations']}>
      <Routes>
        <Route path="/investigations" element={<InvestigationList />} />
        <Route path="/investigations/:id" element={<div>detail page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => vi.clearAllMocks());

describe('InvestigationList', () => {
  it('shows the empty hint', async () => {
    investigationsService.list.mockResolvedValue([]);
    renderList();
    expect(await screen.findByText(/No investigations yet/)).toBeInTheDocument();
  });

  it('lists investigations and opens one', async () => {
    investigationsService.list.mockResolvedValue([ROW]);
    const user = userEvent.setup();
    renderList();

    const row = (await screen.findByText('Case A')).closest('tr');
    expect(within(row).getByText('3')).toBeInTheDocument();
    await user.click(row);

    expect(screen.getByText('detail page')).toBeInTheDocument();
  });

  it('creates an investigation and navigates to it', async () => {
    investigationsService.list.mockResolvedValue([]);
    investigationsService.create.mockResolvedValue({ id: 9 });
    const user = userEvent.setup();
    renderList();

    await user.type(await screen.findByLabelText('New investigation name'), 'Fresh{Enter}');

    expect(investigationsService.create).toHaveBeenCalledWith('Fresh');
    expect(await screen.findByText('detail page')).toBeInTheDocument();
  });

  it('deletes after confirmation', async () => {
    investigationsService.list.mockResolvedValue([ROW]);
    investigationsService.remove.mockResolvedValue();
    const user = userEvent.setup();
    renderList();

    await user.click(await screen.findByRole('button', { name: 'Delete' }));
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete' }));

    expect(investigationsService.remove).toHaveBeenCalledWith(4);
    expect(screen.queryByText('Case A')).not.toBeInTheDocument();
  });

  it('shows a load error', async () => {
    investigationsService.list.mockRejectedValue(new Error('down'));
    renderList();
    expect(await screen.findByText("Couldn't load investigations.")).toBeInTheDocument();
  });
});
