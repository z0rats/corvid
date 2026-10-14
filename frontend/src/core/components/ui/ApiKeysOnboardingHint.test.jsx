import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import ApiKeysOnboardingHint from './ApiKeysOnboardingHint';
import api from '../../services/baseApi';

vi.mock('../../services/baseApi', () => ({ default: { get: vi.fn() } }));

const renderHint = () => render(<MemoryRouter><ApiKeysOnboardingHint /></MemoryRouter>);

beforeEach(() => localStorage.clear());
afterEach(() => vi.clearAllMocks());

describe('ApiKeysOnboardingHint', () => {
  it('shows while no key is configured, linking to API Keys', async () => {
    api.get.mockResolvedValue({ data: { virustotal: false, shodan: false } });
    renderHint();
    expect(await screen.findByText('No API keys configured yet')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Add keys' })).toHaveAttribute('href', '/settings/apikeys');
  });

  it('stays hidden once any key is configured', async () => {
    api.get.mockResolvedValue({ data: { virustotal: true, shodan: false } });
    const { container } = renderHint();
    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it('remembers being dismissed', async () => {
    api.get.mockResolvedValue({ data: {} });
    const { unmount } = renderHint();
    fireEvent.click(await screen.findByRole('button', { name: /close/i }));
    expect(screen.queryByText('No API keys configured yet')).not.toBeInTheDocument();
    unmount();

    renderHint();
    expect(api.get).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('No API keys configured yet')).not.toBeInTheDocument();
  });
});
