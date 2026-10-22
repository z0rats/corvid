import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ApiDownloadButtons from './ApiDownloadButtons';
import { downloadFromApi } from '../../services/apiDownload';

vi.mock('../../services/apiDownload', () => ({ downloadFromApi: vi.fn() }));

afterEach(() => vi.clearAllMocks());

const request = (fmt) => ({ path: `/api/r/${fmt}`, params: { format: fmt }, fallbackName: `r.${fmt}` });

describe('ApiDownloadButtons', () => {
  it('downloads the chosen format through downloadFromApi', async () => {
    downloadFromApi.mockResolvedValue();
    const user = userEvent.setup();
    render(<ApiDownloadButtons formats={['html', 'pdf']} request={request} />);

    await user.click(screen.getByRole('button', { name: 'PDF' }));

    expect(downloadFromApi).toHaveBeenCalledWith('/api/r/pdf', { params: { format: 'pdf' }, fallbackName: 'r.pdf' });
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('says so when a download fails', async () => {
    downloadFromApi.mockRejectedValue(new Error('401'));
    const user = userEvent.setup();
    render(<ApiDownloadButtons formats={['html']} request={request} />);

    await user.click(screen.getByRole('button', { name: 'HTML' }));

    expect(await screen.findByText(/Download failed/)).toBeInTheDocument();
  });
});
