import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router';
import InvestigationDetail from './InvestigationDetail';
import { investigationsService } from '../../../core/services/api/investigationsService';
import { downloadFromApi } from '../../../core/services/apiDownload';

vi.mock('../../../core/services/api/investigationsService', () => ({
  investigationsService: {
    get: vi.fn(),
    update: vi.fn(),
    updateItem: vi.fn(),
    removeItem: vi.fn(),
    reportRequest: vi.fn((id, format, locale) => ({ path: `/r/${id}`, params: { format, locale } })),
    remove: vi.fn(),
    features: vi.fn(),
    graph: vi.fn(),
  },
}));
vi.mock('../../../core/services/apiDownload', () => ({ downloadFromApi: vi.fn() }));
vi.mock('./EntityGraph', () => ({ default: () => <div>graph tab</div> }));

const ITEMS = [
  { id: 1, feature: 'username_search', run_id: 5, target: 'jdoe', note: null, added_at: '2026-10-01T00:00:00Z', missing: false },
  { id: 2, feature: 'ioc_lookup', run_id: 8, target: '1.2.3.4', note: 'old lookup', added_at: '2026-10-01T00:00:00Z', missing: true },
];
const INVESTIGATION = {
  id: 3, name: 'Case A', notes: 'first', created_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-01T00:00:00Z', items: ITEMS,
};

function renderDetail() {
  return render(
    <MemoryRouter initialEntries={['/investigations/3']}>
      <Routes>
        <Route path="/investigations" element={<div>list page</div>} />
        <Route path="/investigations/:id" element={<InvestigationDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  investigationsService.get.mockResolvedValue(INVESTIGATION);
  investigationsService.features.mockResolvedValue([
    { feature: 'username_search', label: 'Username search' },
    { feature: 'ioc_lookup', label: 'IOC lookup' },
  ]);
});

afterEach(() => vi.clearAllMocks());

describe('InvestigationDetail', () => {
  it('lists runs, linking live ones and marking deleted ones', async () => {
    renderDetail();

    expect(await screen.findByRole('link', { name: 'jdoe' })).toHaveAttribute('href', '/username-search/history/5');
    expect(screen.queryByRole('link', { name: '1.2.3.4' })).not.toBeInTheDocument();
    expect(screen.getByText('Run deleted')).toBeInTheDocument();
    expect(await screen.findByText('Username search')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Runs (2)' })).toBeInTheDocument();
  });

  it('saves edited notes', async () => {
    investigationsService.update.mockResolvedValue({ ...INVESTIGATION, notes: 'first, more' });
    const user = userEvent.setup();
    renderDetail();

    await user.type(await screen.findByLabelText('Notes'), ', more');
    await user.click(screen.getByRole('button', { name: 'Save notes' }));

    expect(investigationsService.update).toHaveBeenCalledWith('3', { notes: 'first, more' });
    expect(screen.queryByRole('button', { name: 'Save notes' })).not.toBeInTheDocument();
  });

  it('saves an item note on Enter', async () => {
    investigationsService.updateItem.mockResolvedValue({ ...ITEMS[0], note: 'same person' });
    const user = userEvent.setup();
    renderDetail();

    const row = (await screen.findByRole('link', { name: 'jdoe' })).closest('tr');
    await user.type(within(row).getByLabelText('Note'), 'same person{Enter}');

    expect(investigationsService.updateItem).toHaveBeenCalledWith('3', 1, 'same person');
  });

  it('removes a run from the investigation', async () => {
    investigationsService.removeItem.mockResolvedValue();
    const user = userEvent.setup();
    renderDetail();

    const row = (await screen.findByRole('link', { name: 'jdoe' })).closest('tr');
    await user.click(within(row).getByRole('button', { name: 'Remove from investigation' }));

    expect(investigationsService.removeItem).toHaveBeenCalledWith('3', 1);
    expect(screen.queryByRole('link', { name: 'jdoe' })).not.toBeInTheDocument();
  });

  it('exports the report through the authenticated download helper', async () => {
    downloadFromApi.mockResolvedValue();
    const user = userEvent.setup();
    renderDetail();

    await user.click(await screen.findByRole('button', { name: 'PDF' }));

    expect(investigationsService.reportRequest).toHaveBeenCalledWith(3, 'pdf', 'en');
    expect(downloadFromApi).toHaveBeenCalledWith('/r/3', { params: { format: 'pdf', locale: 'en' } });
  });

  it('offers no export for an empty investigation', async () => {
    investigationsService.get.mockResolvedValue({ ...INVESTIGATION, items: [] });
    renderDetail();
    expect(await screen.findByText(/No runs yet/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'PDF' })).not.toBeInTheDocument();
  });

  it('switches to the graph tab', async () => {
    const user = userEvent.setup();
    renderDetail();

    await user.click(await screen.findByRole('tab', { name: 'Graph' }));

    expect(screen.getByText('graph tab')).toBeInTheDocument();
  });

  it('deletes the investigation and goes back to the list', async () => {
    investigationsService.remove.mockResolvedValue();
    const user = userEvent.setup();
    renderDetail();

    await user.click(await screen.findByRole('button', { name: 'Delete' }));
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete' }));

    expect(investigationsService.remove).toHaveBeenCalledWith('3');
    expect(await screen.findByText('list page')).toBeInTheDocument();
  });

  it('says so when the investigation does not exist', async () => {
    investigationsService.get.mockRejectedValue(new Error('404'));
    renderDetail();
    expect(await screen.findByText('Investigation not found.')).toBeInTheDocument();
  });
});
