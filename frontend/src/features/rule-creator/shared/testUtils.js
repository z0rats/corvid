import { vi } from 'vitest';

/**
 * Clicks the page's export button and returns { filename, content } of the file
 * exportAsFile would have downloaded.
 */
export async function captureExport(fireEvent, button) {
  let blob;
  const createObjectURL = vi.spyOn(window.URL, 'createObjectURL').mockImplementation((b) => { blob = b; return 'blob:x'; });
  const revoke = vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});
  let filename;
  const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function click() { filename = this.download; });
  fireEvent.click(button);
  createObjectURL.mockRestore();
  revoke.mockRestore();
  click.mockRestore();
  return { filename, content: blob ? await blob.text() : null };
}
