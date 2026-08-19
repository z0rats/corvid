import { defangApi, defangUtils } from './defangApi';
import api from '../../../../../core/services/baseApi';

vi.mock('../../../../../core/services/baseApi', () => ({ default: { post: vi.fn() } }));

afterEach(() => vi.clearAllMocks());

describe('defangApi.batchProcessIOCs', () => {
  it('posts the text and operation, returning the results array', async () => {
    api.post.mockResolvedValue({ data: { results: [{ original: 'x', processed: 'x[.]' }] } });

    const results = await defangApi.batchProcessIOCs('1.2.3.4', 'defang');

    expect(api.post).toHaveBeenCalledWith('/api/defang/', { text: '1.2.3.4', operation: 'defang' });
    expect(results).toEqual([{ original: 'x', processed: 'x[.]' }]);
  });

  it('defaults the operation to defang', async () => {
    api.post.mockResolvedValue({ data: { results: [] } });

    await defangApi.batchProcessIOCs('1.2.3.4');

    expect(api.post).toHaveBeenCalledWith('/api/defang/', { text: '1.2.3.4', operation: 'defang' });
  });
});

describe('defangApi.defangIOC', () => {
  it('returns the processed value from the first result', async () => {
    api.post.mockResolvedValue({ data: { results: [{ processed: '1[.]2[.]3[.]4' }] } });

    expect(await defangApi.defangIOC('1.2.3.4')).toBe('1[.]2[.]3[.]4');
  });

  it('falls back to the original IOC when no results are returned', async () => {
    api.post.mockResolvedValue({ data: { results: [] } });

    expect(await defangApi.defangIOC('1.2.3.4')).toBe('1.2.3.4');
  });
});

describe('defangApi.fangIOC', () => {
  it('requests the fang operation', async () => {
    api.post.mockResolvedValue({ data: { results: [{ processed: '1.2.3.4' }] } });

    await defangApi.fangIOC('1[.]2[.]3[.]4');

    expect(api.post).toHaveBeenCalledWith('/api/defang/', {
      text: '1[.]2[.]3[.]4',
      operation: 'fang',
    });
  });
});

describe('defangUtils', () => {
  const results = [
    { original: 'a', processed: 'a[.]', types: ['Domain'], changed: true },
    { original: 'b', processed: 'b', types: ['IP Address'], changed: false },
  ];

  it('getProcessedIOCs extracts the processed value from every result', () => {
    expect(defangUtils.getProcessedIOCs(results)).toEqual(['a[.]', 'b']);
  });

  it('getChangedIOCs returns only results marked as changed', () => {
    expect(defangUtils.getChangedIOCs(results)).toEqual([results[0]]);
  });

  it('getIOCsByType filters by the given type', () => {
    expect(defangUtils.getIOCsByType(results, 'IP Address')).toEqual([results[1]]);
  });
});
