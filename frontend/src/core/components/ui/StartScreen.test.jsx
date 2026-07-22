import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import StartScreen from './StartScreen';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  mockNavigate.mockClear();
  localStorage.clear();
});

function renderStartScreen() {
  return render(
    <MemoryRouter>
      <StartScreen />
    </MemoryRouter>,
  );
}

describe('StartScreen', () => {
  it('renders a search input, focused by default', () => {
    renderStartScreen();
    const input = screen.getByPlaceholderText(/search tools/i);
    expect(input).toHaveFocus();
  });

  it('opens the top text match on Enter', async () => {
    const user = userEvent.setup();
    renderStartScreen();

    const input = screen.getByPlaceholderText(/search tools/i);
    await user.type(input, 'reddit');
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(mockNavigate).toHaveBeenCalledWith('/reddit-search');
  });

  it('opens a recognized value with a prefilled URL on Enter', async () => {
    const user = userEvent.setup();
    renderStartScreen();

    const input = screen.getByPlaceholderText(/search tools/i);
    await user.type(input, '8.8.8.8');
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(mockNavigate).toHaveBeenCalledTimes(1);
    expect(mockNavigate.mock.calls[0][0]).toContain('q=8.8.8.8');
  });

  it('shows the full catalog with nothing typed', () => {
    renderStartScreen();
    expect(screen.getByText('Reddit Search')).toBeInTheDocument();
    expect(screen.getByText('IOC Tools')).toBeInTheDocument();
  });
});
