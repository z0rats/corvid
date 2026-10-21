import { render, screen, fireEvent, within, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import TemplatesView from './TemplatesView';
import { templatesApi } from '../../services/api/templatesApi';
import { categoriesApi } from '../../services/api/categoriesApi';
import { SYSTEM_CATEGORY_IDS } from '../../constants/templateConstants';

// Capture the DragDropContext's onDragEnd so drags can be replayed as plain events.
const dnd = vi.hoisted(() => ({ onDragEnd: null }));
vi.mock('@hello-pangea/dnd', () => {
  const provided = { innerRef: () => {}, droppableProps: {}, draggableProps: {}, dragHandleProps: {}, placeholder: null };
  return {
    DragDropContext: ({ onDragEnd, children }) => { dnd.onDragEnd = onDragEnd; return children; },
    Droppable: ({ children }) => children(provided, {}),
    Draggable: ({ children }) => children(provided, {}),
  };
});
vi.mock('../../services/api/templatesApi', () => ({
  templatesApi: {
    getTemplates: vi.fn(), reorderTemplates: vi.fn(), deleteTemplate: vi.fn(),
    executeTemplate: vi.fn(), updateTemplate: vi.fn(),
  },
}));
vi.mock('../../services/api/categoriesApi', () => ({
  categoriesApi: {
    getCategories: vi.fn(), createCategory: vi.fn(), updateCategory: vi.fn(), deleteCategory: vi.fn(),
    reorderCategories: vi.fn(), moveTemplates: vi.fn(),
  },
}));

const CAT_A = { id: 'cat-a', name: 'Phishing', is_system: false, order_number: 2 };
const CAT_B = { id: 'cat-b', name: 'Malware', is_system: false, order_number: 3 };
const CATEGORIES = [
  { id: SYSTEM_CATEGORY_IDS.FAVORITES, name: 'Favorites', is_system: true, order_number: 0 },
  { id: SYSTEM_CATEGORY_IDS.DEFAULT, name: 'Default', is_system: true, order_number: 1 },
  CAT_A, CAT_B,
];
const tpl = (id, category_id, order_number, extra = {}) => ({
  id, title: `Template ${id}`, description: `About ${id}`, category_id, order_number,
  payload_fields: [{ name: 'email_body', type: 'textarea' }], ...extra,
});
const TEMPLATES = [
  tpl('a1', 'cat-a', 0), tpl('a2', 'cat-a', 1),
  tpl('b1', 'cat-b', 2), tpl('b2', 'cat-b', 3), tpl('b3', 'cat-b', 4),
];

async function setup() {
  templatesApi.getTemplates.mockResolvedValue(TEMPLATES.map((t) => ({ ...t })));
  categoriesApi.getCategories.mockResolvedValue(CATEGORIES);
  templatesApi.reorderTemplates.mockResolvedValue({});
  render(<MemoryRouter><TemplatesView /></MemoryRouter>);
  await screen.findByText('Template b3');
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});
afterEach(() => vi.clearAllMocks());

