import { act, renderHook, waitFor } from '@testing-library/react';
import { useGhuntProfile } from './useGhuntProfile';
import { ghuntProfileApi } from '../../services/api/ghuntProfileApi';

vi.mock('../../services/api/ghuntProfileApi');

afterEach(() => vi.clearAllMocks());

describe('useGhuntProfile', () => {
  it('fetches health on mount', async () => {
    ghuntProfileApi.getHealth.mockResolvedValue({ installed: true, session_configured: true });

    const { result } = renderHook(() => useGhuntProfile());

    await waitFor(() => expect(result.current.health).toEqual({
      installed: true, session_configured: true,
    }));
  });

  it('populates the result on a successful lookup', async () => {
    ghuntProfileApi.getHealth.mockResolvedValue({ installed: true, session_configured: true });
    const mockProfile = { gaia_id: '123', email: 'target@gmail.com' };
    ghuntProfileApi.lookup.mockResolvedValue(mockProfile);

    const { result } = renderHook(() => useGhuntProfile());

    await act(async () => {
      await result.current.lookup('target@gmail.com');
    });

    expect(result.current.result).toEqual(mockProfile);
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('surfaces the error code and message on failure', async () => {
    ghuntProfileApi.getHealth.mockResolvedValue({ installed: true, session_configured: false });
    ghuntProfileApi.lookup.mockRejectedValue({
      response: { data: { detail: 'No session configured', error_code: 'GHUNT_SESSION_MISSING' } },
    });

    const { result } = renderHook(() => useGhuntProfile());

    await act(async () => {
      await result.current.lookup('target@gmail.com');
    });

    expect(result.current.error).toEqual({
      code: 'GHUNT_SESSION_MISSING', message: 'No session configured',
    });
    expect(result.current.result).toBeNull();
  });

  it('reset clears result and error', async () => {
    ghuntProfileApi.getHealth.mockResolvedValue({ installed: true, session_configured: true });
    ghuntProfileApi.lookup.mockResolvedValue({ gaia_id: '123' });

    const { result } = renderHook(() => useGhuntProfile());

    await act(async () => {
      await result.current.lookup('target@gmail.com');
    });
    expect(result.current.result).not.toBeNull();

    act(() => {
      result.current.reset();
    });

    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
