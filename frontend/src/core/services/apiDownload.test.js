import api from './baseApi';
import { downloadFile } from '../utils/exportData';
import { downloadFromApi, filenameFromDisposition } from './apiDownload';

vi.mock('./baseApi', () => ({ default: { get: vi.fn() } }));
vi.mock('../utils/exportData', () => ({ downloadFile: vi.fn() }));

afterEach(() => vi.clearAllMocks());

describe('filenameFromDisposition', () => {
  it.each([
    ['attachment; filename="ioc-lookup-5-1.1.1.1.pdf"', 'ioc-lookup-5-1.1.1.1.pdf'],
    ["attachment; filename*=UTF-8''%D0%BE%D1%82%D1%87%D1%91%D1%82.pdf", 'отчёт.pdf'],
    ['attachment; filename=plain.html', 'plain.html'],
    [undefined, null],
    ['inline', null],
  ])('%s -> %s', (header, expected) => {
    expect(filenameFromDisposition(header)).toBe(expected);
  });
});

describe('downloadFromApi', () => {
  it('fetches a blob through the authenticated client and saves it under the server name', async () => {
    const blob = new Blob(['x'], { type: 'application/pdf' });
    api.get.mockResolvedValue({ data: blob, headers: { 'content-disposition': 'attachment; filename="r.pdf"' } });

    await downloadFromApi('/api/x/report', { params: { format: 'pdf' }, fallbackName: 'fallback.pdf' });

    expect(api.get).toHaveBeenCalledWith('/api/x/report', { params: { format: 'pdf' }, responseType: 'blob' });
    expect(downloadFile).toHaveBeenCalledWith(blob, 'r.pdf', 'application/pdf');
  });

  it('falls back to the given name when the header is not readable', async () => {
    api.get.mockResolvedValue({ data: new Blob(['x']), headers: {} });

    await downloadFromApi('/api/x', { fallbackName: 'fallback.txt' });

    expect(downloadFile).toHaveBeenCalledWith(expect.any(Blob), 'fallback.txt', 'application/octet-stream');
  });

  it('propagates a failed request', async () => {
    api.get.mockRejectedValue(new Error('401'));
    await expect(downloadFromApi('/api/x')).rejects.toThrow('401');
    expect(downloadFile).not.toHaveBeenCalled();
  });
});
