import { render, screen, fireEvent, within } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router';
import { Provider, createStore } from 'jotai';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../config/theme';
import Layout from './Layout';
import { themeModeAtom } from '../../state/atoms';
import { OPEN_COMMAND_PALETTE_EVENT } from '../../hooks/useGlobalPaletteShortcuts';

vi.mock('../../services/api/activityService', () => ({ activityService: { listActive: vi.fn().mockResolvedValue([]), list: vi.fn().mockResolvedValue([]) } }));
vi.mock('../../services/api/alertsService', () => ({
  alertsService: { getUnreadCount: vi.fn().mockResolvedValue(0), list: vi.fn().mockResolvedValue([]) },
}));
vi.mock('../../services/baseApi', () => ({ default: { get: vi.fn().mockResolvedValue({ data: {} }), post: vi.fn() } }));

function renderAt(path) {
  const store = createStore();
  const utils = render(
    <ThemeProvider theme={lightTheme}>
      <Provider store={store}>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route element={<Layout />}>
              <Route path="*" element={<div>PAGE CONTENT</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </Provider>
    </ThemeProvider>,
  );
  return { ...utils, store };
}

const stored = (key) => JSON.parse(localStorage.getItem(key));

beforeEach(() => localStorage.clear());

describe('Layout', () => {
  it('renders the routed page inside the app chrome', () => {
    renderAt('/ioc-tools/lookup');
    expect(screen.getByText('PAGE CONTENT')).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Home' })[0]).toHaveAttribute('href', '/');
    expect(screen.getAllByRole('link', { name: 'Settings' })[0]).toHaveAttribute('href', expect.stringContaining('/settings'));
  });

  it('flat feature tabs render above the page; nested ones get the side drawer', () => {
    const { unmount } = renderAt('/ioc-tools/lookup');
    expect(screen.getAllByRole('tab').length).toBeGreaterThan(1);
    unmount();
    renderAt('/newsfeed');
    expect(screen.queryAllByRole('tab')).toHaveLength(0);
    expect(screen.getAllByRole('separator', { name: 'Resize section panel' }).length).toBeGreaterThan(0);
  });

  it('collapsing the tool panel is remembered', () => {
    renderAt('/');
    fireEvent.click(screen.getAllByRole('button', { name: 'Toggle sidebar' })[0]);
    expect(stored('layout.leftPanelOpen')).toBe(false);
  });

  it('dragging the resize handle changes and persists the panel width, clamped', () => {
    renderAt('/');
    const handle = screen.getByRole('separator', { name: 'Resize tool panel' });
    fireEvent.pointerDown(handle, { clientX: 220 });
    fireEvent.pointerMove(document, { clientX: 260 });
    fireEvent.pointerUp(document);
    expect(stored('layout.leftPanelWidth')).toBe(260);

    fireEvent.pointerDown(handle, { clientX: 260 });
    fireEvent.pointerMove(document, { clientX: 2000 });
    fireEvent.pointerUp(document);
    expect(stored('layout.leftPanelWidth')).toBe(360);
    expect(document.body.style.cursor).toBe('');
  });

  it('keyboard resizing works through the separator', () => {
    renderAt('/');
    const handle = screen.getByRole('separator', { name: 'Resize tool panel' });
    const before = Number(handle.getAttribute('aria-valuenow'));
    fireEvent.keyDown(handle, { key: 'ArrowRight' });
    expect(Number(screen.getByRole('separator', { name: 'Resize tool panel' }).getAttribute('aria-valuenow'))).toBeGreaterThan(before);
  });

  it('the search box opens the command palette', () => {
    const listener = vi.fn();
    window.addEventListener(OPEN_COMMAND_PALETTE_EVENT, listener);
    renderAt('/ioc-tools/lookup');
    const search = screen.getByRole('button', { name: /Search tools/i });
    fireEvent.click(search);
    fireEvent.keyDown(search, { key: 'Enter' });
    expect(listener).toHaveBeenCalledTimes(2);
    window.removeEventListener(OPEN_COMMAND_PALETTE_EVENT, listener);
  });

  it('toggles dark mode', () => {
    const { store } = renderAt('/');
    const before = store.get(themeModeAtom);
    fireEvent.click(screen.getByRole('button', { name: 'Toggle dark mode' }));
    expect(store.get(themeModeAtom)).not.toBe(before);
  });

  it('the left panel lists tool sections linking to their routes', () => {
    renderAt('/');
    const nav = screen.getAllByRole('link').map((a) => a.getAttribute('href'));
    expect(nav).toEqual(expect.arrayContaining(['/ioc-tools', '/newsfeed']));
    expect(within(document.body).getAllByText(/Newsfeed/).length).toBeGreaterThan(0);
  });
});
