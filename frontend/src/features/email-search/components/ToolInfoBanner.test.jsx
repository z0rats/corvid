import { render, screen, waitFor } from '@testing-library/react';
import ToolInfoBanner from './ToolInfoBanner';
import { emailSearchApi } from '../services/api/emailSearchApi';

vi.mock('../services/api/emailSearchApi', () => ({ emailSearchApi: { getInfo: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('ToolInfoBanner', () => {
  it('asks for the selected source and shows its tool, version and provider count', async () => {
    emailSearchApi.getInfo.mockResolvedValue({ tool: 'user-scanner', version: '1.5.2.1', provider_count: 152, available: true });

    render(<ToolInfoBanner source="user_scanner" />);

    await waitFor(() => expect(screen.getByText(/user-scanner v1\.5\.2\.1/)).toBeTruthy());
    expect(emailSearchApi.getInfo).toHaveBeenCalledWith('user_scanner');
    expect(screen.getByText(/152 providers checked/)).toBeTruthy();
  });

  it('tells the operator when the package is missing from the image', async () => {
    emailSearchApi.getInfo.mockResolvedValue({ tool: 'user-scanner', version: '', provider_count: 152, available: false });

    render(<ToolInfoBanner source="user_scanner" />);

    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('user-scanner is not installed'));
  });

  it('warns up front when the current settings would refuse the scan', async () => {
    emailSearchApi.getInfo.mockResolvedValue({
      tool: 'user-scanner', version: '1.5.2.1', provider_count: 152, available: true,
      blocked_reason: 'Turn off Tor and the proxy',
    });

    render(<ToolInfoBanner source="user_scanner" />);

    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('Turn off Tor and the proxy'));
  });

  it('defaults to mailcat', async () => {
    emailSearchApi.getInfo.mockResolvedValue({ tool: 'mailcat', version: '1.0', provider_count: 26 });

    render(<ToolInfoBanner />);

    await waitFor(() => expect(emailSearchApi.getInfo).toHaveBeenCalledWith('mailcat'));
  });
});
