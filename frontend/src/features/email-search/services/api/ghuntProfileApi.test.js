import api from '../../../../core/services/baseApi';
import { ghuntProfileApi } from './ghuntProfileApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('ghuntProfileApi', () => {
  it('lookup posts the email to the profile-lookup endpoint', async () => {
    api.post.mockResolvedValue({ data: { gaia_id: '123', email: 'target@gmail.com' } });

    const result = await ghuntProfileApi.lookup('target@gmail.com');

    expect(api.post).toHaveBeenCalledWith('/api/email-search/ghunt-profile', {
      email: 'target@gmail.com',
    });
    expect(result).toEqual({ gaia_id: '123', email: 'target@gmail.com' });
  });

  it('getHealth fetches the health endpoint', async () => {
    api.get.mockResolvedValue({ data: { installed: true, session_configured: false } });

    const result = await ghuntProfileApi.getHealth();

    expect(api.get).toHaveBeenCalledWith('/api/email-search/ghunt-profile/health');
    expect(result).toEqual({ installed: true, session_configured: false });
  });
});
