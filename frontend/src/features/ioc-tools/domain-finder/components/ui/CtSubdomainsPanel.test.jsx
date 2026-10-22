import { render, screen, fireEvent } from '@testing-library/react';
import CtSubdomainsPanel from './CtSubdomainsPanel';
import { useDomainPanel } from '../../hooks/useDomainPanel';

vi.mock('../../hooks/useDomainPanel', () => ({ useDomainPanel: vi.fn() }));

const showing = (data) => useDomainPanel.mockReturnValue({ data, loading: false, error: null, unsupported: false });

describe('CtSubdomainsPanel', () => {
  it('lists merged subdomains and one status line per source', () => {
    showing({
      subdomains: ['mail.example.com', 'www.example.com'],
      sources: [
        { name: 'crt.sh', ok: true, subdomain_count: 2, certificate_count: 5, truncated: false },
        { name: 'Cert Spotter', ok: true, subdomain_count: 1, certificate_count: 80, truncated: true },
      ],
    });

    render(<CtSubdomainsPanel domain="example.com" />);

    expect(screen.getByText('mail.example.com')).toBeInTheDocument();
    expect(screen.getByText('crt.sh: 2 subdomain(s) from 5 certificate(s)')).toBeInTheDocument();
    expect(
      screen.getByText('Cert Spotter: 1 subdomain(s) from the newest 80 certificate(s), more exist'),
    ).toBeInTheDocument();
  });

  it('says a failed source was not checked while still showing the other source', () => {
    showing({
      subdomains: ['mail.example.com'],
      sources: [
        { name: 'crt.sh', ok: false, error: 'Request timeout while connecting to crt.sh', error_code: 'CRTSH_TIMEOUT' },
        { name: 'Cert Spotter', ok: true, subdomain_count: 1, certificate_count: 3, truncated: false },
      ],
    });

    render(<CtSubdomainsPanel domain="example.com" />);

    expect(
      screen.getByText('crt.sh: not checked (Request timeout while connecting to crt.sh, CRTSH_TIMEOUT)'),
    ).toBeInTheDocument();
    expect(screen.getByText('mail.example.com')).toBeInTheDocument();
  });

  it('pivots a clicked subdomain into a scan', () => {
    showing({ subdomains: ['mail.example.com'], sources: [] });
    const onScanSubdomain = vi.fn();

    render(<CtSubdomainsPanel domain="example.com" onScanSubdomain={onScanSubdomain} />);
    fireEvent.click(screen.getByText('mail.example.com'));

    expect(onScanSubdomain).toHaveBeenCalledWith('mail.example.com');
  });
});
