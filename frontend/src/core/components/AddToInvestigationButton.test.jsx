import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AddToInvestigationButton from './AddToInvestigationButton';
import { investigationsService } from '../services/api/investigationsService';

vi.mock('../services/api/investigationsService', () => ({
  investigationsService: {
    list: vi.fn(),
    memberships: vi.fn(),
    addItem: vi.fn(),
    create: vi.fn(),
  },
}));

beforeEach(() => {
  investigationsService.list.mockResolvedValue([
    { id: 1, name: 'Case A' },
    { id: 2, name: 'Case B' },
  ]);
  investigationsService.memberships.mockResolvedValue([{ id: 2, name: 'Case B' }]);
  investigationsService.addItem.mockResolvedValue({ id: 10 });
});

afterEach(() => vi.clearAllMocks());

describe('AddToInvestigationButton', () => {
  it('adds the run to a chosen investigation', async () => {
    const user = userEvent.setup();
    render(<AddToInvestigationButton feature="username_search" runId={5} />);

    await user.click(screen.getByRole('button', { name: 'Add to investigation' }));
    await user.click(await screen.findByRole('menuitem', { name: 'Case A' }));

    expect(investigationsService.memberships).toHaveBeenCalledWith('username_search', 5);
    expect(investigationsService.addItem).toHaveBeenCalledWith(1, 'username_search', 5);
    expect(await screen.findByText('Added to "Case A"')).toBeInTheDocument();
  });

  it('disables investigations that already hold the run', async () => {
    const user = userEvent.setup();
    render(<AddToInvestigationButton feature="username_search" runId={5} />);

    await user.click(screen.getByRole('button', { name: 'Add to investigation' }));

    const member = await screen.findByRole('menuitem', { name: /Case B/ });
    expect(member).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByText('Already added')).toBeInTheDocument();
  });

  it('creates a new investigation and adds the run to it', async () => {
    investigationsService.create.mockResolvedValue({ id: 3, name: 'Fresh' });
    const user = userEvent.setup();
    render(<AddToInvestigationButton feature="ioc_lookup" runId={9} />);

    await user.click(screen.getByRole('button', { name: 'Add to investigation' }));
    await user.click(await screen.findByRole('menuitem', { name: 'New investigation…' }));
    await user.type(screen.getByLabelText('Name'), '  Fresh  ');
    await user.click(screen.getByRole('button', { name: 'Create and add' }));

    expect(investigationsService.create).toHaveBeenCalledWith('Fresh');
    expect(investigationsService.addItem).toHaveBeenCalledWith(3, 'ioc_lookup', 9);
  });

  it('reports a failed add', async () => {
    investigationsService.addItem.mockRejectedValue(new Error('409'));
    const user = userEvent.setup();
    render(<AddToInvestigationButton feature="ioc_lookup" runId={9} />);

    await user.click(screen.getByRole('button', { name: 'Add to investigation' }));
    await user.click(await screen.findByRole('menuitem', { name: 'Case A' }));

    expect(await screen.findByText("Couldn't add this run to the investigation.")).toBeInTheDocument();
  });
});