describe('TemplatesView', () => {
  it('lists templates grouped by category and prompts for a selection', async () => {
    await setup();
    expect(screen.getByText('Phishing')).toBeInTheDocument();
    expect(screen.getByText('Malware')).toBeInTheDocument();
    expect(screen.getByText('Select a template to get started')).toBeInTheDocument();
  });

  it('reordering inside a later category persists that category\'s new order', async () => {
    // Regression: a global source index was mixed with a category-local destination index,
    // so moving b1 to the end of "Malware" saved the unchanged order.
    await setup();
    await act(async () => {
      await dnd.onDragEnd({
        type: 'template', draggableId: 'b1',
        source: { droppableId: 'cat-b', index: 0 }, destination: { droppableId: 'cat-b', index: 2 },
      });
    });
    const ids = templatesApi.reorderTemplates.mock.calls[0][0];
    const malware = ids.filter((id) => id.startsWith('b'));
    expect(malware).toEqual(['b2', 'b3', 'b1']);
    expect(ids.filter((id) => id.startsWith('a'))).toEqual(['a1', 'a2']);
  });

  it('dragging into another category moves the template there', async () => {
    categoriesApi.moveTemplates.mockResolvedValue({});
    await setup();
    await act(async () => {
      await dnd.onDragEnd({
        type: 'template', draggableId: 'a1',
        source: { droppableId: 'cat-a', index: 0 }, destination: { droppableId: 'cat-b', index: 0 },
      });
    });
    expect(categoriesApi.moveTemplates).toHaveBeenCalledWith(['a1'], 'cat-b');
  });

  it('categories cannot be dropped above the system groups', async () => {
    await setup();
    await act(async () => {
      await dnd.onDragEnd({ type: 'category', draggableId: 'cat-cat-b', source: { index: 3 }, destination: { index: 0 } });
    });
    expect(categoriesApi.reorderCategories).not.toHaveBeenCalled();
  });

  it('a failed reorder is reported and reloads from the server', async () => {
    categoriesApi.moveTemplates.mockRejectedValue(new Error('x'));
    await setup();
    await act(async () => {
      await dnd.onDragEnd({
        type: 'template', draggableId: 'a1',
        source: { droppableId: 'cat-a', index: 0 }, destination: { droppableId: 'cat-b', index: 0 },
      });
    });
    expect(await screen.findByText('Failed to update order')).toBeInTheDocument();
    expect(templatesApi.getTemplates).toHaveBeenCalledTimes(2);
  });

  it('selects a template, fills its fields and executes it', async () => {
    templatesApi.executeTemplate.mockResolvedValue({ result: 'Verdict: phishing' });
    await setup();
    fireEvent.click(screen.getByText('Template a1'));
    await waitFor(() => expect(screen.getAllByText('Template a1')).toHaveLength(2)); // card + detail panel
    fireEvent.change(screen.getByLabelText('email_body'), { target: { value: 'Click here to reset your password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Execute Template' }));
    expect(await screen.findByText('Template executed successfully!')).toBeInTheDocument();
    expect(templatesApi.executeTemplate).toHaveBeenCalledWith('a1', {
      template_id: 'a1',
      payload_data: { email_body: 'Click here to reset your password' },
    });
  });

  it('search filters the list', async () => {
    await setup();
    fireEvent.change(screen.getByPlaceholderText('Search templates (5)...'), { target: { value: 'b2' } });
    await waitFor(() => expect(screen.queryByText('Template a1')).toBeNull());
    expect(screen.getByText('Template b2')).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText('Search templates (5)...'), { target: { value: 'nothing-matches' } });
    expect(await screen.findByText('No templates match your search')).toBeInTheDocument();
  });

  it('deletes a template after confirmation', async () => {
    templatesApi.deleteTemplate.mockResolvedValue({});
    await setup();
    const deletes = screen.getAllByLabelText('Delete template');
    fireEvent.click(deletes[1]); // a2, second card
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Delete' }));
    expect(await screen.findByText('Template deleted successfully!')).toBeInTheDocument();
    expect(templatesApi.deleteTemplate).toHaveBeenCalledWith('a2');
    await waitFor(() => expect(screen.queryByText('Template a2')).toBeNull());
  });

  it('toggling favorite moves the template into Favorites', async () => {
    categoriesApi.moveTemplates.mockResolvedValue({});
    await setup();
    fireEvent.click(screen.getByText('Template b3'));
    fireEvent.click(await screen.findByRole('button', { name: 'Toggle favorite' }));
    await waitFor(() => expect(categoriesApi.moveTemplates).toHaveBeenCalledWith(['b3'], SYSTEM_CATEGORY_IDS.FAVORITES));
  });

  it('edits a template and reflects the change', async () => {
    templatesApi.updateTemplate.mockImplementation(async (id, data) => ({ ...data, id }));
    await setup();
    fireEvent.click(screen.getAllByLabelText('Edit template')[0]);
    const dialog = await screen.findByRole('dialog');
    fireEvent.change(within(dialog).getByLabelText(/^Title/), { target: { value: 'Phishing triage v2' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save Changes' }));
    expect(await screen.findByText('Template updated successfully!')).toBeInTheDocument();
    expect(templatesApi.updateTemplate).toHaveBeenCalledWith('a1', expect.objectContaining({ title: 'Phishing triage v2' }));
    expect(screen.getByText('Phishing triage v2')).toBeInTheDocument();
  });

  it('creates, renames and deletes a group', async () => {
    categoriesApi.createCategory.mockResolvedValue({ id: 'cat-c', name: 'Recon', is_system: false, order_number: 4 });
    categoriesApi.updateCategory.mockResolvedValue({ ...CAT_A, name: 'Phishing & BEC' });
    categoriesApi.deleteCategory.mockResolvedValue({});
    await setup();

    fireEvent.click(screen.getByText('Add Group'));
    let dialog = await screen.findByRole('dialog');
    fireEvent.change(within(dialog).getByLabelText('Group name'), { target: { value: '  Recon  ' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Create' }));
    expect(await screen.findByText('Group created!')).toBeInTheDocument();
    expect(categoriesApi.createCategory).toHaveBeenCalledWith('Recon');

    // option menus follow category order: Favorites, Default, Phishing, Malware, Recon
    const phishingOptions = () => screen.getByText(/^Phishing/).closest('.MuiBox-root').querySelector('button');
    fireEvent.click(phishingOptions());
    fireEvent.click(await screen.findByRole('menuitem', { name: 'Rename' }));
    dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByLabelText('Group name')).toHaveValue('Phishing');
    fireEvent.change(within(dialog).getByLabelText('Group name'), { target: { value: 'Phishing & BEC' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }));
    expect(await screen.findByText('Group renamed!')).toBeInTheDocument();
    expect(categoriesApi.updateCategory).toHaveBeenCalledWith('cat-a', 'Phishing & BEC');

    fireEvent.click(phishingOptions());
    fireEvent.click(await screen.findByRole('menuitem', { name: 'Delete' }));
    dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText(/It contains 2 templates/)).toBeInTheDocument();
    fireEvent.click(within(dialog).getByLabelText('Delete all templates in this group'));
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }));
    expect(await screen.findByText('Group deleted!')).toBeInTheDocument();
    expect(categoriesApi.deleteCategory).toHaveBeenCalledWith(expect.any(String), 'delete_templates');
  });
});
