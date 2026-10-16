import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { Provider, createStore } from 'jotai';
import { modulesState } from '../../state/atoms';
import StartScreen from './StartScreen';

vi.mock('../../services/api/activityService', () => ({
  activityService: { listRecent: vi.fn().mockResolvedValue([]) },
}));

vi.mock('./ApiKeysOnboardingHint', () => ({ default: () => null }));

const mockNavigate = vi.fn();

vi.mock('react-router', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  mockNavigate.mockClear();
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

  it('hides modules disabled in Settings -> Modules from the catalog', () => {
    const store = createStore();
    store.set(modulesState, { reddit_search: { enabled: false } });
    renderStartScreen(store);
    expect(screen.queryByText('Reddit Search')).not.toBeInTheDocument();
    expect(screen.getByText('IOC Tools')).toBeInTheDocument();
  });

  it('puts the search input before the example chips', () => {
    renderStartScreen();
    const input = screen.getByPlaceholderText(/search tools/i);
    const example = screen.getByText('IP address');
    // DOCUMENT_POSITION_FOLLOWING: the example comes after the input in document order.
    expect(input.compareDocumentPosition(example) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('fills the input from a labelled example chip', async () => {
    const user = userEvent.setup();
    renderStartScreen();

    await user.click(screen.getByText('IP address'));

    expect(screen.getByPlaceholderText(/search tools/i)).toHaveValue('185.220.101.7');
  });

  it('explains the search syntax only once the help toggle is opened', async () => {
    const user = userEvent.setup();
    renderStartScreen();
    expect(screen.queryByText(/list tools by tag/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /search syntax/i }));

    expect(screen.getByText(/list tools by tag/i)).toBeInTheDocument();
    expect(screen.getByText('type:kind')).toBeInTheDocument();
  });

  it('shows no row-actions button, since the start screen has no action panel', () => {
    renderStartScreen();
    expect(screen.queryByRole('button', { name: 'Row actions' })).not.toBeInTheDocument();
  });
});
