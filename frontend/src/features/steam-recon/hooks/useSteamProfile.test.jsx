import { renderHook, act, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { Provider, createStore } from 'jotai';
import { useSteamProfile } from './useSteamProfile';
import { steamReconApi } from '../services/api/steamReconApi';

vi.mock('../services/api/steamReconApi', () => ({ steamReconApi: { profile: vi.fn() } }));

function setup(initialEntry = '/steam-recon') {
  const store = createStore();
  const wrapper = ({ children }) => (
    <Provider store={store}>
      <MemoryRouter initialEntries={[initialEntry]}>{children}</MemoryRouter>
    </Provider>
  );
  return renderHook(() => useSteamProfile(), { wrapper });
}

afterEach(() => vi.clearAllMocks());

describe('useSteamProfile', () => {
  it('trims the target and stores the result', async () => {
    steamReconApi.profile.mockResolvedValue({ profile: { steamid64: '1' } });
    const { result } = setup();

    await act(async () => {
      await result.current.lookupProfile('  robinwalker  ');
    });

    expect(steamReconApi.profile).toHaveBeenCalledWith('robinwalker');
    expect(result.current.result).toEqual({ profile: { steamid64: '1' } });
    expect(result.current.error).toBeNull();
  });

  it('ignores an empty target', async () => {
    const { result } = setup();

    await act(async () => {
      await result.current.lookupProfile('   ');
    });

    expect(steamReconApi.profile).not.toHaveBeenCalled();
  });

  it('exposes the API error detail and code', async () => {
    steamReconApi.profile.mockRejectedValue({
      response: { data: { detail: 'Steam rejected the API key', error_code: 'STEAM_KEY_REJECTED' } },
    });
    const { result } = setup();

    await act(async () => {
      await result.current.lookupProfile('robinwalker');
    });

    expect(result.current.result).toBeNull();
    expect(result.current.error).toBe('Steam rejected the API key');
    expect(result.current.errorCode).toBe('STEAM_KEY_REJECTED');
  });

  it('prefills the field and runs the lookup from ?q= (command palette pivot)', async () => {
    steamReconApi.profile.mockResolvedValue({ profile: { steamid64: '1' } });
    const { result } = setup('/steam-recon?q=76561197960435530');

    await waitFor(() => expect(steamReconApi.profile).toHaveBeenCalledWith('76561197960435530'));
    expect(result.current.target).toBe('76561197960435530');
  });
});
