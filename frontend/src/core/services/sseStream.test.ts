import { openSseStream, readSseEvents } from './sseStream';

vi.mock('./baseApi', () => ({ baseURL: 'http://backend.test' }));
vi.mock('../utils/accessToken', () => ({ getAccessToken: () => 'tok' }));

function streamOf(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < chunks.length) controller.enqueue(encoder.encode(chunks[i++]));
      else controller.close();
    },
  });
}

async function collect(stream: ReadableStream<Uint8Array>, signal?: AbortSignal) {
  const events: unknown[] = [];
  for await (const event of readSseEvents(stream, signal)) events.push(event);
  return events;
}

afterEach(() => vi.unstubAllGlobals());

describe('openSseStream', () => {
  it('POSTs a JSON body with the bearer token and returns the response body', async () => {
    const body = streamOf([]);
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body });
    vi.stubGlobal('fetch', fetchMock);

    expect(await openSseStream('/api/x/scan', { body: { q: 1 } })).toBe(body);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('http://backend.test/api/x/scan');
    expect(init).toMatchObject({
      method: 'POST',
      body: '{"q":1}',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream', Authorization: 'Bearer tok' },
    });
  });

  it('sends an authenticated GET without a body - what EventSource could not do', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, body: streamOf([]) });
    vi.stubGlobal('fetch', fetchMock);

    await openSseStream('/api/newsfeed/stream', { method: 'GET' });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe('GET');
    expect(init.body).toBeUndefined();
    expect(init.headers).toEqual({ Accept: 'text/event-stream', Authorization: 'Bearer tok' });
  });

  it('throws on a non-OK response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, statusText: 'Unauthorized', body: null }));

    await expect(openSseStream('/api/x/scan')).rejects.toThrow('Server error: Unauthorized');
  });
});

describe('readSseEvents', () => {
  it('yields parsed data frames, reassembling frames split across chunks', async () => {
    const events = await collect(streamOf(['data: {"a":1}\n\nda', 'ta: {"b":2}\n', '\n']));
    expect(events).toEqual([{ a: 1 }, { b: 2 }]);
  });

  it('skips non-data and unparseable frames without ending the stream', async () => {
    const events = await collect(streamOf([': ping\n\n', 'data: {nope\n\n', 'data: {"ok":true}\n\n']));
    expect(events).toEqual([{ ok: true }]);
  });

  it('stops once the signal aborts', async () => {
    const controller = new AbortController();
    controller.abort();
    expect(await collect(streamOf(['data: {"a":1}\n\n']), controller.signal)).toEqual([]);
  });
});
