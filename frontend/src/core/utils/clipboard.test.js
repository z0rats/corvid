import { copyToClipboard } from './clipboard';

describe('copyToClipboard', () => {
  const originalIsSecureContext = window.isSecureContext;
  const originalClipboard = navigator.clipboard;
  const originalExecCommand = document.execCommand;

  afterEach(() => {
    Object.defineProperty(window, 'isSecureContext', { value: originalIsSecureContext, configurable: true });
    Object.defineProperty(navigator, 'clipboard', { value: originalClipboard, configurable: true });
    document.execCommand = originalExecCommand;
  });

  it('uses navigator.clipboard.writeText in a secure context', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true });
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });

    const result = await copyToClipboard('hello');

    expect(writeText).toHaveBeenCalledWith('hello');
    expect(result).toBe(true);
  });

  it('falls back to execCommand when not a secure context', async () => {
    Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
    Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true });
    document.execCommand = vi.fn().mockReturnValue(true);

    const result = await copyToClipboard('hello');

    expect(document.execCommand).toHaveBeenCalledWith('copy');
    expect(result).toBe(true);
  });

  it('falls back to execCommand when the secure-context write throws', async () => {
    const writeText = vi.fn().mockRejectedValue(new Error('denied'));
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true });
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
    document.execCommand = vi.fn().mockReturnValue(true);

    const result = await copyToClipboard('hello');

    expect(document.execCommand).toHaveBeenCalledWith('copy');
    expect(result).toBe(true);
  });

  it('returns false when every path fails, without throwing', async () => {
    Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
    Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true });
    document.execCommand = vi.fn(() => { throw new Error('not supported'); });

    const result = await copyToClipboard('hello');

    expect(result).toBe(false);
  });

  it('removes the temporary textarea from the DOM after use', async () => {
    Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
    Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true });
    document.execCommand = vi.fn().mockReturnValue(true);

    await copyToClipboard('hello');

    expect(document.querySelector('textarea')).toBeNull();
  });
});
