import { extractorApi, extractorUtils } from './extractorApi';
import api from '../../../../../core/services/baseApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('extractorApi.extractFromText', () => {
  it('posts the text and returns the response data', async () => {
    api.post.mockResolvedValue({ data: { domains: ['example.com'] } });

    const result = await extractorApi.extractFromText('example.com');

    expect(api.post).toHaveBeenCalledWith('/api/extractor/text/', { text: 'example.com' });
    expect(result).toEqual({ domains: ['example.com'] });
  });
});

describe('extractorApi.extractFromFile', () => {
  it('posts multipart form data with the file', async () => {
    api.post.mockResolvedValue({ data: { domains: [] } });
    const file = new File(['content'], 'iocs.txt');

    await extractorApi.extractFromFile(file);

    const [url, formData, config] = api.post.mock.calls[0];
    expect(url).toBe('/api/extractor/');
    expect(formData.get('file')).toBe(file);
    expect(config.headers['Content-Type']).toBe('multipart/form-data');
  });

  it('reports upload progress as a percentage', async () => {
    api.post.mockImplementation(async (_url, _data, config) => {
      config.onUploadProgress({ loaded: 50, total: 200 });
      return { data: {} };
    });
    const onProgress = vi.fn();

    await extractorApi.extractFromFile(new File(['x'], 'x.txt'), onProgress);

    expect(onProgress).toHaveBeenCalledWith(25);
  });

  it('omits onUploadProgress entirely when no callback is given', async () => {
    api.post.mockResolvedValue({ data: {} });

    await extractorApi.extractFromFile(new File(['x'], 'x.txt'));

    const [, , config] = api.post.mock.calls[0];
    expect(config.onUploadProgress).toBeUndefined();
  });
});

describe('extractorUtils.getAllIOCsFromExtraction', () => {
  it('flattens known IOC categories into value/type pairs', () => {
    const result = extractorUtils.getAllIOCsFromExtraction({
      ips: ['1.2.3.4'],
      domains: ['example.com'],
      unrelated_key: ['ignored'],
    });

    expect(result).toEqual([
      { value: '1.2.3.4', type: 'IP Address' },
      { value: 'example.com', type: 'Domain' },
    ]);
  });
});

describe('extractorUtils.countTotalIOCs', () => {
  it('sums the length of every array-valued field', () => {
    expect(extractorUtils.countTotalIOCs({ ips: ['a', 'b'], domains: ['c'], meta: 'ignored' })).toBe(3);
  });
});

describe('extractorUtils.getIOCsByType', () => {
  it('returns the array for the given key', () => {
    expect(extractorUtils.getIOCsByType({ domains: ['a.com'] }, 'domains')).toEqual(['a.com']);
  });

  it('returns an empty array for a missing key', () => {
    expect(extractorUtils.getIOCsByType({}, 'domains')).toEqual([]);
  });
});
