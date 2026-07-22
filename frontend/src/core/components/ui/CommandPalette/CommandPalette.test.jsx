import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import CommandPalette from './CommandPalette';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  mockNavigate.mockClear();
  localStorage.clear();
});

function renderPalette(extra = null) {
  return render(
    <MemoryRouter>
      {extra}
      <CommandPalette />
    </MemoryRouter>,
  );
}

function getSearchInput() {
  return screen.getByPlaceholderText(/search tools/i);
}

describe('CommandPalette — "/" guard', () => {
  it('opens on "/" when no input is focused', () => {
    renderPalette();

    expect(screen.queryByPlaceholderText(/search tools/i)).not.toBeInTheDocument();

    fireEvent.keyDown(window, { key: '/' });

    expect(screen.getByPlaceholderText(/search tools/i)).toBeInTheDocument();
  });

  it('does not open on "/" while a text input elsewhere is focused', async () => {
    const user = userEvent.setup();
    renderPalette(<input data-testid="other-input" aria-label="other input" />);

    const otherInput = screen.getByTestId('other-input');
    otherInput.focus();
    await user.keyboard('/');

    expect(screen.queryByPlaceholderText(/search tools/i)).not.toBeInTheDocument();
  });

  it('opens on Cmd/Ctrl+K regardless of focus', () => {
    renderPalette();

    fireEvent.keyDown(window, { key: 'k', metaKey: true });

    expect(screen.getByPlaceholderText(/search tools/i)).toBeInTheDocument();
  });

  it('Cmd/Ctrl+, opens Settings directly, closed or open', () => {
    renderPalette();

    fireEvent.keyDown(window, { key: ',', metaKey: true });
    expect(mockNavigate).toHaveBeenCalledWith('/settings');
    expect(screen.queryByPlaceholderText(/search tools/i)).not.toBeInTheDocument();

    mockNavigate.mockClear();
    fireEvent.keyDown(window, { key: '/' });
    fireEvent.keyDown(window, { key: ',', metaKey: true });
    expect(mockNavigate).toHaveBeenCalledWith('/settings');
  });
});

describe('CommandPalette — Esc behavior', () => {
  it('clears the query on the first Esc, then closes on the second', async () => {
    const user = userEvent.setup();
    renderPalette();
    fireEvent.keyDown(window, { key: '/' });

    const input = getSearchInput();
    await user.type(input, 'reddit');
    expect(input).toHaveValue('reddit');

    fireEvent.keyDown(input, { key: 'Escape' });
    expect(getSearchInput()).toHaveValue('');

    fireEvent.keyDown(getSearchInput(), { key: 'Escape' });
    await waitFor(() => {
      expect(screen.queryByPlaceholderText(/search tools/i)).not.toBeInTheDocument();
    });
  });
});

describe('CommandPalette — arrow-key navigation and Enter', () => {
  it('opens the top text match on Enter', async () => {
    const user = userEvent.setup();
    renderPalette();
    fireEvent.keyDown(window, { key: '/' });

    await user.type(getSearchInput(), 'reddit');
    fireEvent.keyDown(getSearchInput(), { key: 'Enter' });

    expect(mockNavigate).toHaveBeenCalledWith('/reddit-search');
  });

  it('ArrowDown moves the selection to the next match before Enter opens it', async () => {
    const user = userEvent.setup();
    renderPalette();
    fireEvent.keyDown(window, { key: '/' });

    // #recon matches several tools; arrow down once and open the second one.
    await user.type(getSearchInput(), '#recon');
    const rows = await screen.findAllByRole('button', { name: /.+/ });
    const resultRows = rows.filter((r) => r.closest('ul'));
    expect(resultRows.length).toBeGreaterThan(1);

    fireEvent.keyDown(getSearchInput(), { key: 'ArrowDown' });
    fireEvent.keyDown(getSearchInput(), { key: 'Enter' });

    expect(mockNavigate).toHaveBeenCalledTimes(1);
    const openedPath = mockNavigate.mock.calls[0][0];
    expect(typeof openedPath).toBe('string');
  });

  it('opens a recognized value on Enter with a prefilled URL', async () => {
    const user = userEvent.setup();
    renderPalette();
    fireEvent.keyDown(window, { key: '/' });

    await user.type(getSearchInput(), '8.8.8.8');
    await waitFor(() => expect(screen.getByText(/detected/i)).toBeInTheDocument());

    fireEvent.keyDown(getSearchInput(), { key: 'Enter' });

    expect(mockNavigate).toHaveBeenCalledTimes(1);
    const openedPath = mockNavigate.mock.calls[0][0];
    expect(openedPath).toContain('q=8.8.8.8');
  });

  it('runs a >settings action on Enter', async () => {
    const user = userEvent.setup();
    renderPalette();
    fireEvent.keyDown(window, { key: '/' });

    await user.type(getSearchInput(), '>settings');
    fireEvent.keyDown(getSearchInput(), { key: 'Enter' });

    expect(mockNavigate).toHaveBeenCalledWith('/settings');
  });

  it('jumps straight to the Nth result with Cmd+number', async () => {
    const user = userEvent.setup();
    renderPalette();
    fireEvent.keyDown(window, { key: '/' });

    await user.type(getSearchInput(), '#recon');
    fireEvent.keyDown(getSearchInput(), { key: '2', metaKey: true });

    expect(mockNavigate).toHaveBeenCalledTimes(1);
  });

  it('does not swallow bare digits typed into the query (regression: only Cmd/Ctrl+digit jumps)', async () => {
    const user = userEvent.setup();
    renderPalette();
    fireEvent.keyDown(window, { key: '/' });

    // A raw value full of digits (IP, hash, CVE year, port) must type in untouched — the jump
    // shortcut requires a modifier specifically so it never competes with typed digits.
    await user.type(getSearchInput(), '185.220.101.7');

    expect(getSearchInput()).toHaveValue('185.220.101.7');
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
