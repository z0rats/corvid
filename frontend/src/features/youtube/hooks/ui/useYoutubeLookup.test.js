import { act, renderHook, waitFor } from '@testing-library/react';
import { createElement } from 'react';
import { MemoryRouter } from 'react-router';
import { Provider, createStore } from 'jotai';
import { useYoutubeLookup } from './useYoutubeLookup';
import { youtubeApi } from '../../services/api/youtubeApi';

vi.mock('../../services/api/youtubeApi');

afterEach(() => vi.clearAllMocks());

const VIDEO = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';

function render(initialEntry = '/youtube', store = createStore()) {
  const wrapper = ({ children }) => createElement(
    Provider, { store }, createElement(MemoryRouter, { initialEntries: [initialEntry] }, children),
  );
  return renderHook(() => useYoutubeLookup(), { wrapper });
}

describe('useYoutubeLookup', () => {
  it('looks up the video in the URL on load', async () => {
    youtubeApi.lookup.mockResolvedValue({ title: 'x' });
    const { result } = render(`/youtube?q=${encodeURIComponent(VIDEO)}`);

    await waitFor(() => expect(result.current.result).toEqual({ title: 'x' }));
    expect(youtubeApi.lookup).toHaveBeenCalledWith(VIDEO);
    expect(result.current.url).toBe(VIDEO);
  });

  it('does not re-run a lookup whose result is already shown', async () => {
    youtubeApi.lookup.mockResolvedValue({ title: 'x' });
    const store = createStore();
    const first = render(`/youtube?q=${encodeURIComponent(VIDEO)}`, store);
    await waitFor(() => expect(first.result.current.result).not.toBeNull());
    first.unmount();

    render(`/youtube?q=${encodeURIComponent(VIDEO)}`, store);

    expect(youtubeApi.lookup).toHaveBeenCalledTimes(1);
  });

  it('surfaces an API error', async () => {
    youtubeApi.lookup.mockRejectedValue({ response: { data: { detail: 'Not a video' } } });
    const { result } = render();

    act(() => result.current.setUrl(VIDEO));
    await act(async () => result.current.lookupVideo());

    await waitFor(() => expect(result.current.error).toBe('Not a video'));
  });
});
