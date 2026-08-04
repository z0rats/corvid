import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import WelcomeScreen from './WelcomeScreen';

describe('WelcomeScreen', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the intro copy and key feature cards', () => {
    render(<WelcomeScreen onTrySample={vi.fn()} />);

    expect(screen.getByText('Image Tools')).toBeInTheDocument();
    expect(screen.getByText('Key Features')).toBeInTheDocument();
  });

  it('fetches the bundled sample photo and hands it to onTrySample as a File', async () => {
    const blob = new Blob(['fake jpeg bytes'], { type: 'image/jpeg' });
    global.fetch.mockResolvedValue({ blob: () => Promise.resolve(blob) });
    const onTrySample = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<WelcomeScreen onTrySample={onTrySample} />);
    await user.click(screen.getByRole('button', { name: /try it with a sample photo/i }));

    expect(global.fetch).toHaveBeenCalledWith('/sample/corvid-sample.jpg');
    await waitFor(() => expect(onTrySample).toHaveBeenCalledTimes(1));
    const [file] = onTrySample.mock.calls[0];
    expect(file).toBeInstanceOf(File);
    expect(file.name).toBe('corvid-sample.jpg');
    expect(file.type).toBe('image/jpeg');
  });

  it('shows a loading state while the sample photo is being fetched and analyzed', async () => {
    let resolveFetch;
    global.fetch.mockReturnValue(new Promise((resolve) => { resolveFetch = resolve; }));
    const user = userEvent.setup();

    render(<WelcomeScreen onTrySample={vi.fn().mockResolvedValue(undefined)} />);
    await user.click(screen.getByRole('button', { name: /try it with a sample photo/i }));

    expect(screen.getByText(/analyzing the sample photo/i)).toBeInTheDocument();

    resolveFetch({ blob: () => Promise.resolve(new Blob(['x'], { type: 'image/jpeg' })) });
    await waitFor(() => expect(screen.queryByText(/analyzing the sample photo/i)).not.toBeInTheDocument());
  });
});
