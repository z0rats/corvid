import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { Provider, createStore } from 'jotai';
import NewSearch from './NewSearch';
import { emailScanStateAtom, SCAN_INITIAL_STATE } from '../state/scanAtoms';

vi.mock('../services/api/emailSearchApi', () => ({
  emailSearchApi: { getInfo: vi.fn().mockResolvedValue(null) },
}));
vi.mock('./GhuntProfilePanel', () => ({ default: () => null }));

const renderWithScan = (scanState) => {
  const store = createStore();
  store.set(emailScanStateAtom, { ...SCAN_INITIAL_STATE, ...scanState });
  return render(
    <Provider store={store}>
      <MemoryRouter initialEntries={['/email-search/new']}><NewSearch /></MemoryRouter>
    </Provider>,
  );
};

describe('Email Search NewSearch: selected tool', () => {
  it('follows the scan already on screen when the page is revisited', () => {
    renderWithScan({ phase: 'completed', source: 'user_scanner', username: 'a@b.test', searchId: 3 });

    expect(screen.getByLabelText('Email address')).toBeInTheDocument();
    expect(screen.getByText(/sent to about 150 third-party services/)).toBeInTheDocument();
  });

  it('starts on Mailcat with no scan on screen', () => {
    renderWithScan({});

    expect(screen.getByLabelText('Username')).toBeInTheDocument();
  });
});
