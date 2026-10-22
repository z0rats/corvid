import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router';
import cytoscape from 'cytoscape';
import EntityGraph from './EntityGraph';
import { investigationsService } from '../../../core/services/api/investigationsService';
import { downloadFile } from '../../../core/utils/exportData';

const handlers = {};
const fakeCy = {
  on: vi.fn((event, selectorOrHandler, handler) => {
    handlers[typeof selectorOrHandler === 'string' ? `${event}:${selectorOrHandler}` : event] =
      handler ?? selectorOrHandler;
  }),
  destroy: vi.fn(),
  fit: vi.fn(),
  layout: vi.fn(() => ({ run: vi.fn() })),
  png: vi.fn(() => 'png-blob'),
};
vi.mock('cytoscape', () => ({ default: vi.fn(() => fakeCy) }));
vi.mock('../../../core/services/api/investigationsService', () => ({
  investigationsService: { graph: vi.fn() },
}));
vi.mock('../../../core/utils/exportData', async (importOriginal) => ({
  ...(await importOriginal()),
  downloadFile: vi.fn(),
}));

const node = (id, type, extra = {}) => {
  const value = id.split(':').slice(1).join(':');
  return {
    id, type, value, raw_value: value, label: id.split(':')[1], degree: 1, is_root: false,
    sources: [{ feature: 'username_search', run_id: 5 }], ...extra,
  };
};

const GRAPH = {
  nodes: [
    node('username:jdoe', 'username', { is_root: true, degree: 2, raw_value: 'JDoe' }),
    node('account:https://github.com/jdoe', 'account', { label: 'GitHub: jdoe', raw_value: 'https://github.com/JDoe' }),
    node('subreddit:osint', 'subreddit'),
  ],
  edges: [
    { source: 'username:jdoe', target: 'account:https://github.com/jdoe', relation: 'account', sources: [] },
    { source: 'username:jdoe', target: 'subreddit:osint', relation: 'active in', sources: [] },
  ],
  total_nodes: 3,
  truncated: false,
  entity_types: ['username', 'account', 'subreddit'],
  type_counts: { username: 1, account: 1, subreddit: 1 },
};

function Location() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname + location.search}</div>;
}

function renderGraph() {
  return render(
    <MemoryRouter initialEntries={['/investigations/3']}>
      <Routes>
        <Route
          path="*"
          element={(
            <>
              <EntityGraph
                investigationId={3}
                investigationName="Case A"
                featureLabels={{ username_search: 'Username search' }}
                refreshKey={1}
              />
              <Location />
            </>
          )}
        />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  Object.keys(handlers).forEach((key) => delete handlers[key]);
  investigationsService.graph.mockResolvedValue(GRAPH);
});
afterEach(() => vi.clearAllMocks());

describe('EntityGraph', () => {
  it('draws the elements with cytoscape', async () => {
    renderGraph();

    await waitFor(() => expect(cytoscape).toHaveBeenCalled());
    const { elements, container } = cytoscape.mock.calls.at(-1)[0];
    expect(elements).toHaveLength(5);
    expect(container).toBe(screen.getByTestId('entity-graph-canvas'));
    expect(investigationsService.graph).toHaveBeenCalledWith(3, null);
  });

  it('filters by type on the server, keeping the full chip list', async () => {
    const user = userEvent.setup();
    renderGraph();

    await user.click(await screen.findByRole('button', { name: 'Subreddit (1)' }));

    await waitFor(() => expect(investigationsService.graph).toHaveBeenLastCalledWith(3, ['account', 'username']));
    expect(screen.getByRole('button', { name: 'Subreddit (1)' })).toHaveAttribute('aria-pressed', 'false');

    await user.click(screen.getByRole('button', { name: 'All' }));
    await waitFor(() => expect(investigationsService.graph).toHaveBeenLastCalledWith(3, null));
  });

  it('opens the node panel on tap, with provenance and pivots', async () => {
    renderGraph();
    await waitFor(() => expect(handlers['tap:node']).toBeDefined());

    act(() => handlers['tap:node']({ target: { id: () => 'username:jdoe' } }));

    expect(screen.getByRole('link', { name: 'Username search #5' })).toHaveAttribute('href', '/username-search/history/5');
    await userEvent.click(screen.getByRole('button', { name: 'Reddit Search' }));
    // The value as found, not the normalized (lowercased) one.
    expect(screen.getByTestId('location')).toHaveTextContent('/reddit-search/new?q=JDoe');
  });

  it('offers the external link for an account node', async () => {
    renderGraph();
    await waitFor(() => expect(handlers['tap:node']).toBeDefined());

    act(() => handlers['tap:node']({ target: { id: () => 'account:https://github.com/jdoe' } }));

    expect(screen.getByRole('link', { name: 'Open link' })).toHaveAttribute('href', 'https://github.com/JDoe');
  });

  it("pivots an account node through its linked username", async () => {
    renderGraph();
    await waitFor(() => expect(handlers['tap:node']).toBeDefined());

    act(() => handlers['tap:node']({ target: { id: () => 'account:https://github.com/jdoe' } }));
    await userEvent.click(screen.getByRole('button', { name: 'Username Search: JDoe' }));

    expect(screen.getByTestId('location')).toHaveTextContent('/username-search/new?q=JDoe');
  });

  it('keeps a chip for a type the node cap dropped entirely', async () => {
    investigationsService.graph.mockResolvedValue({
      ...GRAPH,
      truncated: true,
      total_nodes: 400,
      type_counts: { username: 1, account: 1, subreddit: 1, breach: 397 },
    });
    renderGraph();

    expect(await screen.findByRole('button', { name: 'Breach (397)' })).toBeInTheDocument();
  });

  it('warns when the graph was truncated', async () => {
    investigationsService.graph.mockResolvedValue({ ...GRAPH, truncated: true, total_nodes: 900 });
    renderGraph();
    expect(await screen.findByText(/Showing the 3 most connected of 900 entities/)).toBeInTheDocument();
  });

  it('shows the empty state', async () => {
    investigationsService.graph.mockResolvedValue({ ...GRAPH, nodes: [], edges: [], total_nodes: 0 });
    renderGraph();
    expect(await screen.findByText(/No entities to show/)).toBeInTheDocument();
    expect(cytoscape).not.toHaveBeenCalled();
  });

  it('exports a PNG', async () => {
    const user = userEvent.setup();
    renderGraph();
    await waitFor(() => expect(cytoscape).toHaveBeenCalled());

    await user.click(screen.getByRole('button', { name: 'Export PNG' }));

    expect(downloadFile).toHaveBeenCalledWith('png-blob', 'investigation-Case_A.png', 'image/png');
  });

  it('shows a load error', async () => {
    investigationsService.graph.mockRejectedValue(new Error('down'));
    renderGraph();
    expect(await screen.findByText("Couldn't load the graph.")).toBeInTheDocument();
  });
});
