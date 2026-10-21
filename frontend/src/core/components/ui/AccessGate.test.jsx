import { render, screen, fireEvent } from '@testing-library/react';
import AccessGate from './AccessGate';
import api from '../../services/baseApi';
import { getAccessToken, setAccessToken } from '../../utils/accessToken';

const reload = vi.fn();

beforeEach(() => {
  localStorage.clear();
  reload.mockReset();
  vi.stubGlobal('location', { ...window.location, reload });
});
afterEach(() => vi.unstubAllGlobals());

describe('AccessGate', () => {
  it('renders the app once a token is stored', () => {
    setAccessToken('tok');
    render(<AccessGate><div>APP</div></AccessGate>);
    expect(screen.getByText('APP')).toBeInTheDocument();
  });

  it('without a token asks for one, never showing the app', () => {
    render(<AccessGate><div>APP</div></AccessGate>);
    expect(screen.queryByText('APP')).toBeNull();
    expect(screen.getByText('Access Token Required')).toBeInTheDocument();
    expect(screen.getByLabelText('Access token')).toHaveAttribute('type', 'password');
  });

  it('stores the trimmed token and reloads; blank input does nothing', () => {
    render(<AccessGate><div>APP</div></AccessGate>);
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
    expect(reload).not.toHaveBeenCalled();
    expect(getAccessToken()).toBe('');

    fireEvent.change(screen.getByLabelText('Access token'), { target: { value: '  s3cret  ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
    expect(getAccessToken()).toBe('s3cret');
    expect(reload).toHaveBeenCalledTimes(1);
  });
});

describe('baseApi auth interceptors', () => {
  function respondWith(status) {
    const seen = [];
    api.defaults.adapter = async (config) => {
      seen.push(config.headers.Authorization);
      if (status >= 400) {
        const error = new Error(`HTTP ${status}`);
        error.response = { status, data: {}, config };
        error.config = config;
        throw error;
      }
      return { status, data: { ok: true }, headers: {}, config, statusText: 'OK' };
    };
    return seen;
  }

  it('attaches the bearer token to every request', async () => {
    setAccessToken('tok-1');
    const seen = respondWith(200);
    await api.get('/api/x');
    expect(seen).toEqual(['Bearer tok-1']);
  });

  it('sends no Authorization header without a token', async () => {
    const seen = respondWith(200);
    await api.get('/api/x');
    expect(seen).toEqual([undefined]);
  });

  it('a 401 with a stored token clears it and reloads to the gate', async () => {
    setAccessToken('revoked');
    respondWith(401);
    await expect(api.get('/api/x')).rejects.toThrow('HTTP 401');
    expect(getAccessToken()).toBe('');
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('a 401 before any token exists does not reload (no loop)', async () => {
    respondWith(401);
    await expect(api.get('/api/x')).rejects.toThrow('HTTP 401');
    expect(reload).not.toHaveBeenCalled();
  });

  it('other errors leave the token alone', async () => {
    setAccessToken('tok');
    respondWith(500);
    await expect(api.get('/api/x')).rejects.toThrow('HTTP 500');
    expect(getAccessToken()).toBe('tok');
    expect(reload).not.toHaveBeenCalled();
  });
});
