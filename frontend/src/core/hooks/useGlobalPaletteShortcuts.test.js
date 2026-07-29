import React from 'react';
import { renderHook, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { useGlobalPaletteShortcuts } from './useGlobalPaletteShortcuts';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  mockNavigate.mockClear();
});

function setup({ isOpen = false, initialEntries = ['/'] } = {}) {
  const open = vi.fn();
  const close = vi.fn();
  const onShowShortcutSheet = vi.fn();
  const wrapper = ({ children }) => React.createElement(MemoryRouter, { initialEntries }, children);
  renderHook(() => useGlobalPaletteShortcuts(isOpen, open, close, onShowShortcutSheet), { wrapper });
  return { open, close, onShowShortcutSheet };
}

describe('useGlobalPaletteShortcuts', () => {
  it('opens on "/" when no input is focused and the palette is closed', () => {
    const { open } = setup({ isOpen: false });

    fireEvent.keyDown(window, { key: '/' });

    expect(open).toHaveBeenCalledTimes(1);
  });

  it('does not open on "/" while a text input elsewhere is focused', () => {
    const { open } = setup({ isOpen: false });
    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();

    fireEvent.keyDown(input, { key: '/' });

    expect(open).not.toHaveBeenCalled();
    document.body.removeChild(input);
  });

  it('opens on Cmd/Ctrl+K regardless of focus', () => {
    const { open } = setup({ isOpen: false });

    fireEvent.keyDown(window, { key: 'k', metaKey: true });

    expect(open).toHaveBeenCalledTimes(1);
  });

  it('Cmd/Ctrl+, navigates to Settings and closes when open, closed or open', () => {
    const { close: closeWhenClosed } = setup({ isOpen: false });
    fireEvent.keyDown(window, { key: ',', metaKey: true });
    expect(mockNavigate).toHaveBeenCalledWith('/settings');
    expect(closeWhenClosed).not.toHaveBeenCalled();

    mockNavigate.mockClear();
    const { close: closeWhenOpen } = setup({ isOpen: true });
    fireEvent.keyDown(window, { key: ',', metaKey: true });
    expect(mockNavigate).toHaveBeenCalledWith('/settings');
    expect(closeWhenOpen).toHaveBeenCalledTimes(1);
  });

  it('shows the shortcut sheet on "?" when closed and not typing in a field', () => {
    const { onShowShortcutSheet } = setup({ isOpen: false });

    fireEvent.keyDown(window, { key: '?' });

    expect(onShowShortcutSheet).toHaveBeenCalledTimes(1);
  });

  it('ignores "/" and Cmd/Ctrl+K while already open', () => {
    const { open } = setup({ isOpen: true });

    fireEvent.keyDown(window, { key: '/' });
    fireEvent.keyDown(window, { key: 'k', metaKey: true });

    expect(open).not.toHaveBeenCalled();
  });

  it('dispatches OPEN_COMMAND_PALETTE_EVENT to open with a carried query when closed', async () => {
    const { OPEN_COMMAND_PALETTE_EVENT } = await import('./useGlobalPaletteShortcuts');
    const { open } = setup({ isOpen: false });

    window.dispatchEvent(new CustomEvent(OPEN_COMMAND_PALETTE_EVENT, { detail: { query: 'reddit' } }));

    expect(open).toHaveBeenCalledWith('reddit');
  });

  it('a pasted image navigates to /image-tools with the file in location state', () => {
    const { close } = setup({ isOpen: true, initialEntries: ['/dashboard'] });
    const file = new File(['data'], 'clip.png', { type: 'image/png' });
    const items = [{ type: 'image/png', getAsFile: () => file }];

    const event = new Event('paste', { bubbles: true, cancelable: true });
    Object.defineProperty(event, 'clipboardData', { value: { items } });
    window.dispatchEvent(event);

    expect(close).toHaveBeenCalledTimes(1);
    expect(mockNavigate).toHaveBeenCalledWith('/image-tools', { state: { file } });
  });

  it('does not intercept a pasted image while already on /image-tools', () => {
    setup({ isOpen: false, initialEntries: ['/image-tools'] });
    const file = new File(['data'], 'clip.png', { type: 'image/png' });
    const items = [{ type: 'image/png', getAsFile: () => file }];

    const event = new Event('paste', { bubbles: true, cancelable: true });
    Object.defineProperty(event, 'clipboardData', { value: { items } });
    window.dispatchEvent(event);

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('ignores a paste with no image item', () => {
    setup({ isOpen: false });
    const items = [{ type: 'text/plain', getAsFile: () => null }];

    const event = new Event('paste', { bubbles: true, cancelable: true });
    Object.defineProperty(event, 'clipboardData', { value: { items } });
    window.dispatchEvent(event);

    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
