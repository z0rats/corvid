import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router';
import { Provider, createStore } from 'jotai';
import { generalSettingsState } from '../../state/atoms';
import { OPEN_COMMAND_PALETTE_EVENT } from '../../hooks/useGlobalPaletteShortcuts';
import api from '../../services/baseApi';
import { copyToClipboard } from '../../utils/clipboard';
import { sha256Hex } from '../../utils/fileHash';
import StartScreen from './StartScreen';

vi.mock('../../services/api/activityService', () => ({
  activityService: { listRecent: vi.fn().mockResolvedValue([]) },
}));
vi.mock('./ApiKeysOnboardingHint', () => ({ default: () => null }));
vi.mock('../../services/baseApi', () => ({ default: { post: vi.fn() } }));
vi.mock('../../utils/clipboard', () => ({ copyToClipboard: vi.fn() }));
vi.mock('../../utils/fileHash', () => ({ sha256Hex: vi.fn() }));

const { mockNavigate, toggleColorMode } = vi.hoisted(() => ({ mockNavigate: vi.fn(), toggleColorMode: vi.fn() }));
vi.mock('react-router', async (importOriginal) => ({ ...(await importOriginal()), useNavigate: () => mockNavigate }));
vi.mock('../../hooks/ui/useThemeManager', () => ({ useThemeManager: () => ({ toggleColorMode }) }));

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

function renderStartScreen(store = createStore()) {
  return render(
    <Provider store={store}>
      <MemoryRouter>
        <StartScreen />
      </MemoryRouter>
    </Provider>,
  );
}

const input = () => screen.getByRole('textbox', { name: /search tools/i });

function submit(text) {
  fireEvent.change(input(), { target: { value: text } });
  fireEvent.keyDown(input(), { key: 'Enter' });
}

function drop(target, file) {
  fireEvent.drop(target, { dataTransfer: { types: ['Files'], files: [file] } });
}

