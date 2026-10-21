import { act, renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { useCommandPalette } from './useCommandPalette';
import api from '../services/baseApi';
import { copyToClipboard } from '../utils/clipboard';
import { getRecents, getQueryHistory, addQueryToHistory } from '../utils/commandPaletteStorage';

const navigate = vi.fn();
const toggleColorMode = vi.fn();

vi.mock('react-router', async (importOriginal) => ({
  ...(await importOriginal()),
  useNavigate: () => navigate,
}));
vi.mock('./ui/useThemeManager', () => ({ useThemeManager: () => ({ toggleColorMode }) }));
vi.mock('../services/baseApi', () => ({ default: { post: vi.fn() } }));
vi.mock('../utils/clipboard', () => ({ copyToClipboard: vi.fn() }));

function setup() {
  return renderHook(() => useCommandPalette(), { wrapper: MemoryRouter }).result;
}

function key(k, mods = {}) {
  return { key: k, preventDefault: vi.fn(), metaKey: false, ctrlKey: false, shiftKey: false, altKey: false, ...mods };
}

function typeQuery(result, q) {
  act(() => result.current.open());
  act(() => result.current.setQuery(q));
}

beforeEach(() => {
  localStorage.clear();
  navigate.mockReset();
  toggleColorMode.mockReset();
  api.post.mockReset();
  copyToClipboard.mockReset();
});

describe('useCommandPalette — open/close', () => {
  it('opens with an initial query and Escape clears the query before closing', () => {
    const result = setup();
    act(() => result.current.open('8.8.8.8'));
    expect(result.current.isOpen).toBe(true);
    expect(result.current.query).toBe('8.8.8.8');

    act(() => result.current.handlePaletteKeyDown(key('Escape')));
    expect(result.current.query).toBe('');
    expect(result.current.isOpen).toBe(true);

    act(() => result.current.handlePaletteKeyDown(key('Escape')));
    expect(result.current.isOpen).toBe(false);
  });

  it('empty query shows the registry as selectable rows', () => {
    const result = setup();
    act(() => result.current.open());
    expect(result.current.parsed.kind).toBe('empty');
    expect(result.current.visibleResults.length).toBeGreaterThan(0);
    expect(result.current.visibleResults.every((r) => r.type === 'entry')).toBe(true);
  });
});

describe('useCommandPalette — opening a tool for a value', () => {
  it('navigates with the value prefilled, records a recent + breadcrumb, and closes', () => {
    const result = setup();
    typeQuery(result, '8.8.8.8');
    expect(result.current.parsed.kind).toBe('value');
    const first = result.current.visibleResults[0];
    expect(first.type).toBe('entry');

    act(() => result.current.runSelected(0));

    expect(navigate).toHaveBeenCalledTimes(1);
    expect(navigate.mock.calls[0][0]).toMatch(/\?q=8\.8\.8\.8$/);
    expect(result.current.isOpen).toBe(false);
    expect(result.current.breadcrumbs).toEqual([
      expect.objectContaining({ toolId: first.entry.id, value: '8.8.8.8' }),
    ]);
    expect(getRecents()[0]).toEqual(expect.objectContaining({ toolId: first.entry.id, value: '8.8.8.8' }));
    expect(getQueryHistory()).toContain('8.8.8.8');
  });

  it('opening a tool from the empty state navigates without a ?q=', () => {
    const result = setup();
    act(() => result.current.open());
    act(() => result.current.runSelected(0));
    expect(navigate).toHaveBeenCalledTimes(1);
    expect(navigate.mock.calls[0][0]).not.toContain('?q=');
  });
});

describe('useCommandPalette — instant answers', () => {
  it('defangs through the API, copies the result and reports it', async () => {
    api.post.mockResolvedValue({ data: { results: [{ processed: '1[.]1[.]1[.]1' }] } });
    copyToClipboard.mockResolvedValue(true);
    const result = setup();
    typeQuery(result, 'defang 1.1.1.1');
    expect(result.current.parsed.kind).toBe('instant');

    await act(async () => result.current.runSelected());

    expect(api.post).toHaveBeenCalledWith('/api/defang/', { text: '1.1.1.1', operation: 'defang' });
    expect(copyToClipboard).toHaveBeenCalledWith('1[.]1[.]1[.]1');
    expect(result.current.notice).toEqual({ message: 'Copied: 1[.]1[.]1[.]1', severity: 'success' });
    expect(result.current.isOpen).toBe(false);
  });

  it('shows the processed value as info when copying is not possible', async () => {
    api.post.mockResolvedValue({ data: { results: [{ processed: 'evil.com' }] } });
    copyToClipboard.mockResolvedValue(false);
    const result = setup();
    typeQuery(result, 'fang evil[.]com');
    await act(async () => result.current.runSelected());
    expect(result.current.notice).toEqual({ message: 'evil.com', severity: 'info' });
  });

  it('reports a failure without crashing', async () => {
    api.post.mockRejectedValue(new Error('500'));
    const result = setup();
    typeQuery(result, 'defang 1.1.1.1');
    await act(async () => result.current.runSelected());
    expect(result.current.notice).toEqual({ message: "Couldn't process that value", severity: 'error' });
    expect(result.current.isOpen).toBe(false);
  });
});

describe('useCommandPalette — > actions', () => {
  it('>settings navigates to settings and closes', () => {
    const result = setup();
    typeQuery(result, '>settings');
    act(() => result.current.runSelected());
    expect(navigate).toHaveBeenCalledWith('/settings');
    expect(result.current.isOpen).toBe(false);
  });

  it('>theme toggles the color mode', () => {
    const result = setup();
    typeQuery(result, '>theme');
    act(() => result.current.runSelected());
    expect(toggleColorMode).toHaveBeenCalledTimes(1);
  });

  it('>record starts recording and keeps the palette open', () => {
    const result = setup();
    typeQuery(result, '>record');
    act(() => result.current.runSelected());
    expect(result.current.isRecording).toBe(true);
    expect(result.current.isOpen).toBe(true);
    expect(result.current.query).toBe('');
  });

  it('>playbook:manage switches the view', () => {
    const result = setup();
    typeQuery(result, '>playbook:manage');
    act(() => result.current.runSelected());
    expect(result.current.view).toBe('playbook-manage');
  });

  it('an unknown action shows an info notice', () => {
    const result = setup();
    act(() => result.current.runAction({ kind: 'action', action: 'bogus' }));
    expect(result.current.notice).toEqual({ message: 'Unknown action', severity: 'info' });
  });
});

describe('useCommandPalette — keyboard shortcuts on a focused value', () => {
  it('Ctrl+C copies the raw value, Ctrl+Alt+C the defanged one', async () => {
    copyToClipboard.mockResolvedValue(true);
    api.post.mockResolvedValue({ data: { results: [{ processed: '8[.]8[.]8[.]8' }] } });
    const result = setup();
    typeQuery(result, '8.8.8.8');

    await act(async () => result.current.handlePaletteKeyDown(key('c', { ctrlKey: true })));
    expect(copyToClipboard).toHaveBeenLastCalledWith('8.8.8.8');

    await act(async () => result.current.handlePaletteKeyDown(key('c', { ctrlKey: true, altKey: true })));
    expect(copyToClipboard).toHaveBeenLastCalledWith('8[.]8[.]8[.]8');
  });

  it('copy failure is reported as an error', async () => {
    copyToClipboard.mockResolvedValue(false);
    const result = setup();
    typeQuery(result, '8.8.8.8');
    await act(async () => result.current.copyFocusedValue(false));
    expect(result.current.notice.severity).toBe('error');
  });

  it('copy is a no-op when the query carries no value', async () => {
    const result = setup();
    typeQuery(result, '>settings');
    await act(async () => result.current.copyFocusedValue(false));
    expect(copyToClipboard).not.toHaveBeenCalled();
  });

  it('Ctrl+Shift+B sends the value to bulk lookup', () => {
    const result = setup();
    typeQuery(result, 'evil.example.com');
    act(() => result.current.handlePaletteKeyDown(key('b', { ctrlKey: true, shiftKey: true })));
    expect(navigate).toHaveBeenCalledWith('/ioc-tools/bulk?q=evil.example.com');
    expect(result.current.isOpen).toBe(false);
  });

  it('Ctrl+P pins and unpins the focused tool', () => {
    const result = setup();
    act(() => result.current.open());
    const id = result.current.visibleResults[0].entry.id;
    act(() => result.current.handlePaletteKeyDown(key('p', { ctrlKey: true })));
    expect(result.current.pinnedIds).toContain(id);
    act(() => result.current.togglePin(id));
    expect(result.current.pinnedIds).not.toContain(id);
  });

  it('Ctrl+K toggles the action panel for the selected row', () => {
    const result = setup();
    act(() => result.current.open());
    act(() => result.current.handlePaletteKeyDown(key('k', { ctrlKey: true })));
    expect(result.current.actionPanelIndex).toBe(0);
    act(() => result.current.handlePaletteKeyDown(key('k', { ctrlKey: true })));
    expect(result.current.actionPanelIndex).toBe(null);
  });

  it('Ctrl+ArrowUp/Down walk the query history', () => {
    addQueryToHistory('first');
    addQueryToHistory('second');
    const [newest, older] = getQueryHistory();
    const result = setup();
    act(() => result.current.open());

    act(() => result.current.handlePaletteKeyDown(key('ArrowUp', { ctrlKey: true })));
    expect(result.current.query).toBe(newest);
    act(() => result.current.handlePaletteKeyDown(key('ArrowUp', { ctrlKey: true })));
    expect(result.current.query).toBe(older);
    act(() => result.current.handlePaletteKeyDown(key('ArrowUp', { ctrlKey: true })));
    expect(result.current.query).toBe(older); // clamped at the oldest
    act(() => result.current.handlePaletteKeyDown(key('ArrowDown', { ctrlKey: true })));
    act(() => result.current.handlePaletteKeyDown(key('ArrowDown', { ctrlKey: true })));
    expect(result.current.query).toBe('');
  });
});

describe('useCommandPalette — misc state', () => {
  it('setQuery resets selection and the action panel', async () => {
    const result = setup();
    act(() => result.current.open());
    act(() => result.current.setSelectedIndex(2));
    act(() => result.current.toggleActionPanel(2));
    act(() => result.current.setQuery('who'));
    expect(result.current.selectedIndex).toBe(0);
    expect(result.current.actionPanelIndex).toBe(null);
    act(() => result.current.openShortcutSheet());
    expect(result.current.showShortcutSheet).toBe(true);
    act(() => result.current.closeShortcutSheet());
    await waitFor(() => expect(result.current.showShortcutSheet).toBe(false));
  });

  it('defaults the display preferences when settings have not loaded', () => {
    const result = setup();
    expect(result.current.autoOpenOnSingleMatch).toBe(true);
    expect(result.current.alwaysTiles).toBe(false);
  });
});
