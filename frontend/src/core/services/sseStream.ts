import { baseURL } from './baseApi';
import { getAccessToken } from '../utils/accessToken';
import { createLogger } from '../utils/logger';

const logger = createLogger('SseStream');

// The client half of the backend's `core/scans/sse.py` `sse_stream`: every Server-Sent
// Events endpoint in the app is opened and read through here.
//
// `fetch`, not axios (can't hand back a streaming body in the browser) and not
// `EventSource` (can't send the `Authorization` header every `/api/*` route requires).

export interface OpenSseStreamOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  signal?: AbortSignal;
}

export async function openSseStream(
  path: string,
  { method = 'POST', body, signal }: OpenSseStreamOptions = {}
): Promise<ReadableStream<Uint8Array>> {
  const response = await fetch(`${baseURL}${path}`, {
    method,
    headers: {
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      Accept: 'text/event-stream',
      Authorization: `Bearer ${getAccessToken()}`,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`Server error: ${response.statusText}`);
  }
  return response.body;
}

/** Yields each `data: <json>` frame's parsed payload, in order. A frame that isn't a data
 *  frame or doesn't parse is logged and skipped rather than ending the stream. Stops when the
 *  stream closes or `signal` aborts; a broken connection rejects. */
export async function* readSseEvents(
  stream: ReadableStream<Uint8Array>,
  signal?: AbortSignal
): AsyncGenerator<unknown> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (!signal?.aborted) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split('\n\n');
      buffer = chunks.pop() ?? '';

      for (const chunk of chunks) {
        if (!chunk.startsWith('data: ')) continue;
        let event: unknown;
        try {
          event = JSON.parse(chunk.substring(6));
        } catch (err) {
          logger.error('Failed to parse SSE event:', err, chunk);
          continue;
        }
        yield event;
      }
    }
  } finally {
    reader.releaseLock();
  }
}