describe('StartScreen instant answers', () => {
  it('defangs a value through the backend, copies it and confirms', async () => {
    api.post.mockResolvedValue({ data: { results: [{ processed: '185[.]220[.]101[.]7' }] } });
    copyToClipboard.mockResolvedValue(true);
    renderStartScreen();

    submit('defang 185.220.101.7');

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/api/defang/', { text: '185.220.101.7', operation: 'defang' }));
    expect(copyToClipboard).toHaveBeenCalledWith('185[.]220[.]101[.]7');
    expect(await screen.findByText('Copied: 185[.]220[.]101[.]7')).toBeInTheDocument();
    expect(input()).toHaveValue('');
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('shows the converted value when the clipboard is unavailable', async () => {
    api.post.mockResolvedValue({ data: { results: [{ processed: 'hxxp://evil[.]example' }] } });
    copyToClipboard.mockResolvedValue(false);
    renderStartScreen();

    submit('defang http://evil.example');

    expect(await screen.findByText('hxxp://evil[.]example')).toBeInTheDocument();
  });

  it('reports a failed conversion', async () => {
    api.post.mockRejectedValue(new Error('offline'));
    renderStartScreen();

    submit('fang 185[.]220[.]101[.]7');

    expect(await screen.findByText("Couldn't process that value")).toBeInTheDocument();
    expect(copyToClipboard).not.toHaveBeenCalled();
  });

  it('replaces the result list with a keyboard hint while an instant answer is typed', async () => {
    const user = userEvent.setup();
    renderStartScreen();
    await user.type(input(), 'defang 1.2.3.4');
    expect(screen.getByText('↑↓ navigate · Enter open · Esc close')).toBeInTheDocument();
  });
});

describe('StartScreen actions', () => {
  it('>settings opens Settings', async () => {
    renderStartScreen();
    submit('>settings');
    expect(mockNavigate).toHaveBeenCalledWith('/settings');
    expect(input()).toHaveValue('');
  });

  it('>theme toggles the colour mode without navigating', async () => {
    renderStartScreen();
    submit('>theme');
    expect(toggleColorMode).toHaveBeenCalledTimes(1);
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('hands modal-only actions to the full palette with the typed query', async () => {
    const listener = vi.fn();
    window.addEventListener(OPEN_COMMAND_PALETTE_EVENT, listener);
    renderStartScreen();

    submit('>record');

    window.removeEventListener(OPEN_COMMAND_PALETTE_EVENT, listener);
    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener.mock.calls[0][0].detail).toEqual({ query: '>record' });
    expect(input()).toHaveValue('');
  });

  it('does nothing on Enter for an unknown action', async () => {
    const listener = vi.fn();
    window.addEventListener(OPEN_COMMAND_PALETTE_EVENT, listener);
    renderStartScreen();

    submit('>frobnicate');

    window.removeEventListener(OPEN_COMMAND_PALETTE_EVENT, listener);
    expect(listener).not.toHaveBeenCalled();
    expect(mockNavigate).not.toHaveBeenCalled();
    expect(input()).toHaveValue('>frobnicate');
  });

  it('clears the query on Escape', async () => {
    const user = userEvent.setup();
    renderStartScreen();
    await user.type(input(), 'reddit');
    fireEvent.keyDown(input(), { key: 'Escape' });
    expect(input()).toHaveValue('');
  });
});

describe('StartScreen file drop', () => {
  const dropZone = () => input().closest('.MuiPaper-root');

  it('sends a dropped image to Image Tools', () => {
    renderStartScreen();
    const image = new File(['png'], 'photo.png', { type: 'image/png' });
    drop(dropZone(), image);
    expect(mockNavigate).toHaveBeenCalledWith('/image-tools', { state: { file: image } });
    expect(sha256Hex).not.toHaveBeenCalled();
  });

  it('hashes any other dropped file locally and looks the SHA-256 up', async () => {
    const hash = 'f'.repeat(64);
    sha256Hex.mockResolvedValue(hash);
    renderStartScreen();

    drop(dropZone(), new File(['MZ'], 'sample.exe', { type: 'application/octet-stream' }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalled());
    expect(mockNavigate.mock.calls[0][0]).toMatch(/^\/ioc-tools\//);
    expect(mockNavigate.mock.calls[0][0]).toContain(`q=${hash}`);
  });

  it('reports a file that cannot be hashed', async () => {
    sha256Hex.mockRejectedValue(new Error('read error'));
    renderStartScreen();

    drop(dropZone(), new File(['x'], 'broken.bin'));

    expect(await screen.findByText("Couldn't process that value")).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('ignores drags that carry no files', () => {
    renderStartScreen();
    fireEvent.dragOver(dropZone(), { dataTransfer: { types: ['text/plain'] } });
    fireEvent.drop(dropZone(), { dataTransfer: { types: ['text/plain'], files: [] } });
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('outlines the page while a file is dragged over it', () => {
    renderStartScreen();
    const zone = dropZone();
    fireEvent.dragOver(zone, { dataTransfer: { types: ['Files'] } });
    expect(getComputedStyle(zone).outline).toMatch(/dashed/);
    fireEvent.dragLeave(zone, { dataTransfer: { types: ['Files'] } });
    expect(getComputedStyle(zone).outline).toBe('none');
  });
});

describe('StartScreen layout options', () => {
  it('shows tool tiles when the always-tiles setting is on, and opens a tile', async () => {
    const store = createStore();
    store.set(generalSettingsState, { always_tiles: true });
    renderStartScreen(store);

    fireEvent.click(screen.getByText('Reddit Search'));

    expect(mockNavigate).toHaveBeenCalledWith('/reddit-search');
  });

  it('opens the keyboard shortcut sheet from the syntax help', async () => {
    const user = userEvent.setup();
    renderStartScreen();
    await user.click(screen.getByRole('button', { name: /search syntax/i }));
    await user.click(screen.getByRole('button', { name: 'All keyboard shortcuts' }));
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
  });
});
