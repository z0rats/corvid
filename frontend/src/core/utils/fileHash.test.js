import { sha256Hex } from './fileHash';

// Known SHA-256 digests (verified against Node's crypto module).
const EMPTY_SHA256 = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';
const ABC_SHA256 = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';

describe('sha256Hex', () => {
  const originalIsSecureContext = window.isSecureContext;
  const originalSubtle = crypto.subtle;

  afterEach(() => {
    Object.defineProperty(window, 'isSecureContext', { value: originalIsSecureContext, configurable: true });
    Object.defineProperty(crypto, 'subtle', { value: originalSubtle, configurable: true });
  });

  it('uses crypto.subtle in a secure context', async () => {
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true });
    const file = new File(['abc'], 'abc.txt');

    const result = await sha256Hex(file);

    expect(result).toBe(ABC_SHA256);
  });

  it('falls back to the pure-JS implementation when not a secure context', async () => {
    Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
    const file = new File(['abc'], 'abc.txt');

    const result = await sha256Hex(file);

    expect(result).toBe(ABC_SHA256);
  });

  it('falls back to the pure-JS implementation when crypto.subtle is unavailable', async () => {
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true });
    Object.defineProperty(crypto, 'subtle', { value: undefined, configurable: true });
    const file = new File([], 'empty.txt');

    const result = await sha256Hex(file);

    expect(result).toBe(EMPTY_SHA256);
  });

  it('produces the same digest via both paths for an empty file', async () => {
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true });
    const nativeResult = await sha256Hex(new File([], 'empty.txt'));

    Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
    const fallbackResult = await sha256Hex(new File([], 'empty.txt'));

    expect(nativeResult).toBe(fallbackResult);
    expect(nativeResult).toBe(EMPTY_SHA256);
  });
});
